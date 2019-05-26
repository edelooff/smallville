import bisect
import datetime
import functools
import math
import operator
import random

from . models import (
    City,
    Company)


class CompanyGenerator:
    """Creates Company objects with a name, industry and seed parameters.

    Company names are generated from prefix, suffix and often a finalizer part.
    Industries are picked at random (uniformly) from a list. For each returned
    company, the following seed attributes are also provided:

        - seed_employee_count: used to calculate the hiring chance
        - seed_hiring_chance: chance to hire employee, domain [0, 1] (inital 1)
        - seed_hiring_slowdown: used to calculate the hiring chance, used in
            conjunction with the employee count. the slowdown parameter is a
            real number slighlt over one and is raised to the power of the
            employee count. the reciprocal of this is the hiring chance
        - seed_salary: function to pick a randmo salary, from a gaussian
            distribution. The mean and standard deviation are retrieved from
            parameters based on the city size code.
    """
    def __init__(self, industries, names, salary_bands, hiring_slowdown):
        self._industries = list(industries)
        self._name_prefix = list(names['prefix'])
        self._name_suffix = list(names['suffix'])
        self._name_finalizer = list(names['finalizer'])
        self._salaries = salary_bands
        self._hiring = hiring_slowdown

    def __call__(self, city_size):
        """Returns a Company object with seed parameters based on city size."""
        company = Company(
            industry=random.choice(self._industries),
            name=self.random_name())
        company.seed_employee_count = 0
        company.seed_hiring_chance = 1
        company.seed_hiring_slowdown = random.gauss(*self._hiring[city_size])
        company.seed_salary = functools.partial(
            random.gauss, *self._salaries[city_size])
        return company

    def random_name(self):
        """Returns a random name for a company."""
        name_parts = [self._name_prefix, self._name_suffix]
        if random.random() > 0.33:
            name_parts.append(self._name_finalizer)
        return ' '.join(map(random.choice, name_parts))


class PopulationGenerator:
    BIRTHDATE_RANGE = datetime.date(1980, 1, 1), datetime.date(1998, 1, 1)

    def __init__(
            self,
            last_names,
            names_feminine,
            names_masculine,
            birthdate_range=None):
        self._last_names = list(last_names)
        self._first_names = {
            'f': list(names_feminine),
            'm': list(names_masculine)}
        self._first_names['x'] = operator.add(*self._first_names.values())
        if birthdate_range is None:
            birthdate_range = self.BIRTHDATE_RANGE
        self._birth_epoch = min(birthdate_range)
        self._birth_range = abs(operator.sub(*birthdate_range).total_seconds())

    def __call__(self, size, last_name_pool=None):
        """Returns a generator for a population of the given size.

        If given a last_name_pool, this pool will be used to select last names.
        If no pool is given, it is provided by the `last_name_pool` method.
        """
        if last_name_pool is None:
            last_name_pool = self.last_name_pool(size)
        for _step in range(size):
            gender = self.random_gender()
            yield {
                'birthday': self.random_birthday(),
                'gender': gender,
                'first_name': random.choice(self._first_names[gender]),
                'last_name': pick_member(last_name_pool)}

    def last_name_pool(self, population_size, density_exponent=0.65):
        """Returns a pool of last names, based on population size.

        The sample size is calculated by raising the population size to the
        power of `density_exponent` (a value between 0 and 1). This exponent
        defaults to 0.65. The sample size is limited to the total number of
        names in the last name list.
        """
        natural_count = math.ceil(population_size ** density_exponent)
        sample_size = min(natural_count, len(self._last_names))
        return random.sample(self._last_names, sample_size)

    def random_birthday(self, distribution_func=random.uniform):
        """Returns a seconds-precise random birthdate in the configured range.

        By default, a uniformly distributed random point in time between the
        epoch and the maximum is returned. This can be influenced by providing
        a `distribution_func`. This function should accept 2 parameters: the
        minimum and maximum offset from the birth epoch.
        """
        offset = int(distribution_func(0, self._birth_range))
        return self._birth_epoch + datetime.timedelta(seconds=offset)

    @staticmethod
    def random_gender():
        """Returns a random gender for a person: male, female or non-binary.

        There is a slight bias towards the female gender, as observed in Dutch
        census data (as of 2018). Non-binary genders are returned at a rate of
        1 in 400, following estimated prevalence for the US and UK.
        """
        index = bisect.bisect([496, 1000], random.uniform(0, 1002.5))
        return 'mfx'[index]


def city_generator(population_ranges, company_density_range):
    """Returns a function to generate City objects and seed parameters.

    `population_ranges`: a dict with 2-tuples of (mean, stddev) to generate
        a population size from, mapped to the city size code.
    `company_density_range`: a 2-tuple of (mean, stddev) that is used to
        determine the number of companies in the city

    The returned function requires a `name` for the city and a `size`, the
    latter of which is used to look up the population parameters.

    Returned City includes parameters used for seeding:
        - `seed_company_count`: number of companies in the city
        - `seed_population_size`: number of people that live in the city
    """
    def _generator(name, size):
        population = random.gauss(*population_ranges[size])
        company_density = random.gauss(*company_density_range)
        city = City(name=name, size_code=size)
        city.seed_company_count = round(population / company_density)
        city.seed_population_size = round(population)
        return city
    return _generator


def pick_member(collection):
    """Applies the Central Limit Theorem to random index picking.

    The CLT states that the normalized sum of independent variables tends
    toward a normal distribution. This function averages three results from a
    uniform random function in the domain [0, 1) and stretches that over the
    length of the given collection to pick a random member. The resulting
    distribution is close to normal, but truncated within the range of the
    collection, without the need for clamping or rejection.

    Why exactly three random picks approximate a normal distribution very well
    but four or more don't (too narrow) is still unclear to me and is left as
    an exercise for a later date. For now we'll call it a success.
    """
    average = sum(random.random() for _n in range(3)) / 3
    return collection[int(average * len(collection))]
