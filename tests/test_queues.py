"""Test suite for the smallville.queues module."""


def test_empty_queue_falsy(queue):
    """An empty queue is Boolean False."""
    assert not queue()


def test_nonempty_queue_truthy(queue):
    """A non-empty queue is Boolean True."""
    assert queue({'a': 1})


def test_single_item_init(queue):
    """Initializing a queue with a single items returns that on iteration."""
    q = queue({'a': 1})
    assert next(iter(q)) == ('a', 1)


def test_single_item_push(queue):
    """Creating a queue and pushing a single item returns that on iteration."""
    q = queue()
    q['a'] = 1
    assert next(iter(q)) == ('a', 1)
