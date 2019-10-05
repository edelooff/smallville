from functools import reduce
from itertools import (
    starmap,
    zip_longest)


class BinaryQueue:
    """A priority queue for vertex+distance storage, backed by a binary heap.

    Iteration will pop the lowest value off the heap and return a 2-tuple of
    (vertex, cost). Adding or updating vertices and cost is done by assigning
    the cost to the vertex through subscription (`q[vertex] = cost`).

    When the cost for a destination vertex is updated (only reductions are
    allowed, though not enforced at runtime), its position is looked up, its
    value altered, and it's moved to the correct position in the heap.
    """
    def __init__(self, vertex_dict=None):
        self._heap = []
        self._index_map = {}
        if vertex_dict is not None:
            for vertex, cost in vertex_dict.items():
                self[vertex] = cost

    def __iter__(self):
        while self._heap:
            entry = self._heap[0]
            del self._index_map[entry.vertex]
            tail = self._heap.pop()
            if self._heap:
                self._siftdown(tail)
            yield entry.vertex, entry.cost

    def __setitem__(self, vertex, cost):
        """Updates existing entry in the heap, or inserts a new one."""
        pos = self._index_map.get(vertex)
        if pos is not None:
            entry = self._heap[pos]
            entry.cost = cost
        else:
            pos = len(self._heap)
            entry = _Node(vertex, cost)
            self._heap.append(entry)
        self._siftup(pos, entry)

    def _siftdown(self, entry, pos=0):
        """Moves the item at pos to its correct position deeper in the heap.

        This heavily borrows from the Python heapq implementation which uses
        the elegant intuition that items inserted at the root (following
        extraction) tend to be large. Instead of comparing the new root value,
        the heap is first restored, successively moving up the smaller of two
        child nodes.

        Once the root-inserted value hits the bottom of the heap, it is then
        sifted up as if it had been inserted at this position. This has the
        same worst-case complexity (2 log n), but works out significantly
        better in practice (requiring closer to (log n) comparisons.)
        """
        heap, imap = self._heap, self._index_map
        heaplen = len(heap)
        left = pos * 2 + 1
        while left < heaplen:
            right = left + 1
            minpos = left + (right < heaplen and heap[right] < heap[left])
            minchild = heap[minpos]
            heap[pos] = minchild
            imap[minchild.vertex] = pos
            pos = minpos
            left = pos * 2 + 1
        return self._siftup(pos, entry)

    def _siftup(self, pos, entry):
        """Swaps an entry with its parent until the heap is restored."""
        heap, imap = self._heap, self._index_map
        while pos > 0:
            parent_pos = (pos - 1) // 2
            parent_entry = self._heap[parent_pos]
            if not entry < parent_entry:
                break
            heap[pos] = parent_entry
            imap[parent_entry.vertex] = pos
            pos = parent_pos
        heap[pos] = entry
        imap[entry.vertex] = pos


class PairingQueue:
    """A priority queue for vertex+distance storage, backed by a pairing heap.

    Iteration will pop the lowest value off the heap and return a 2-tuple of
    (vertex, cost). Adding or updating vertices and cost is done by assigning
    the cost to the vertex through subscription (`q[vertex] = cost`).

    When the cost for a destination vertex is updated (only reductions are
    allowed, though not enforced at runtime), its position is looked up, its
    value altered, and it's moved to the correct position in the heap.
    """
    def __init__(self, vertex_dict=None):
        self._heap = None
        self._heapmap = {}
        if vertex_dict is not None:
            for vertex, cost in vertex_dict.items():
                self[vertex] = cost

    def __iter__(self):
        while self._heap is not None:
            entry = self._heap.root
            del self._heapmap[entry.vertex]
            # Remove current top-heap's parent reference in case it is still
            # listed as a subheap somewhere. We do this here (rather than after
            # assignment) so that we do not have to test whether we have a top-
            # level heap at all (because the while loop has just checked this)
            self._heap.parent = None
            self._heap = _merge_pairs(self._heap)
            yield entry.vertex, entry.cost

    def __setitem__(self, vertex, cost):
        heap = self._heapmap.get(vertex)
        if heap is None:
            heap = _PairingHeap(_Node(vertex, cost))
            self._heapmap[vertex] = heap
            self._heap = _merge(self._heap, heap)
        else:
            heap.root.cost = cost
            if heap.incorrectly_nested:
                self._heap = _merge(self._heap, heap)
                self._heap.parent = None


# #############################################################################
# Private classes and helper functions
#
class _Node:
    """Generic pathfinding queue entry storing a vertex and its cost."""
    __slots__ = 'cost', 'vertex'

    def __init__(self, vertex, cost):
        self.cost = cost
        self.vertex = vertex

    def __lt__(self, other):
        return self.cost < other.cost


class _PairingHeap:
    __slots__ = 'root', 'parent', '_subheaps'

    def __init__(self, root):
        self.root = root
        self.parent = None
        self._subheaps = []

    def __iter__(self):
        """Returns an iterator for the heap's valid subheaps."""
        return (heap for heap in self._subheaps if heap.parent is self)

    def add_subheap(self, heap):
        """Adds a subheap to the heap, marking the subheap's parent."""
        heap.parent = self
        self._subheaps.append(heap)
        return self

    @property
    def incorrectly_nested(self):
        """Whether or not the heap is correctly nested under its parent."""
        return self.parent is not None and self.root < self.parent.root


def _merge(h1, h2, meld=_PairingHeap.add_subheap):
    """Merges two pairing heaps or short-circuits if either arg is None."""
    if h1 is None:
        return h2
    elif h2 is None:
        return h1
    return meld(h1, h2) if h1.root < h2.root else meld(h2, h1)


def _merge_pairs(heaps):
    """Returns result of pairwise merge followed by a reducing merge."""
    iheap = iter(heaps)
    return reduce(_merge, starmap(_merge, zip_longest(iheap, iheap)), None)
