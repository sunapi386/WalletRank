import numpy as np
import pandas as pd

from src.Node import Node
from src.resolve import resolve_addr2stake
import dask.dataframe as dd

class Graph:

    def __init__(self):
        self.names_to_nodes = {}

    # Return the node with the name, create and return new node if not found
    def find(self, name):
        if name in self.names_to_nodes.keys():
            return self.names_to_nodes[name]
        else:
            new_node = Node(name)
            self.names_to_nodes[name] = new_node
            return new_node

    def add_edge(self, parent, child):
        parent_node = self.find(parent)
        child_node = self.find(child)

        parent_node.link_child(child_node)
        child_node.link_parent(parent_node)

    def display(self):
        for node in self.names_to_nodes.values():
            print(f'{node.name} links to {[child.name for child in node.children]}')

    def normalize_pagerank(self):
        pagerank_sum = sum(node.pagerank for node in self.names_to_nodes.values())

        for node in self.names_to_nodes.values():
            node.pagerank /= pagerank_sum

    def get_pagerank_list(self):
        return [(node.name, node.pagerank) for node in self.names_to_nodes.values()]

    def pageRank_one_iter(self, d):
        for node in self.names_to_nodes.values():
            node.update_pagerank(d, len(self.names_to_nodes))
        self.normalize_pagerank()


def build_graph(filename):
    graph = Graph()
    df = dd.read_csv(filename)

    if 'src' in df.columns and 'dst' in df.columns:
        for row in df[['src', 'dst']].iterrows():
            idx, (src, dst) = row
            graph.add_edge(src, dst)
    elif 'sender' in df.columns and 'receiver' in df.columns:
        print(f'parsing sender to src...')
        df['src'] = df.sender.apply(resolve_addr2stake)
        print(f'parsing receiver to dst...')
        df['dst'] = df.receiver.apply(resolve_addr2stake)
        for row in df[['src', 'dst']].iterrows():
            idx, (src, dst) = row
            graph.add_edge(src, dst)

    return graph
