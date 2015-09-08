from bulbs.neo4jserver import Graph, Config, NEO4J_URI
from texts.config import NEO4J_URI, NEO4J_USER, NEO4J_PASS
from texts.py import *

g = Graph(config)

def create_link(v1, v2, e1, verb):
    g.vertices.create(name='v1')
    g.vertices.create(name='v2')
    g.edges.create(v1, verb, v2)

