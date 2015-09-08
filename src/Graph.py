__author__ = 'rainierababao'

class Neo4jORM(object):
    """Models an object-relational mapping for the Neo4J graph database.
    """

class Graph(object):
    """Models a directed graph. Edges can have weights.
    To model an undirected graph, add an edge from vertex A
    to vertex B and another edge from vertex B to vertex A.

    To model an unweighted graph, set all edge costs to the
    same value, conventionally 0 or 1.
    """
    INFINITY = float('inf')

    def __init__(self, **kwargs):
        self.vertices = {}
        self.__dict__.update(kwargs)

    def add_edge(self):
        pass

class Edge(object):
    """Models an edge between two vertices.
    """

    def __init__(self, dest, cost, **kwargs):
        if not isinstance(dest, Vertex):
            raise ValueError('Destination must be of type Vertex')
        self.dest = dest
        self.cost = cost
        self.__dict__.update(kwargs)

    def __str__(self):
        return '{0} {1}'.format(self.dest, self.cost)

class Vertex(object):
    """Models a vertex.
    """

    def __init__(self, name, **kwargs):
        self.name = name
        self.adjacent = []
        self.num_connections = 0

        # Caching these attributes should make some algorithms run a lot faster
        self.total_unweighted_path_length = 0
        self.total_weighted_path_length = 0
        self.weighted_cost_from_start_node = 0
        self.num_edges_from_start_node = 0
        self.prev = None
        self.__dict__.update(kwargs)

class Path(object):
    """Models a path between vertices.
    """

    def __init__(self, vertex=None, cost=None):
        self.vertices_in_path = []
        if vertex and cost:
            self.vertex = vertex
            self.weighted_cost_of_path = cost
