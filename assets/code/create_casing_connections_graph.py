import numpy as np
import networkx as nx
import import_from_tenaris_catalogue  # our code from part 1

class Counter:
    def __init__(self, start=0):
        """
        A simple counter class for storing a number that you want to increment
        by one.
        """
        self.counter = start
    
    def count(self):
        """
        Calling this method increments the counter by one and returns what was
        the current count.
        """
        self.counter += 1
        return self.counter - 1

    def current(self):
        """
        If you just want to know the current count, use this method.
        """
        return self.counter


def make_graph(catalogue):
    # Now we want to initiate our graph - we'll make the edges directional, i.e.
    # they will go from large to small
    graph = nx.DiGraph()
    
    return graph

def add_node(
    counter, graph, manufacturer, type, type_name, tags, data
):
    """
    Function for adding a node with attributes to a graph.

    Parameters
    ----------
    counter: Counter object
    graph: (Di)Graph object
    manufacturer: str
        The manufacturer of the item being added as a node.
    type: str
        The type of item being added as a node.
    type_name: str
        The (product) name of the item being added as a node.
    tags: list of str
        The attribute tags (headers) of the attributes of the item.
    data: list or array of floats
        The data for each of the attributes of the item.

    Returns
    -------
    graph: (Di)Graph object
        Returns the (Di)Graph object with the addition of a new node.
    """
    # we'll first create a dictionary with all the node attributes
    node = {
        'manufacturer': manufacturer,
        'type': type,
        'name': type_name
    }
    # loop through the tags and data
    for t, d in zip(tags, data):
        node[t] = d
    # get a UID and assign it
    uid = counter.count()
    node['uid'] = uid

    # overwrite the size - in case it didn't import properly from the pdf
    size = (
        node['pipe_body_inside_diameter']
        + 2 * node['pipe_body_wall_thickness']
    )
    # use the class method to add the node, unpacking the node dictionary
    # and naming the node with its UID
    graph.add_node(uid, **node)
    
    return graph

def check_connection_clearance(graph, node1, node2, cut_off=0.7):
    """
    Function for checking if one component will pass through another.

    Parameters
    ----------
    graph: (Di)Graph object
    node1: dict
        A dictionary of node attributes.
    node2: dict
        A dictionary of node attributes.
    cut_off: 0 < float < 1
        A ration of the nominal component size used as a filter, e.g. if set
        to 0.7, if node 1 has a size of 5, only a node with a size greater than
        3.5 will be considered.

    Returns
    -------
    graph: (Di)Graph object
        Graph with an edge added if node2 will drift node1, with a `clearance`
        attribute indicating the clearance between the critical outer diameter
        of node2 and the drift of node1.
    """
    try:
        node2_connection_od = node2['coupling_outside_diameter']
    except KeyError:
        node2_connection_od = node2['box_outside_diameter']
    clearance = min(
            node1['pipe_body_drift'],
            node1['connection_inside_diameter']
    ) - max(
        node2_connection_od,
        node2['pipe_body_inside_diameter']
        + 2 * node2['pipe_body_wall_thickness']
    )
    if all((
        clearance > 0,
        node2['size'] / node1['size'] > cut_off
    )):
        graph.add_edge(node1['uid'], node2['uid'], **{'clearance': clearance})
    
    return graph

def add_connection_edges(graph, cut_off=0.7):
    """
    Function to add edges between connection components in a network graph.

    Parameters
    ----------
    graph: (Di)Graph object
    cut_off: 0 < float < 1
        A ration of the nominal component size used as a filter, e.g. if set
        to 0.7, if node 1 has a size of 5, only a node with a size greater than
        3.5 will be considered.

    Returns
    -------
    graph: (Di)Graph object
        Graph with edges added for connections that can drift through other
        connections.
    """
    for node_outer in graph.nodes:
        # check if the node is a casing connection
        if graph.nodes[node_outer]['type'] != 'casing_connection':
            continue
        for node_inner in graph.nodes:
            if graph.nodes[node_inner]['type'] != 'casing_connection':
                continue
            graph = check_connection_clearance(
                graph, 
                graph.nodes[node_outer],
                graph.nodes[node_inner],
                cut_off
            )

    return graph

def main():
    # this runs the code from part 1 (make sure it's in your working directory)
    # and assigns the data to the variable catalogue
    catalogue = import_from_tenaris_catalogue.main()

    # initiate our counter and graph
    counter = Counter()
    graph = make_graph(catalogue)

    # add the casing connections from our catalogue to the network graph
    for product, data in catalogue.items():
        for row in data['data']:
            graph = add_node(
                counter,
                graph,
                manufacturer='Tenaris',
                type='casing_connection',
                type_name=product,
                tags=data['headers'],
                data=row
            )
    
    # determine which connections fit through which and add the appropriate
    # edges to the graph.
    graph = add_connection_edges(graph)

    return graph
    
if __name__ == '__main__':
    graph = main()

    # as a QAQC step we can use matplotlib to draw the edges between connected
    # casing connections

    import matplotlib
    import matplotlib.pyplot as plt

    matplotlib.use("TKAgg")  # Ubuntu sometimes needs some help

    nx.draw_networkx(graph, pos=nx.circular_layout(graph))
    plt.show()

    print("Done")
