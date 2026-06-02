import os
import pickle
import networkx as nx
from config import legacy_starlink_graph_dir

# Directory where graphs are stored
directory = legacy_starlink_graph_dir()

def load_and_print_paths():
    # List all pickle files in the directory
    graph_files = [f for f in os.listdir(directory) if f.endswith('.pkl')]

    # Load each graph
    graphs = []
    for filename in graph_files:
        filepath = os.path.join(directory, filename)
        with open(filepath, 'rb') as f:
            graph = pickle.load(f)
            graphs.append(graph)
        
    # Ground stations you are interested in
    start_station = 1682
    end_station = 1612

    # Define your ground stations and satellites
    satellite_nodes = list(range(0, 1583))  # Satellite nodes IDs
    ground_station_nodes = list(range(1583, 1684))  # Ground station node IDs

    for i in range(len(graphs)):

        G = graphs[i]

        # Create a modified graph that excludes all ground stations except start and end
        H = G.copy()
        H.remove_nodes_from([n for n in ground_station_nodes if n not in [start_station, end_station]])


        # Compute the shortest path
        try:
            path = nx.shortest_path(H, source=start_station, target=end_station, weight='weight')  # Use weight='weight' if your graph is weighted
            print("Shortest path from A to E:", path)
        except nx.NetworkXNoPath:
            print("No path exists between the chosen nodes.")
