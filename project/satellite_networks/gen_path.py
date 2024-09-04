import sys
import os
import pickle
import networkx as nx
import numpy as np
sys.path.append(os.path.expanduser("~") + "/hypatia/satgenpy")
import satgen
import exputil

def gen_path(graph_directory, simulation_end_time_ns, dynamic_state_update_interval_ns, output_data_dir, satellite_count, ground_station_count, satellite_network_dir, output_path_dir):

    # Ensure the output directories exist
    if not os.path.exists(output_path_dir):
        os.makedirs(output_path_dir)

    if not os.path.exists(output_data_dir):
        os.makedirs(output_data_dir)

    # Load initial data
    ground_stations = satgen.read_ground_stations_extended(os.path.join(satellite_network_dir, "ground_stations.txt"))
    tles = satgen.read_tles(os.path.join(satellite_network_dir, "tles.txt"))
    satellites = tles["satellites"]
    list_isls = satgen.read_isls(os.path.join(satellite_network_dir, "isls.txt"), len(satellites))
    epoch = tles['epoch']
    description = exputil.PropertiesConfig(os.path.join(satellite_network_dir, "description.txt"))

    max_gsl_length_m = exputil.parse_positive_float(description.get_property_or_fail("max_gsl_length_m"))
    max_isl_length_m = exputil.parse_positive_float(description.get_property_or_fail("max_isl_length_m"))

    satellite_nodes = set(range(satellite_count))
    ground_station_nodes = set(range(satellite_count, satellite_count + ground_station_count))

    # Initialize variables
    paths = {}
    total_satellite_usage = {sat: 0 for sat in satellite_nodes}
    it = 1

    # Main processing loop
    for t in range(0, simulation_end_time_ns, dynamic_state_update_interval_ns):
        satellite_usage = {sat: 0 for sat in satellite_nodes}
        graph_path = os.path.join(graph_directory, f'graph_at_{t}.pkl')

        if not os.path.exists(graph_path):
            print(f"Graph file {graph_path} does not exist.")
            continue

        # Load the graph from the pickle file
        with open(graph_path, 'rb') as f:
            graph_with_distance = pickle.load(f)

        if not isinstance(graph_with_distance, nx.Graph):
            raise TypeError(f"Loaded object from {graph_path} is not a NetworkX graph.")

        paths_at_t = {}
        for src in range(len(ground_stations)):
            for dst in range(src + 1, len(ground_stations)):
                src_node_id = len(satellites) + src
                dst_node_id = len(satellites) + dst
                try:
                    H = graph_with_distance.copy()
                    H.remove_nodes_from([n for n in ground_station_nodes if n not in [src_node_id, dst_node_id]])

                    path = nx.shortest_path(H, source=src_node_id, target=dst_node_id, weight='weight')
                    paths_at_t[(src, dst)] = path
                    for node in path:
                        if node in satellite_nodes:
                            satellite_usage[node] += 1
                            total_satellite_usage[node] += 1

                except nx.NetworkXNoPath:
                    paths_at_t[(src, dst)] = None

        paths[t] = paths_at_t

        # Write satellite usage rankings to file
        output_file_path = os.path.join(output_data_dir, f'satellite_usage_ranking_at_{t}.txt')
        with open(output_file_path, 'w') as file:
            file.write("Satellites ranked by usage:\n")
            ranked_satellites = sorted(satellite_usage, key=satellite_usage.get, reverse=True)
            for rank, sat in enumerate(ranked_satellites, start=1):
                file.write(f"Rank {rank}: Satellite {sat} used {satellite_usage[sat]} times\n")
        print("Satellite usage counts and rankings have been written to", output_file_path)

        # Show progress
        print(f"{it} / {simulation_end_time_ns // dynamic_state_update_interval_ns}")
        it += 1

    # Save all paths
    with open(os.path.join(output_path_dir, 'all_paths.pkl'), 'wb') as f:
        pickle.dump(paths, f)
    print("Paths saved.")

    # Write total satellite usage counts and rankings
    total_output_file_path = os.path.join(output_data_dir, 'total_satellite_usage_ranking.txt')
    with open(total_output_file_path, 'w') as file:
        file.write("Satellites ranked by usage:\n")
        ranked_satellites = sorted(total_satellite_usage, key=total_satellite_usage.get, reverse=True)
        for rank, sat in enumerate(ranked_satellites, start=1):
            file.write(f"Rank {rank}: Satellite {sat} used {total_satellite_usage[sat]} times\n")
    print("Total satellite usage counts and rankings have been written to", total_output_file_path)