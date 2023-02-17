from optparse import OptionParser

from src.PageRank import PageRankGraph

if __name__ == '__main__':
    optparser = OptionParser()
    optparser.add_option('-f', '--input_file', dest='input_file', help='CSV filename', default='data/graph_sample.txt')
    optparser.add_option('--damping_factor', dest='damping_factor', help='Damping factor (float)', default=0.15, type='float')
    optparser.add_option('--decay_factor', dest='decay_factor', help='Decay factor (float)', default=0.9, type='float')
    optparser.add_option('--iterations', dest='iterations', help='Iteration (int)', default=500, type='int')

    (options, args) = optparser.parse_args()

    file_path = options.input_file
    iterations = options.iterations
    damping_factor = options.damping_factor
    decay_factor = options.decay_factor

    page_rank = PageRankGraph(file_path, damping_factor, iterations)
    page_rank.output_PageRank_csv()
