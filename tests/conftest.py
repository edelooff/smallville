import pytest

from smallville.queues import (
    BinaryQueue,
    PairingQueue)


@pytest.fixture(params=[BinaryQueue, PairingQueue])
def queue(request):
    """Returns an empty Queue instance."""
    return request.param
