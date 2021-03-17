import numpy as np
import networkx as nx
import ray
import create_casing_connections_graph # our code from part 2

def get_roots_and_leaves(graph):
    # initiate our lists
    roots = []
    leaves = []
    # loop through our nodes to discover our start and end nodes
    for node in graph.nodes :
        if all((
            graph.in_degree(node) == 0, # it's a root
            graph.nodes[node]['size'] == 18+5/8
        )):
            roots.append(node)
        if graph.out_degree(node) == 0 : # it's a leaf
            leaves.append(node)
    
    return roots, leaves

@ray.remote
def get_paths(graph, source, target):
    paths = [path for path in nx.all_simple_paths(graph, source, target)]
    return paths

def main():
    # initialize ray
    ray.init()
    
    # generate our graph using code from previous post
    graph = create_casing_connections_graph.main()

    # place a copy of the graph in shared memory
    graph_remote = ray.put(graph)

    # determine roots and leaves
    roots, leaves = get_roots_and_leaves(graph)

    # generate pairs of source and target nodes/vertices
    input = np.array(
        [data for data in map(np.ravel, np.meshgrid(roots, leaves))]
    ).T

    # loop through inputs and append paths to a list, using ray
    paths = ray.get([
        get_paths.remote(graph_remote, s, t)
        for s, t in input
    ])

    # we end up with a list of lists which we need to flatten to a simple list
    paths = [item for sublist in paths for item in sublist]
    first_five = [
        [
            f"{graph.nodes[p]['size']} in - {graph.nodes[p]['nominal_weight']} ppf"
            for p in path
        ] for path in paths[:5]
    ]

    print(f"Number of casing design permutations: {len(paths):,}")
    print("First five permutations (size - nominal weight):")
    for path in first_five:
        print(path)

    print("Done")

if __name__ == '__main__':
    main()