import datetime
import math
import operator
import random

from . models import Person


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


class PopulationGenerator(object):
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
            yield Person(
                birthday=self.random_birthday(),
                gender=gender,
                first_name=random.choice(self._first_names[gender]),
                last_name=pick_member(last_name_pool))

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

        There is a slight bias towards the female gender, as observed in the
        world population. Non-binary sexes are returned at a rate around 1 in
        400, following estimated prevalence for the US and UK.
        """
        male = random.uniform(0, 1)
        female = random.uniform(0.01, 1)
        if male > 0.95 and female > 0.95:
            return 'x'
        return 'f' if female > male else 'm'
