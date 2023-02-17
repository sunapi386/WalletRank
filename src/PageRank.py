import os

import pandas as pd

from src.Graph import build_graph


class PageRankGraph:
    def __init__(self, file_path, damping_factor, iterations):
        self.file_path = file_path
        self.graph = build_graph(file_path)
        self.iterations = iterations
        self.damping_factor = damping_factor
        self.iterate_PageRank(damping_factor, iterations)

    def iterate_PageRank(self, d, iteration=100):
        for i in range(iteration):
            self.graph.pageRank_one_iter(d)

    def output_PageRank_csv(self):
        df = pd.DataFrame(self.graph.get_pagerank_list())
        result_dir = 'out'
        if not os.path.exists(result_dir):
            os.makedirs(result_dir)
        filename = self.file_path.split('/')[-1].split('.')[0]
        df.columns = ["stake_address", "score"]
        df.sort_values(by="score")
        outfile = f"{result_dir}/{filename}.csv"
        df.to_csv(outfile, index=False)
        print(f"Wrote to {outfile}")
