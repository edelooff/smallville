import collections
import heapq


class Vertex(object):
    """Queue entry for VertexQueue.

    Each entry represents a path, with cost and destination vertex, as well as
    a validity flag. Removing an entry from the heap would require a costly
    search, so instead, the entry's validity flag is set to False, indicating
    that is should be discarded when retrieved from the heap.
    """
    __slots__ = 'cost', 'vertex', 'valid'

    def __init__(self, cost, vertex):
        self.cost = cost
        self.vertex = vertex
        self.valid = True

    def __lt__(self, other):
        return self.cost < other.cost


class VertexQueue(object):
    """A priority queue for vertex+distance storage.

    Uses a heap for minimum cost-sorted entries. When the cost for an entry
    is altered, the existing entry is declared invalid and will be discarded
    upon retrieval during iteration.

    Iteration will yield the next lowest and valid vertex stored in the queue.
    """
    def __init__(self, vertex_dict=None):
        self._heap = []
        self.vertex_map = {}
        if vertex_dict is not None:
            for vertex, cost in vertex_dict.items():
                self.add(vertex, cost)

    def __iter__(self):
        while self._heap:
            entry = heapq.heappop(self._heap)
            if entry.valid:
                yield entry.vertex, entry.cost

    def add(self, vertex, cost):
        entry = Vertex(cost, vertex)
        self.vertex_map[vertex] = entry
        heapq.heappush(self._heap, entry)

    def update_cost(self, vertex, cost):
        existing = self.vertex_map.get(vertex)
        if existing is not None:
            existing.valid = False
        self.add(vertex, cost)


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
        for neighbour, dist_n in vertex.paths.items():
            new_distance = dist_v + dist_n
            if new_distance < distance[neighbour]:
                distance[neighbour] = new_distance
                reverse_path[neighbour] = vertex
                queue.update_cost(neighbour, new_distance)
    return distance, reverse_path
