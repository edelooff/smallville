import collections

from . queues import BinaryQueue


def construct_path(vertex, reverse_paths):
    """Returns the shortest path to a vertex using the reverse_path mapping."""
    path = []
    while vertex is not None:
        path.append(vertex)
        vertex = reverse_paths[vertex]
    return list(reversed(path))


def dijkstra(graph, start):
    """Given a graph and start, returns distances to all reachable vertices.

    This implementation uses a binary heap priority queue to keep track of
    unvisited vertices in order of lowest distance, removing the need for
    constant re-sorting.
    """
    distance = collections.defaultdict(lambda: float('inf'))
    distance[start] = 0
    queue = BinaryQueue(distance)
    reverse_path = {}

    for vertex, dist_v in queue:
        for neighbour, dist_n in vertex.transport_links.items():
            new_distance = dist_v + dist_n
            if new_distance < distance[neighbour]:
                distance[neighbour] = new_distance
                reverse_path[neighbour] = vertex
                queue[neighbour] = new_distance
    return distance, reverse_path
