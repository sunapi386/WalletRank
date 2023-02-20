import json
import unittest

from src.Graph import Graph
from src.Node import Node
from src.PageRank import PageRankGraph
from src.resolve import resolve_addr2stake


def all_equal(iterator):
    iterator = iter(iterator)
    try:
        first = next(iterator)
    except StopIteration:
        return True
    return all(first == x for x in iterator)


#https://stackoverflow.com/questions/25851183/how-to-compare-two-json-objects-with-the-same-elements-in-a-different-order-equa
def ordered(obj):
    if isinstance(obj, dict):
        return sorted((k, ordered(v)) for k, v in obj.items())
    if isinstance(obj, list):
        return sorted(ordered(x) for x in obj)
    else:
        return obj

class Tests(unittest.TestCase):

    def test_resolve_addr2stake(self):
        addrs = [
            'addr1qyygx4fw97wdqj6gr2zl9xcaxr4pek3l5nd4hgcrtr9vq0trt0d9x8stdern4227k24w8yq6g6g5fg6rwxav39szej4supw4qz',
            'addr1qx3zplpafymacnmw3234avrtmpham35zkxptmetp74j6jsmrt0d9x8stdern4227k24w8yq6g6g5fg6rwxav39szej4stdqf6k',
            'addr1qxt60qght7ryz7w543ndr9qyc92e9q7lqxhlkqfp68lceqnrt0d9x8stdern4227k24w8yq6g6g5fg6rwxav39szej4sm2596p']
        stakes = [resolve_addr2stake(a) for a in addrs]
        self.assertTrue(all_equal(stakes))
        self.assertEqual('stake1u934hkjnrc9ku3e6490t92hrjqdydy2y5dphrwkgjcpve2cydqvjq', stakes[0])

    def test_pagerank(self):
        graph = Graph()
        edges = [(1, 2),
                 (2, 3),
                 (3, 4),
                 (4, 5),
                 (5, 6)]
        for src, dst in edges:
            graph.add_edge(src, dst)
        iteration = 500
        damp = 0.15
        for i in range(iteration):
            graph.pageRank_one_iter(damp)

        pr = graph.get_pagerank_list()
        approx = [(1, 0.0607),
                  (2, 0.1123),
                  (3, 0.1561),
                  (4, 0.1934),
                  (5, 0.2251),
                  (6, 0.2521)]
        self.assertEqual(len(pr), len(approx))
        for actual, expected in zip(pr, approx):
            self.assertEqual(actual[0], expected[0])
            self.assertAlmostEqual(actual[1], expected[1], delta=0.001)

    def test_graph(self):
        graph = Graph()
        edges = [(1, 2),
                 (2, 3),
                 (3, 4),
                 (4, 5),
                 (5, 6)]
        for src, dst in edges:
            graph.add_edge(src, dst)
        pr = graph.get_pagerank_list()
        self.assertEqual(pr, [(1, 1.0), (2, 1.0), (3, 1.0), (4, 1.0), (5, 1.0), (6, 1.0)])

    def test_node(self):
        parent = Node.fetch('parent')
        child = Node.fetch('child')
        self.assertTrue(parent.name == 'parent')

        parent.link_child(child)
        self.assertTrue(child.name in parent.children)
        self.assertTrue(len(parent.children) == 1)

        self.assertTrue(parent not in child.parents)
        child.link_parent(parent)
        self.assertTrue(parent in child.parents)

        # test that children and parents are references only, not new copies of nodes
        # we want this feature for performance, not more copies of nodes
        self.assertTrue(parent.children[0] == child.name)
        self.assertTrue(child.parents[0] is parent)

        json_parent = parent.json()
        load_parent = json.loads(json_parent)
        copy_parent = Node(**load_parent)
        original = ordered(parent.json())
        copy = ordered(copy_parent.json())
        self.assertTrue(original == copy)

        json_child = child.json()
        load_child = json.loads(json_child)
        copy_child = Node(**load_child)
        self.assertTrue(child.json() == copy_child.json())

    def test_graph_construction(self):
        page_rank = PageRankGraph('../data/simple.csv', 0.15, 100)
        df = page_rank.output_PageRank_csv(write=False)
        self.assertEqual(len(df), len(page_rank.graph.names_to_nodes))

    def test_graph_construction_sender_receiver(self):
        page_rank = PageRankGraph('../data/sender_receiver_amount_id-100.csv', 0.15, 100)
        df = page_rank.output_PageRank_csv(write=False)
        self.assertEqual(len(df), len(page_rank.graph.names_to_nodes))

    def test_graph_construction_src_dst(self):
        page_rank = PageRankGraph('../data/src_dst_amount_id-100.csv', 0.15, 100)
        df = page_rank.output_PageRank_csv(write=False)
        self.assertEqual(len(df), len(page_rank.graph.names_to_nodes))



if __name__ == '__main__':
    unittest.main()
