import numpy as np
import ray
import graph_tool as gt
from graph_tool.all import *
import import_from_tenaris_catalogue  # our code from part 1

def make_graph(catalogue):
    # Now we want to initiate our graph - we'll make the edges directional, i.e.
    # they will go from large to small
    graph = gt.Graph(directed=True)
    
    return graph

def calculate_pipe_burst_pressure(
    yield_strength,
    wall_thickness,
    pipe_outside_diameter,
    safety_factor=1.0
):
    burst_pressure = (
        (2 * yield_strength * 1000 * wall_thickness)
        / (pipe_outside_diameter * safety_factor)
    )

    return burst_pressure

def add_burst_pressure_to_graph(graph, yield_min=55, yield_max=125):
    attrs = ['pipe_burst_pressure_min', 'pipe_burst_pressure_max']
    for a in attrs:
        graph.vertex_properties[a] = (
            graph.new_vertex_property("double")
        )
    burst_min = calculate_pipe_burst_pressure(
        yield_strength=yield_min,
        wall_thickness=graph.vp['pipe_body_wall_thickness'].get_array(),
        pipe_outside_diameter=(
            graph.vp['pipe_body_inside_diameter'].get_array()
            + 2 * graph.vp['pipe_body_wall_thickness'].get_array()
        ),
        safety_factor=1.0
    )
    # lazy calculation of burst max - factoring the burt min result
    burst_max = (
        burst_min / yield_min * yield_max
    )
    # add the calculated results to our graph vertex properties
    for k, v in {
        'pipe_burst_pressure_min': burst_min,
        'pipe_burst_pressure_max': burst_max
    }.items():
        graph.vp[k].a = v

    return graph

def add_vertices(
    graph, manufacturer, type, type_name, tags, data
):
    """
    Function for adding a node with attributes to a graph.

    Parameters
    ----------
    graph: Graph object
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
    graph: Graph object
        Returns the Graph object with the additional node(s).
    """
    # when we start adding more conections, we need to be careful with indexing
    # so here we make a note of the current index of the last vertex and the
    # number of vertices we're adding
    start_index = len(list(graph.get_vertices()))
    number_of_vertices = len(data)

    graph.add_vertex(number_of_vertices)

    # here we initate our string vertex property maps
    vprops = {
        'manufacturer': manufacturer,
        'type': type,
        'name': type_name
    }

    # and then add these property maps as internal property maps (so they're)
    # included as part of our Graph
    for key, value in vprops.items():
        # check if property already exists
        if key in graph.vertex_properties:
            continue
        else:
            graph.vertex_properties[key] = (
                graph.new_vertex_property("string")
            )
        for i in range(start_index, number_of_vertices):
            graph.vertex_properties[key][graph.vertex(i)] = value
    
    # initiate our internal property maps for the data and populate them
    for t, d in zip(tags, data.T):
        # check if property already exists
        if t in graph.vertex_properties:
            continue
        else:
            graph.vertex_properties[t] = (
                graph.new_vertex_property("double")
            )
        # since these properties are scalar we can assign with arrays
        graph.vertex_properties[t].get_array()[
            start_index: number_of_vertices
        ] = d

    # overwrite the size - in case it didn't import properly from the pdf
    graph.vertex_properties['size'].get_array()[
        start_index: number_of_vertices
    ] = (
        graph.vertex_properties['pipe_body_inside_diameter'].get_array()[
            start_index: number_of_vertices
        ] + 2 * graph.vertex_properties['pipe_body_wall_thickness'].get_array()[
            start_index: number_of_vertices
        ]
    )

    # calculate and add our min and max pipe body burst pressures
    graph = add_burst_pressure_to_graph(graph)
    
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

    # get indexes of casing connections - we're thinking ahead since in the
    # future we might be adding more than just casing connections to our graph
    idx = [
        i for i, type in enumerate(graph.vp['type'])
        if type == 'casing_connection'
    ]

    # ensure that all the vertex properties exist - this list will likely
    # expand so at some point we might want a parameters file to store all our
    # property names that can be edited outside of this code
    vps = ['coupling_outside_diameter', 'box_outside_diameter']
    for vp in vps:
        if vp not in graph.vp:
            graph.vertex_properties[vp] = (
                graph.new_vertex_property("double")
            )

    # hold onto your seats... we're using array methods to do this super fast
    # calculate the clearance for every combination of connections
    clearance = np.amin((
            graph.vp['pipe_body_drift'].get_array()[idx],
            graph.vp['connection_inside_diameter'].get_array()[idx]
    ), axis=0).reshape(-1, 1) - np.amax((
        graph.vp['coupling_outside_diameter'].get_array()[idx],
        graph.vp['box_outside_diameter'].get_array()[idx],
        graph.vp['pipe_body_inside_diameter'].get_array()[idx]
        + 2 * graph.vp['pipe_body_wall_thickness'].get_array()[idx]
    ), axis=0).T
    
    # our data is raw and ideally needs cleaning, but in the meantime we'll
    # just ignore errors so that we don't display them to the console
    with np.errstate(invalid='ignore'):
        clearance_idx = np.where(
            np.all((
                clearance > 0,
                (
                    graph.vp['size'].get_array()[idx].T
                    / graph.vp['size'].get_array()[idx].reshape(-1, 1)
                    > cut_off
                )
            ), axis=0)
        )

    # make a list of our edges
    edges = np.vstack(clearance_idx).T

    # initiate an internal property map for storing clearance data
    graph.edge_properties['clearance'] = (
        graph.new_edge_property('double')
    )

    # add our edges to the graph along with their associated clearances
    # although we're not using this property yet, we might want to when
    # filtering our options later
    graph.add_edge_list(
        np.concatenate(
            (edges, clearance[clearance_idx].reshape(-1, 1)), axis=1
        ), eprops=[graph.edge_properties['clearance']]
    )

    return graph

# def get_roots_and_leaves(graph, surface_casing_size=18.625):
#     roots = np.where(graph.get_in_degrees(graph.get_vertices()) == 0)
#     roots = roots[0][np.where(
#         graph.vp['size'].get_array()[roots] == surface_casing_size
#     )]

#     leaves = np.where(graph.get_out_degrees(graph.get_vertices()) == 0)[0]

#     return roots, leaves

def get_roots_and_leaves(graph, surface_casing_size=18.625):
    roots = np.where(np.all((
        graph.vp['vertices_filter'].a,
        graph.vp['size'].a == surface_casing_size
    ), axis=0))[0]

    leaves = graph.get_vertices()[np.where(
        graph.get_out_degrees(graph.get_vertices()) == 0
    )[0]]

    return roots, leaves

@ray.remote
def get_paths(graph, source, target):
    paths = [
        tuple(path) for path in gt.topology.all_paths(
            graph, source, target
        )
    ]
    return paths

def set_vertex_filter(
    graph,
    surface_casing_size=18.625,
    surface_casing_wall_thickness=0.5,
    production_envelope_id_min=6.2
):
    # first let's filter out all vertices that are 18 5/8" except for the
    # one with the wall thickness of 0.5" that we desire
    filter_surface_casing = np.invert(np.all((
        graph.vp['size'].a >= surface_casing_size,
        graph.vp['pipe_body_wall_thickness'].a != surface_casing_wall_thickness
    ), axis=0))

    # we can also filter out anything that has an internal drift diameter of
    # 6.2" or smaller
    filter_leaves = np.invert(np.any((
        graph.vp['pipe_body_drift'].a <= production_envelope_id_min,
        graph.vp['pipe_body_inside_diameter'].a <= production_envelope_id_min,
        graph.vp['connection_inside_diameter'].a <= production_envelope_id_min
    ), axis=0))

    # create a boolean mask that we can apply to our graph
    graph_filter = np.all((
        filter_surface_casing,
        filter_leaves
    ), axis=0)

    # create a PropertyMap to store our mask/filter and assign our array to it
    graph.vp['vertices_filter'] = graph.new_vertex_property('bool')
    graph.vp['vertices_filter'].a = graph_filter

    # apply the filter to the graph
    graph.set_vertex_filter(graph.vp['vertices_filter'])

    # return the filtered graph
    return graph

def main():
    # this runs the code from part 1 (make sure it's in your working directory)
    # and assigns the data to the variable catalogue
    catalogue = import_from_tenaris_catalogue.main()

    # initiate our graph and ray
    graph = make_graph(catalogue)
    ray.init()

    # add the casing connections from our catalogue to the network graph
    for product, data in catalogue.items():
        graph = add_vertices(
            graph,
            manufacturer='Tenaris',
            type='casing_connection',
            type_name=product,
            tags=data.get('headers'),
            data=data.get('data')
        )
    
    # determine which connections fit through which and add the appropriate
    # edges to the graph.
    graph = add_connection_edges(graph)

    graph = set_vertex_filter(graph)

    # place a copy of the graph in shared memory
    graph_remote = ray.put(graph)

    # # determine roots and leaves
    roots, leaves = get_roots_and_leaves(graph)


    # generate pairs of source and target nodes/vertices
    # we do this primarily to maximise utility of multiprocessing, to minimise
    # processor idling
    input = np.array(
        [data for data in map(np.ravel, np.meshgrid(roots, leaves))]
    ).T

    # loop through inputs and append paths to a list, using ray
    paths = ray.get([
        get_paths.remote(graph, s, t)
        for s, t in input
    ])

    # we end up with a list of lists which we need to flatten to a simple list
    paths = [item for sublist in paths for item in sublist]

    # we're only interested in paths of 7 or more
    paths_filtered_number_of_strings = [p for p in paths if len(p) == 5]

    # we only want paths where the production casing (which is the 3rd string
    # from the end) has a maximum burst pressure larger than the 10,000 psi
    # requirement from our Production Technologist
    paths_filtered_production_casing_burst = [
        p for p in paths_filtered_number_of_strings
        if graph.vp['pipe_burst_pressure_max'].a[p[-3]] > 10000
    ]

    first_five = [
        [
            f"{graph.vp['size'][p]} in - {graph.vp['nominal_weight'][p]} ppf"
            for p in path
        ] for path in paths_filtered_number_of_strings[:5]
    ]

    print(
        f"Number of casing design permutations: "
        f"{len(paths_filtered_number_of_strings):,}"
    )
    print("First five permutations (size - nominal weight):")
    for path in first_five:
        print(path)

    # filter results
    paths_filtered_first_position = [
        p for p in paths_filtered_number_of_strings
        if max(
            graph.vp['box_outside_diameter'].a[p[1]],
            graph.vp['coupling_outside_diameter'].a[p[1]]
        ) < 14.0
    ]

    paths_filtered_second_position = [
        p for p in paths_filtered_first_position
        if max(
            graph.vp['box_outside_diameter'].a[p[2]],
            graph.vp['coupling_outside_diameter'].a[p[2]]
        ) < 11
    ]

    paths_filtered_production_casing_wt_max = [
        p for i, p in enumerate(paths_filtered_second_position)
        if i in np.where(
            graph.vp['pipe_body_wall_thickness'].a == max([
                graph.vp['pipe_body_wall_thickness'].a[p[-1]]
                for p in paths_filtered_second_position
            ])
        )[0]
    ]

    def get_clearance(graph, path):
        upper = path[:-1]
        lower = path[1:]

        clearance = sum([
            graph.ep['clearance'].a[graph.edge_index[graph.edge(u, l)]]
            for u, l in zip(upper, lower)
        ])

        return clearance

    clearance = [
        get_clearance(graph, p)
        for p in paths_filtered_production_casing_wt_max
    ]

    selected_concept = paths_filtered_production_casing_wt_max[
        np.argmax(clearance)
    ]
    
    plot(graph, paths_filtered_production_casing_wt_max, selected_concept)

    [
        f"{graph.vp['size'][p]} in - {graph.vp['nominal_weight'][p]} ppf"
        for p in selected_concept
    ]

    return graph

def plot(graph, paths, preferred_path=None):
    import plotly.graph_objects as go

    casing_sizes = np.unique(graph.vp['size'].a).tolist()

    casing_weights = {}
    for s in casing_sizes:
        if np.isnan(s):
            continue
        idx = np.where(graph.vp['size'].a == s)
        weight = graph.vp['nominal_weight'].a[idx]
        casing_weights[s] = {
            'weight_min': float(np.min(weight)),
            'weight_range': float(np.max(weight) - np.min(weight))
        }
    
    def get_edge_trace(graph, paths, color='blue', width=1.0):
        edge_x = []
        edge_y = []
        edge_c = []
        pos = {}
        for path in paths:
            upper = path[:-1]
            lower = path[1:]
            for items in zip(upper, lower):
                for i in items:
                    edge_x.append((
                        graph.vp['nominal_weight'].a[i]
                        - casing_weights[
                            graph.vp['size'].a[i]
                        ]['weight_min']
                    ) / casing_weights[
                        graph.vp['size'].a[i]
                    ]['weight_range'])
                    edge_y.append(graph.vp['size'].a[i])
            edge_x.append(None)
            edge_y.append(None)
        
        edge_trace = go.Scatter(
            x=edge_x, y=edge_y,
            line=dict(
                width=width,
                color=color
            ),
            mode='lines',
            showlegend=False
        )
        return edge_trace

    edge_trace = get_edge_trace(graph, paths)
    if preferred_path:
        preferred_edge_trace = get_edge_trace(
            graph, [preferred_path], color='red', width=2.0
        )
    else:
        preferred_edge_trace = []

    # flatten the paths and get unique list of nodes
    nodes = list(set([item for sublist in paths for item in sublist]))

    node_x = []
    node_y = []
    node_text = []
    for node in nodes:
        node_x.append((
            graph.vp['nominal_weight'].a[node]
                - casing_weights[
                    graph.vp['size'].a[node]
                ]['weight_min']
        ) / casing_weights[
            graph.vp['size'].a[node]
        ]['weight_range'])
        node_y.append(graph.vp['size'].a[node])
        node_text.append(
            f"{graph.vp['size'].a[node]} in"
            f" : {graph.vp['nominal_weight'].a[node]} ppf"
        )
    
    node_trace = go.Scatter(
        x=node_x, y=node_y,
        mode='markers+text',
        text=node_text,
        textposition="top center",
        marker=dict(
            size=20,
            line_width=2
        ),
        showlegend=False
        )

    layout = go.Layout(
        title="Casing Design Concepts",
        xaxis=dict(
            title="Normalized Weight (ppf)",
            autorange=True,
            # showgrid=False,
            ticks='',
            showticklabels=False
        ),
        yaxis=dict(
            title="Nominal Size (inches)"
        )
    )


    fig = go.Figure(
        data=[edge_trace, preferred_edge_trace, node_trace],
        layout=layout
    )

    fig.show()
    
if __name__ == '__main__':
    graph = main()

    print("Done")
