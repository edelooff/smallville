import collections


class Vertex:
    """Queue entry for VertexQueue, storing a destination and its cost."""
    __slots__ = 'cost', 'vertex'

    def __init__(self, vertex, cost):
        self.cost = cost
        self.vertex = vertex

    def __lt__(self, other):
        return self.cost < other.cost


class VertexQueue:
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
                self._siftdown(0, tail)
            yield entry.vertex, entry.cost

    def __setitem__(self, vertex, cost):
        """Updates existing entry in the heap, or inserts a new one."""
        pos = self._index_map.get(vertex)
        if pos is not None:
            entry = self._heap[pos]
            entry.cost = cost
        else:
            pos = len(self._heap)
            entry = Vertex(vertex, cost)
            self._heap.append(entry)
        self._siftup(pos, entry)

    def _siftdown(self, pos, entry):
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
        child_pos = pos * 2 + 1
        while child_pos < heaplen:
            right_pos = child_pos + 1
            if right_pos < heaplen and heap[right_pos] < heap[child_pos]:
                child_pos = right_pos
            child_entry = heap[child_pos]
            heap[pos] = child_entry
            imap[child_entry.vertex] = pos
            pos = child_pos
            child_pos = pos * 2 + 1
        self._siftup(pos, entry)

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


def construct_path(vertex, reverse_paths):
    """Returns the shortest path to a vertex using the reverse_path mapping."""
    path = []
    while vertex is not None:
        path.append(vertex)
        vertex = reverse_paths[vertex]
    return list(reversed(path))


def dijkstra(graph, start):
    """Given a graph and start, returns distances to all reachable vertices.

    This implementation uses a heap (VertexQueue) to keep track of unvisited
    vertices in order of lowest distance, removing the need for re-sorting.
    """
    distance = collections.defaultdict(lambda: float('inf'))
    distance[start] = 0
    queue = VertexQueue(distance)
    reverse_path = {}

    for vertex, dist_v in queue:
        for neighbour, dist_n in vertex.transport_links.items():
            new_distance = dist_v + dist_n
            if new_distance < distance[neighbour]:
                distance[neighbour] = new_distance
                reverse_path[neighbour] = vertex
                queue[neighbour] = new_distance
    return distance, reverse_path
