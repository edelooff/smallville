import getpass
import itertools
import json
import math
import os
import random
import time

from sqlalchemy import (
    create_engine,
    null)
from sqlalchemy.orm import sessionmaker

from smallville.base import Base
from smallville.generators import (
    CompanyGenerator,
    PopulationGenerator,
    city_generator)
from smallville.models import (
    Company,
    Employment,
    Person,
    TransportLink)
from smallville.pathfinding import dijkstra


class BulkSaver:
    """Chunked bulk insert/update utility.

    This provides a wrapper around SQLAlchemy's Session.bulk_save_objects,
    providing both grouping of inserts by their mapped class, as well as
    chunked inserts based on a configurable threshold.

    A flush is triggered once the number of pending objects meets the threshold
    value. The inserts are then performed in the order of the mappings as
    provided on initiation of the BulkSaver. This allows non-cyclical
    foreign keys to resolve correctly (provided the Mapping order is correct.)
    """
    def __init__(self, session, *mappings, threshold=2000):
        self.session = session
        self.mappings = mappings
        self.threshold = threshold
        self._objects = {mapping: [] for mapping in mappings}
        self._pending = 0

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        if type is None:
            self.flush()

    def add(self, obj):
        """Adds an object to the pending collection, or nothing when `None`.

        Automatically flushes all pending objects when threshold is reached.
        """
        if obj is not None:
            self._objects[type(obj)].append(obj)
            self._pending += 1
            if self._pending >= self.threshold:
                self.flush()

    def flush(self):
        """Bulk-saves objects to the database, in mapping order."""
        for mapping in self.mappings:
            self.session.bulk_save_objects(self._objects.pop(mapping))
            self._objects[mapping] = []
        self._pending = 0


# #############################################################################
# Connectors and data loaders
#
def connect(db, user=None, echo=False):
    """Creates and returns a database engine for the given database.

    Optionally allows for specifiation of a user name (defaults to the current
    process user, and statement echo/verbosity.
    """
    if user is None:
        user = getpass.getuser()
    return create_engine(
        f'postgres://{user}@/{db}', echo=echo, use_batch_mode=True)


def seed_entries(seed_file):
    """Returns trimmed, non-empty, non-comment lines from a named seed file."""
    here = os.path.dirname(__file__)
    filename = os.path.join(here, 'seed_data', seed_file) + '.txt'
    with open(filename) as fp:
        for line in map(str.strip, fp):
            if line and not line.startswith('#'):
                yield line


def seed_json(seed_file):
    """Returns JSON loaded from given filename."""
    here = os.path.dirname(__file__)
    path = os.path.join(here, 'seed_data', seed_file) + '.json'
    with open(path) as fp:
        return json.load(fp)


def shuffle_infix(name):
    """Pulls the surname's infix to the front of the name, from the end."""
    return ' '.join(reversed(name.split(', ')))


def split_field(split_on):
    """Returns a function that splits input text, based on given parameter."""
    def _splitter(text):
        return map(str.strip, text.split(split_on))

    return _splitter


# #############################################################################
# Seed functions
#
def create_cities(session):
    """Creates cities for people to live in and companies to work at."""
    company_params = seed_json('business')
    company_params['names']['finalizer'] += company_params['names']['suffix']
    make_city = city_generator(**seed_json('cities'))
    make_company = CompanyGenerator(**company_params)
    names_and_sizes = map(split_field(';'), seed_entries('cities'))
    for city in itertools.starmap(make_city, names_and_sizes):
        size_args = itertools.repeat(city.size_code, city.seed_company_count)
        city.companies = [make_company(size) for size in size_args]
        yield city
        session.add(city)
    session.flush()


def create_transport_network(session, cities):
    """Creates a number of transport links between cities.

    This function creates a network that necessarily includes all cities in the
    graph. It achieves this by shuffling the city list and connecting every
    city to the next in the list, and finally connecting the first and last.

    To create a graph where distant nodes are (mostly) limited to `n` hops,
    a number of chains equal to the n-th root of the number of nodes should be
    created. Concretely, a graph of 1000 nodes with 10 such chains will have
    most (if not all) nodes within 3 hops of each other.
    """
    params = seed_json('transport')
    chain_count = len(cities) ** (1 / params['max_hop_distance'])
    dist = lambda: round(random.uniform(*params['distance_range']))  # noqa

    created_links = set()
    for _repeat in range(round(chain_count - 0.25)):  # biased rounding
        random.shuffle(cities)
        for city, neighbour in pairwise_full_circle(cities):
            lower, higher = sorted((city, neighbour), key=lambda city: city.id)
            if (lower, higher) not in created_links:
                created_links.add((lower, higher))
                yield TransportLink(
                    lower_city=lower, higher_city=higher, distance=dist())


def create_population(session, cities):
    """Creates a population for each city, and puts them to work.

    Given the large amount of objects (Person and Employment) generated by this
    function and its sub-parts, the SQLAlchemy ORM unit of work is bypassed in
    favour of bulk inserts. The following changes are made:

    - Primary keys are prepopulated rather than retrieved after insertion
    - Relationships are assigned via FK-fields rather than through the ORM
    - Objects are bundled and saved in bulk using `Session.bulk_save_objects`
    - Objects are grouped and sent to the database in medium sized batches

    These changes combined reduce insert time by approximately 60%, and reduce
    the memory footprint from around 1GB to ~50MB.
    """
    make_people = PopulationGenerator(
        map(shuffle_infix, seed_entries('last_names')),
        seed_entries('first_names_feminine'),
        seed_entries('first_names_masculine'))
    serial = itertools.count(1)
    with BulkSaver(session, Person, Employment) as batch:
        for city in cities:
            for person in make_people(city.seed_population_size):
                person.id = next(serial)
                person.city_id = city.id
                batch.add(person)
                batch.add(employ_person(person, city.companies))


def create_commuters(session, cities, closest_n=15):
    """For the unemployed, searches for employment in nearby cities.

    For each person in the pool of unemployed people, an atempt is made to
    employ them in cities nearby the one they live in. A list of nearby cities
    is made based on results from Dijkstra's shortest path algorithm, and an
    attempt at employment is made at each employer in a number of nearby cities
    taken from `closest_n`.
    """
    neighbouring = {}
    with BulkSaver(session, Employment) as batch:
        for person in unemployed_people(session):
            city = person.city
            if city not in neighbouring:
                distance, _previous = dijkstra(cities, city)
                neighbours = sorted(distance, key=distance.__getitem__)
                neighbouring[city] = neighbours[1:closest_n + 1]
            companies = itertools.chain.from_iterable(
                neighbour.companies for neighbour in neighbouring[city])
            batch.add(employ_person(person, companies))


def create_self_employment(session):
    """Assigns income from self-employment to share of unemployed people."""
    with BulkSaver(session, Person) as batch:
        for person in unemployed_people(session):
            if random.random() > 0.5:
                city_salary = person.city.companies[0].seed_salary()
                salary_multiplier = random.uniform(0.5, 1.2)
                person.self_employment_income = city_salary * salary_multiplier
                batch.add(person)


def employ_person(person, companies):
    """Assign the person an employer from a list of companies."""
    def role_and_salary(company):
        percentile = random.uniform(0, 100)
        if percentile < 85:
            return {'role': 'worker', 'salary': company.seed_salary()}
        salaries = company.seed_salary(), company.seed_salary()
        if percentile < 98:
            return {'role': 'manager', 'salary': max(salaries)}
        return {'role': 'director', 'salary': sum(salaries)}

    for company in companies:
        if random.random() < company.seed_hiring_chance:
            company.seed_employee_count += 1
            company.seed_hiring_chance = math.pow(
                company.seed_hiring_slowdown, -company.seed_employee_count)
            return Employment(
                person_id=person.id,
                company_id=company.id,
                **role_and_salary(company))


def unemployed_people(session):
    """Returns a query for people without an employer (Company)."""
    employment_q = session.query(Employment).filter_by(person_id=Person.id)
    return session.query(Person).filter(~employment_q.exists()).yield_per(500)


def pairwise_full_circle(sequence):
    """Yields 2-tuples of two sequential items from the sequene.

    The final value contains a pair of the last item from the sequence
    combined with the very first item from the sequence.
    """
    this, ahead = itertools.tee(sequence)
    ahead = itertools.chain(ahead, [next(ahead)])
    return zip(this, ahead)


def main():
    def emit(text, start_time=time.time()):
        elapsed = round((time.time() - start_time), 1)
        print('[{:>4.1f}s] {}'.format(elapsed, '\n\t '.join(text.split('\n'))))

    emit('(Re-)creating database and tables for SmallVille')
    engine = connect('smallville')
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    session = sessionmaker(bind=engine)()

    emit('Creating cities and companies ..')
    cities = list(create_cities(session))
    emit('  Number of cities: {}'.format(len(cities)))
    emit('  Total company count: {}'.format(
        sum(city.seed_company_count for city in cities)))
    emit('  Total population size: {}'.format(
        sum(city.seed_population_size for city in cities)))

    emit('Creating transport network ..')
    network = list(create_transport_network(session, cities))
    emit(f'  Number of transport links: {len(network)}')

    emit('Creating population and employment ..')
    create_population(session, cities)
    emit('  Number of locally employed people: {}'.format(
        session.query(Employment).count()))
    create_commuters(session, cities)
    emit('  Number of commuters: {}'.format(
        session.query(Employment)
        .join(Employment.person, Employment.company)
        .filter(Person.city_id != Company.city_id)
        .count()))
    create_self_employment(session)
    emit('  Number of (partially) self-employed: {}'.format(
        session.query(Person)
        .filter(Person.self_employment_income != null())
        .count()))

    emit('Committing ..')
    session.commit()
    emit('All done!')


if __name__ == '__main__':
    main()
