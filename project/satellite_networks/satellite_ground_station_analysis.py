import os
import pickle
import networkx as nx
import exputil

# Configuration dictionary
config = {
    "graph_directory": '/home/leo/hypatia/ECE227/satellite_networks/gen_data/72_22_53_550_starlinkshell1/graph/graph_72_22_53_550_starlinkshell1',
    "output_data_dir": '/home/leo/hypatia/ECE227/satellite_networks/gen_data/72_22_53_550_starlinkshell1/satellite_gs_ranking',
    "total_output_file_path": '/home/leo/hypatia/ECE227/total_satellite_gs_ranking.txt',
    "simulation_end_time_s": 200,
    "dynamic_state_update_interval_ms": 1000,
    "satellite_network_dir": "/home/leo/hypatia/paper/satellite_networks_state/gen_data/starlink_550_isls_plus_grid_ground_stations_top_100_algorithm_free_one_only_over_isls"
}

# Ensure the output directory exists
if not os.path.exists(config["output_data_dir"]):
    os.makedirs(config["output_data_dir"])

# Calculate derived parameters
simulation_end_time_ns = config["simulation_end_time_s"] * 1000 * 1000 * 1000
dynamic_state_update_interval_ns = config["dynamic_state_update_interval_ms"] * 1000 * 1000

description = exputil.PropertiesConfig(config["satellite_network_dir"] + "/description.txt")
max_gsl_length_m = exputil.parse_positive_float(description.get_property_or_fail("max_gsl_length_m"))

# Initialize a dictionary to keep track of total satellite usage
satellite_ground_station_counts = {sat: 0 for sat in range(1584)}

for t in range(0, simulation_end_time_ns, dynamic_state_update_interval_ns):
    print(f"Generating data for t={t} ns (= {t / 1e9} seconds)")
    graph_path = os.path.join(config["graph_directory"], f'graph_at_{t}.pkl')

    if not os.path.exists(graph_path):
        print(f"Graph file {graph_path} does not exist.")
        continue

    with open(graph_path, 'rb') as f:
        G = pickle.load(f)

    # Define the range of satellite and ground station nodes
    satellite_nodes = set(range(0, 1584))  # Adjust according to your ID definitions
    ground_station_nodes = set(range(1584, 1684))
    satellite_usage = {sat: 0 for sat in satellite_nodes}

    # Counting the number of connected ground stations
    for sat in satellite_nodes:
        for ground_station in ground_station_nodes:
            if G.has_edge(sat, ground_station):
                distance = G[sat][ground_station]['weight']
                if distance <= max_gsl_length_m:
                    satellite_ground_station_counts[sat] += 1
                    satellite_usage[sat] += 1

    output_file_path = os.path.join(config["output_data_dir"], f'satellite_gs_ranking_at_{t}.txt')

    # Open the file and write the satellite usage counts and rankings
    with open(output_file_path, 'w') as file:
        # Write satellite rankings
        file.write("Satellites ranked by gs:\n")
        ranked_satellites = sorted(satellite_usage, key=satellite_usage.get, reverse=True)
        for rank, sat in enumerate(ranked_satellites, start=1):
            file.write(f"Rank {rank}: Satellite {sat} connects {satellite_usage[sat]} ground stations\n")

    print("Satellite gs counts and rankings have been written to", output_file_path)

# Write total satellite usage counts and rankings
with open(config["total_output_file_path"], 'w') as file:
    file.write("Satellites ranked by gs:\n")
    ranked_satellites = sorted(satellite_ground_station_counts, key=satellite_ground_station_counts.get, reverse=True)
    for rank, sat in enumerate(ranked_satellites, start=1):
        file.write(f"Rank {rank}: Satellite {sat} connects {satellite_ground_station_counts[sat]} ground stations\n")

print("Total satellite usage counts and rankings have been written to", config["total_output_file_path"])