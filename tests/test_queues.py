"""Test suite for the smallville.queues module."""

import pytest


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


def test_iteration_empties_queue(queue):
    """Iterating over the queue empties it."""
    q = queue({'a': 1})
    assert list(q) == [('a', 1)]
    assert list(q) == []
    with pytest.raises(StopIteration):
        next(iter(q))


def test_initialize_and_decrease(queue):
    """Initializing and then decreasing that value return updated value."""
    q = queue({'a': 1})
    q['a'] = 5
    assert list(q) == [('a', 5)]


def test_order_insert_exhaust(queue, sequence):
    """Queue returns items in sorted (ascending) order."""
    q = queue()
    for idx, value in enumerate(sequence):
        q[idx] = value
    assert [val for idx, val in q] == sorted(sequence)


def test_order_insert_decrease_exhaust(queue, sequence):
    """Queue returns items in sorted (ascending) order after decreases."""
    q = queue(dict(enumerate(sequence)))
    expected = {}
    for idx, value in enumerate(sequence):
        # Alternates between larger and smaller reductions, trending smaller
        reduction = (1 / (idx + 1)) * len(sequence) * (idx % 2 + 0.5)
        expected[idx] = q[idx] = value - reduction
    assert [val for idx, val in q] == sorted(expected.values())
