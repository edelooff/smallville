import getpass
import itertools
import json
import math
import os
import random
import time

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from smallville.base import Base
from smallville.generators import (
    CompanyGenerator,
    PopulationGenerator,
    city_generator)
from smallville.models import (
    Employment,
    TransportLink)


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
    engine_url = 'postgres://{user}@/{db}'.format(user=user, db=db)
    return create_engine(engine_url, echo=echo)


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
    make_company = CompanyGenerator(**company_params)
    make_city = city_generator(**seed_json('cities'))
    names_and_sizes = map(split_field(';'), seed_entries('cities'))
    for city in itertools.starmap(make_city, names_and_sizes):
        size_args = itertools.repeat(city.size_code, city.seed_company_count)
        city.companies.extend(map(make_company, size_args))
        session.add(city)
        session.flush()
        yield city


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
    dist = lambda: round(random.uniform(*params['distance_range']))

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
    def flush_pending(*object_groups):
        for group in object_groups:
            session.bulk_save_objects(filter(None, group))
            del group[:]

    make_people = PopulationGenerator(
        map(shuffle_infix, seed_entries('last_names')),
        seed_entries('first_names_feminine'),
        seed_entries('first_names_masculine'))
    serial = itertools.count(1)
    people, employment = [], []
    for city in cities:
        for person in make_people(city.seed_population_size):
            person.id = next(serial)
            person.city_id = city.id
            people.append(person)
            employment.append(employ_person(person, city.companies))
            if not person.id % 2000:
                flush_pending(people, employment)
    flush_pending(people, employment)


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

    emit('Committing ..')
    session.commit()
    emit('All done!')


if __name__ == '__main__':
    main()
