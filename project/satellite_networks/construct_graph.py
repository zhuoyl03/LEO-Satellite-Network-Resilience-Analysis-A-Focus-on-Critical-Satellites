import sys
sys.path.append(os.path.expanduser("~") + "/hypatia/satgenpy")
import os
import pickle
import matplotlib.pyplot as plt
import networkx as nx
import satgen
import exputil
from astropy import units as u

SPEED_OF_LIGHT_M_PER_S = 299792458.0
GEODESIC_ECDF_PLOT_CUTOFF_KM = 500

# Function to read the data from the files
def read_usage_data(file_path, num):
    usage_data = []
    with open(file_path, 'r') as file:
        lines = file.readlines()[1:]  # Skip the header lines
        i = 0
        for line in lines:
            parts = line.strip().split(':')
            if len(parts) == 2:
                satellite_part = parts[1].strip()
                satellite_id = int(satellite_part.split(" ")[1])
                usage_data.append(satellite_id)
                i += 1
                if i >= num:
                    break
    return usage_data

# Function to construct graph by using etworkx
def construct_graph_with_distances(epoch, time_since_epoch_ns, satellites, ground_stations, list_isls,
                                   max_gsl_length_m, max_isl_length_m, deleted_satellites):
    time = epoch + time_since_epoch_ns * u.ns
    sat_net_graph_with_gs = nx.Graph()

    for sid in range(len(satellites)):
        sat_net_graph_with_gs.add_node(sid)

    for gs in range(len(ground_stations)):
        sat_net_graph_with_gs.add_node(gs + len(satellites))

    for (a, b) in list_isls:
        if a in deleted_satellites or b in deleted_satellites:
            continue
        sat_distance_m = satgen.distance_m_between_satellites(satellites[a], satellites[b], str(epoch), str(time))
        if sat_distance_m <= max_isl_length_m:
            sat_net_graph_with_gs.add_edge(a, b, weight=sat_distance_m)

    for ground_station in ground_stations:
        for sid in range(len(satellites)):
            if sid in deleted_satellites:
                continue
            distance_m = satgen.distance_m_ground_station_to_satellite(ground_station, satellites[sid], str(epoch), str(time))
            if distance_m <= max_gsl_length_m:
                sat_net_graph_with_gs.add_edge(len(satellites) + ground_station["gid"], sid, weight=distance_m)

    return sat_net_graph_with_gs


def construct_graph(directory, usage_data_file_path, satellite_network_dir, deletion_of_satellites, simulation_end_time_ns, dynamic_state_update_interval_ns): 
    # Ensure the directory exists
    if not os.path.exists(directory):
        os.makedirs(directory)

    if not os.path.exists(usage_data_file_path):
        print("usage_data_file_path is not exist")
        usage_data = []
    else:
        usage_data = read_usage_data(usage_data_file_path, deletion_of_satellites)    # Modify this parameter to change the number of deleted satellites


    # Variables (load in for each thread such that they don't interfere)
    ground_stations = satgen.read_ground_stations_extended(os.path.join(satellite_network_dir, "ground_stations.txt"))
    tles = satgen.read_tles(os.path.join(satellite_network_dir, "tles.txt"))
    satellites = tles["satellites"]
    list_isls = satgen.read_isls(os.path.join(satellite_network_dir, "isls.txt"), len(satellites))
    epoch = tles["epoch"]
    description = exputil.PropertiesConfig(os.path.join(satellite_network_dir, "description.txt"))

    # Derivatives
   
    max_gsl_length_m = exputil.parse_positive_float(description.get_property_or_fail("max_gsl_length_m"))
    max_isl_length_m = exputil.parse_positive_float(description.get_property_or_fail("max_isl_length_m"))

    num_iterations = simulation_end_time_ns / dynamic_state_update_interval_ns
    it = 1
    for t in range(0, simulation_end_time_ns, dynamic_state_update_interval_ns):
        # Given we are going to graph often, we can pre-compute the edge lengths
        graph_with_distance = construct_graph_with_distances(epoch, t, satellites, ground_stations,
                                                            list_isls, max_gsl_length_m, max_isl_length_m, usage_data)
        print(graph_with_distance)
        
        # File path for the graph
        graph_filename = os.path.join(directory, f'graph_at_{t}.pkl')
        
        # Save the graph to a file using pickle
        with open(graph_filename, 'wb') as f:
            pickle.dump(graph_with_distance, f)

        it += 1
    
# print(graph_with_distance)
# # Assuming 'graph_with_distance' is already your NetworkX graph
# G = graph_with_distance


# # Basic properties
# print("Number of nodes:", G.number_of_nodes())
# print("Number of edges:", G.number_of_edges())

# # Check if the graph is connected
# print("Is the graph connected?", nx.is_connected(G))

# # Components
# components = [c for c in nx.connected_components(G)]
# print("Number of connected components:", len(components))

# # Check the diameter of the graph's largest component (if it's connected)
# if nx.is_connected(G):
#     print("Diameter of the graph:", nx.diameter(G))
# else:
#     largest_component = max(components, key=len)
#     subgraph = G.subgraph(largest_component)
#     print("Diameter of the largest component:", nx.diameter(subgraph))

# # Degree distribution
# degrees = [G.degree(n) for n in G.nodes()]
# print("Average degree:", sum(degrees) / len(degrees))

# # Optionally, plot the degree distribution
# plt.figure()
# plt.hist(degrees, bins=20)
# plt.title("Degree Distribution")
# plt.xlabel("Degree")
# plt.ylabel("Number of Nodes")
# plt.show()


# # Drawing the graph (this can be very dense and may not look great for large graphs)
# plt.figure(figsize=(12, 12))  # Set the size of the figure
# pos = nx.spring_layout(G)  # Positions for all nodes using the Spring layout
# nx.draw(G, pos, with_labels=True, node_color='skyblue', edge_color='#FF5733', node_size=50, font_size=10)
# plt.title("Graph Visualization with Matplotlib")
# plt.savefig('./myplot.svg')  # Saves the plot as a PNG file
# plt.close()  # Closes the plotting window

