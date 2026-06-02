import os
import pickle
import networkx as nx
from config import PROJECT_DIR, legacy_starlink_graph_dir

# Load a single graph for demonstration
directory = legacy_starlink_graph_dir()
graph_path = directory / "graph_at_0.pkl"

def analyze_single_graph_usage():
    with open(graph_path, 'rb') as f:
        G = pickle.load(f)

    # Define the range of satellite and ground station nodes
    satellite_nodes = set(range(0, 1584))  # Adjust according to your ID definitions
    ground_station_nodes = set(range(1584, 1684))

    # Initialize a dictionary to keep track of satellite usage
    satellite_usage = {sat: 0 for sat in satellite_nodes}

    # Compute shortest paths between all pairs of ground stations
    for start_station in ground_station_nodes:
        for end_station in ground_station_nodes:
            if start_station != end_station:
                try:
                    # Create a modified graph that excludes all other ground stations except start and end
                    H = G.copy()
                    H.remove_nodes_from([n for n in ground_station_nodes if n not in [start_station, end_station]])

                    # Compute the shortest path
                    path = nx.shortest_path(H, source=start_station, target=end_station, weight='weight')
                
                    # Increment the usage count for each satellite node in the path
                    for node in path:
                        if node in satellite_nodes:
                            satellite_usage[node] += 1

                    # print(f"Shortest path from {start_station} to {end_station}: {path}")
                except nx.NetworkXNoPath:
                    print(f"No path exists between station {start_station} and station {end_station}.")

    # Define the file path for output
    output_file_path = PROJECT_DIR / "satellite_usage_ranking.txt"

    # Open the file and write the satellite usage counts and rankings
    with open(output_file_path, 'w') as file:
        # Write satellite usage counts
        file.write("Satellite Usage Counts:\n")
        for sat, count in sorted(satellite_usage.items(), key=lambda item: item[1], reverse=True):
            file.write(f"Satellite {sat} was used {count} times\n")

        # Write satellite rankings
        file.write("\nSatellites ranked by usage:\n")
        ranked_satellites = sorted(satellite_usage, key=satellite_usage.get, reverse=True)
        for rank, sat in enumerate(ranked_satellites, start=1):
            file.write(f"Rank {rank}: Satellite {sat} used {satellite_usage[sat]} times\n")

    print("Satellite usage counts and rankings have been written to", output_file_path)
