import os
import pickle
import networkx as nx

# Configuration dictionary
config = {
    "graph_directory": "/home/leo/hypatia/ECE227/satellite_networks/gen_data/kuiper_590_isls_plus_grid_ground_stations_top_100_algorithm_free_one_only_over_isls/graph/graph_28_28_33_590_kuipershell3",
    "simulation_end_time_s": 200,
    "dynamic_state_update_interval_ms": 1000,
    "output_data_dir": "/home/leo/hypatia/ECE227/satgen_analysis/kuiper_590_isls_plus_grid_ground_stations_top_100_algorithm_free_one_only_over_isls/1000ms_for_200s/usage/satellite_usage_ranking",
    "satellite_count": 784,
    "ground_station_count": 100
}

# Derived parameters
simulation_end_time_ns = config["simulation_end_time_s"] * 1000 * 1000 * 1000
dynamic_state_update_interval_ns = config["dynamic_state_update_interval_ms"] * 1000 * 1000

# Initialize a dictionary to keep track of total satellite usage
total_satellite_usage = {sat: 0 for sat in range(config["satellite_count"])}

# Ensure the output directory exists
if not os.path.exists(config["output_data_dir"]):
    os.makedirs(config["output_data_dir"])

for t in range(0, simulation_end_time_ns, dynamic_state_update_interval_ns):
    print(f"Generating data for t={t} ns (= {t / 1e9} seconds)")
    output_file_path = os.path.join(config["output_data_dir"], f'satellite_usage_ranking_at_{t}.txt')
    graph_path = os.path.join(config["graph_directory"], f'graph_at_{t}.pkl')

    if not os.path.exists(graph_path):
        print(f"Graph file {graph_path} does not exist.")
        continue

    with open(graph_path, 'rb') as f:
        G = pickle.load(f)

    # Define the range of satellite and ground station nodes
    satellite_nodes = set(range(0, config["satellite_count"]))
    ground_station_nodes = set(range(config["satellite_count"], config["satellite_count"] + config["ground_station_count"]))

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
                            total_satellite_usage[node] += 1
                except nx.NetworkXNoPath:
                    print(f"No path exists between station {start_station} and station {end_station}.")

    # Open the file and write the satellite usage counts and rankings
    with open(output_file_path, 'w') as file:
        # Write satellite rankings
        file.write("Satellites ranked by usage:\n")
        ranked_satellites = sorted(satellite_usage, key=satellite_usage.get, reverse=True)
        for rank, sat in enumerate(ranked_satellites, start=1):
            file.write(f"Rank {rank}: Satellite {sat} used {satellite_usage[sat]} times\n")

    print("Satellite usage counts and rankings have been written to", output_file_path)

# Write total satellite usage counts and rankings
total_output_file_path = os.path.join(config["output_data_dir"], 'total_satellite_usage_ranking.txt')
with open(total_output_file_path, 'w') as file:
    file.write("Satellites ranked by usage:\n")
    ranked_satellites = sorted(total_satellite_usage, key=total_satellite_usage.get, reverse=True)
    for rank, sat in enumerate(ranked_satellites, start=1):
        file.write(f"Rank {rank}: Satellite {sat} used {total_satellite_usage[sat]} times\n")

print("Total satellite usage counts and rankings have been written to", total_output_file_path)
