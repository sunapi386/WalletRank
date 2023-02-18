import unittest

from src.Graph import Graph
from src.Node import Node
from src.resolve import resolve_addr2stake


class Tests(unittest.TestCase):

    def test_resolve_addr2stake(self):
        addr = 'addr1q9f2prypgqkrmr5497d8ujl4s4qu9hx0w6kruspdkjyudc2xjgcagrdn0jxnf47yd96p7zdpfzny30l2jh5u5vwurxasjwukdr'
        stake = resolve_addr2stake(addr)
        self.assertEqual(stake, 'stake1u9rfyvw5pkeherf56lzxjaqlpxs53fjghl4ft6w2x8wpnwchfeam3')

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
        parent = Node('parent')
        child = Node('child')
        self.assertTrue(parent.name == 'parent')

        parent.link_child(child)
        self.assertTrue(child in parent.children)
        self.assertTrue(parent not in child.children)

        self.assertTrue(parent not in child.parents)
        child.link_parent(parent)
        self.assertTrue(parent in child.parents)


if __name__ == '__main__':
    unittest.main()
