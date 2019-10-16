import itertools

import pytest

from smallville.queues import (
    BinaryQueue,
    PairingQueue)


@pytest.fixture(params=[BinaryQueue, PairingQueue])
def queue(request):
    """Returns an empty Queue instance."""
    return request.param


@pytest.fixture(params=['linear', 'organpipe', 'interleaved', 'shifted'])
def _sequence(request):
    """Returns a list of numbers in several different variations."""
    length = 500
    if request.param == 'linear':
        return list(range(length))
    if request.param == 'organpipe':
        peak = length // 4 * 3
        return list(itertools.chain(range(peak), range(peak, 0, -3)))
    if request.param == 'interleaved':
        return list(itertools.chain.from_iterable(zip(
            range(length // 2), range(length // 2, length))))
    if request.param == 'shifted':
        return list(itertools.chain(
            range(length // 10, length), range(length // 10)))


@pytest.fixture(params=['natural', 'reversed'])
def sequence(request, _sequence):
    if request.param == 'reverse':
        return list(reversed(_sequence))
    return _sequence
