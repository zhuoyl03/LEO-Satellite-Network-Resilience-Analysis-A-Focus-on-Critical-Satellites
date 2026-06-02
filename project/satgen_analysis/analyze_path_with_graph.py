import sys
import os
from pathlib import Path
PROJECT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_DIR))
from config import DEFAULT_SATELLITE_DATA_NAME, PROJECT_ANALYSIS_DIR, PROJECT_NETWORKS_DIR, SATGENPY_DIR, paper_network_dir
sys.path.append(str(SATGENPY_DIR))
import satgen
import exputil
import numpy as np
from statsmodels.distributions.empirical_distribution import ECDF
import matplotlib.pyplot as plt
import pickle
import networkx as nx

# Configuration dictionary
DEFAULT_CONFIG = {
    'simulation_end_time_s': 200,
    'dynamic_state_update_interval_ms': 1000,
    'satellite_network_dir': str(paper_network_dir(DEFAULT_SATELLITE_DATA_NAME)),
    'satgenpy_dir_with_ending_slash': str(SATGENPY_DIR) + os.sep,
    'paths_file': str(PROJECT_NETWORKS_DIR / DEFAULT_SATELLITE_DATA_NAME / "path" / "delete_0" / "all_paths.pkl"),
    'output_data_dir': str(PROJECT_ANALYSIS_DIR),
    'graph_template_path': str(PROJECT_NETWORKS_DIR / DEFAULT_SATELLITE_DATA_NAME / "graph" / "delete_0" / "graph_at_{}.pkl")
}

def analyze_path_with_graph(config=None):
    config = dict(DEFAULT_CONFIG if config is None else config)
    config['simulation_end_time_ns'] = config['simulation_end_time_s'] * 1000 * 1000 * 1000
    config['dynamic_state_update_interval_ns'] = config['dynamic_state_update_interval_ms'] * 1000 * 1000

    # Create output directory if it does not exist
    if not os.path.exists(config['output_data_dir']):
        os.makedirs(config['output_data_dir'])

    # Read ground stations and TLEs
    ground_stations = satgen.read_ground_stations_extended(config['satellite_network_dir'] + "/ground_stations.txt")
    tles = satgen.read_tles(config['satellite_network_dir'] + "/tles.txt")
    satellites = tles["satellites"]
    ground_station_nodes = set(range(len(satellites), len(satellites) + len(ground_stations)))

    # Local shell
    local_shell = exputil.LocalShell()
    core_network_folder_name = config['satellite_network_dir'].split("/")[-1]
    base_output_dir = "{}/{}/{}ms_for_{}s/path/path".format(
        config['output_data_dir'], core_network_folder_name, config['dynamic_state_update_interval_ms'], config['simulation_end_time_s']
    )
    pdf_dir = base_output_dir + "/pdf"
    data_dir = base_output_dir + "/data"
    local_shell.remove_force_recursive(pdf_dir)
    local_shell.remove_force_recursive(data_dir)
    local_shell.make_full_dir(pdf_dir)
    local_shell.make_full_dir(data_dir)

    # Analysis
    path_list_per_pair = []
    for i in range(len(ground_stations)):
        temp_list = []
        for j in range(len(ground_stations)):
            temp_list.append([])
        path_list_per_pair.append(temp_list)

    # Time step analysis
    time_step_num_path_changes = []
    time_step_num_fstate_updates = []

    # For each time moment
    fstate = {}
    num_iterations = config['simulation_end_time_ns'] / config['dynamic_state_update_interval_ns']
    it = 1

    # Load all paths
    with open(config["paths_file"], 'rb') as f:
        paths = pickle.load(f)

    for t in range(0, config['simulation_end_time_ns'], config['dynamic_state_update_interval_ns']):
        num_path_changes = 0
        num_fstate_updates = 0
        graph_path = config['graph_template_path'].format(t)

        if not os.path.exists(graph_path):
            print(f"Graph file {graph_path} does not exist.")
            continue

        # Load the graph from the pickle file
        with open(graph_path, 'rb') as f:
            graph_with_distance = pickle.load(f)

        paths_at_t = paths[t]

        # Go over each pair of ground stations and calculate the length
        for src in range(len(ground_stations)):
            for dst in range(src + 1, len(ground_stations)):
                src_node_id = len(satellites) + src
                dst_node_id = len(satellites) + dst
                path = paths_at_t.get((src, dst))
                if not path:
                    if len(path_list_per_pair[src][dst]) == 0 or path_list_per_pair[src][dst][-1] != []:
                        path_list_per_pair[src][dst].append([])
                        num_path_changes += 1
                else:
                    if len(path_list_per_pair[src][dst]) == 0 or path != path_list_per_pair[src][dst][-1]:
                        path_list_per_pair[src][dst].append(path)
                        num_path_changes += 1

        # First iteration has an update for all, which is not interesting
        # to show in the ECDF and is not really a "change" / "update"
        if it != 1:
            time_step_num_path_changes.append(num_path_changes)
            time_step_num_fstate_updates.append(num_fstate_updates)

        # Show progress a bit
        print("{}/{}".format(it, int(num_iterations)))
        it += 1
    print("")

    # Calculate hop count list
    hop_count_list_per_pair = []
    for src in range(len(ground_stations)):
        temp_list = []
        for dst in range(len(ground_stations)):  # The one until src are empty, but those are ignored later
            r = []
            for x in path_list_per_pair[src][dst]:
                if len(x) != 0:
                    if len(x) < 2:
                        raise ValueError("Path must have 0 or at least 2 nodes")
                    r.append(len(x) - 1)  # Number of nodes - 1 is the hop count
            temp_list.append(r)
        hop_count_list_per_pair.append(temp_list)

    #################################################

    # ECDF stuff, which is quick, so we do that first

    # Find all the lists
    list_max_minus_min_hop_count = []
    list_max_hop_count_to_min_hop_count = []
    list_num_path_changes = []
    for src in range(len(ground_stations)):
        for dst in range(src + 1, len(ground_stations)):
            if hop_count_list_per_pair[src][dst]:  # Check if list is not empty
                min_hop_count = np.min(hop_count_list_per_pair[src][dst])
                max_hop_count = np.max(hop_count_list_per_pair[src][dst])
                list_max_hop_count_to_min_hop_count.append(float(max_hop_count) / float(min_hop_count))
                list_max_minus_min_hop_count.append(max_hop_count - min_hop_count)
                list_num_path_changes.append(len(path_list_per_pair[src][dst]) - 1)  # First path is not a change, so - 1

    # Write and plot ECDFs
    for element in [
        ("ecdf_pairs_max_minus_min_hop_count", ECDF(list_max_minus_min_hop_count)),
        ("ecdf_pairs_max_hop_count_to_min_hop_count", ECDF(list_max_hop_count_to_min_hop_count)),
        ("ecdf_pairs_num_path_changes", ECDF(list_num_path_changes)),
        ("ecdf_time_step_num_path_changes", ECDF(time_step_num_path_changes)),
        ("ecdf_time_step_num_fstate_updates", ECDF(time_step_num_fstate_updates)),
    ]:
        name = element[0]
        ecdf = element[1]
        with open(data_dir + "/" + name + ".txt", "w+") as f_out:
            for i in range(len(ecdf.x)):
                f_out.write(str(ecdf.x[i]) + "," + str(ecdf.y[i]) + "\n")

    #################################################

    #################################################

    # Largest hop count delta
    with open(data_dir + "/top_10_largest_hop_count_delta.txt", "w+") as f_out:
        largest_hop_count_delta_list = []
        for src in range(len(ground_stations)):
            for dst in range(src + 1, len(ground_stations)):
                if hop_count_list_per_pair[src][dst]:  # Check if list is not empty
                    min_hop_count = np.min(hop_count_list_per_pair[src][dst])
                    max_hop_count = np.max(hop_count_list_per_pair[src][dst])
                    largest_hop_count_delta_list.append((max_hop_count - min_hop_count, min_hop_count, max_hop_count,
                                                            src, dst))
        largest_hop_count_delta_list = sorted(largest_hop_count_delta_list, reverse=True)
        f_out.write("LARGEST HOP-COUNT DELTA TOP-10 WITHOUT DUPLICATE NODES (EXCL. UNREACHABLE)\n")
        f_out.write("------------------------------------------------------------------\n")
        f_out.write("#      Pair              Delta         Min. hop count    Max. hop count\n")
        already_plotted_nodes = set()
        num_plotted = 0
        for i in range(len(largest_hop_count_delta_list)):
            if largest_hop_count_delta_list[i][3] not in already_plotted_nodes \
                    and largest_hop_count_delta_list[i][4] not in already_plotted_nodes:
                f_out.write("%-3d    %-4d -> %4d       %8d     %-8d          %-8d\n" % (
                    i + 1,
                    len(satellites) + largest_hop_count_delta_list[i][3],
                    len(satellites) + largest_hop_count_delta_list[i][4],
                    largest_hop_count_delta_list[i][0],
                    largest_hop_count_delta_list[i][1],
                    largest_hop_count_delta_list[i][2],
                ))
                satgen.print_routes_and_rtt(base_output_dir, config['satellite_network_dir'], config['dynamic_state_update_interval_ms'],
                                        config['simulation_end_time_s'], len(satellites) + largest_hop_count_delta_list[i][3],
                                        len(satellites) + largest_hop_count_delta_list[i][4],
                                        config['satgenpy_dir_with_ending_slash'])
                already_plotted_nodes.add(largest_hop_count_delta_list[i][3])
                already_plotted_nodes.add(largest_hop_count_delta_list[i][4])
                num_plotted += 1
                if num_plotted >= 10:
                    break
        f_out.write("---------------------------------------------------------------\n")
        f_out.write("\n")

    # Number of path changes
    with open(data_dir + "/top_10_most_path_changes.txt", "w+") as f_out:
        most_path_changes_list = []
        for src in range(len(ground_stations)):
            for dst in range(src + 1, len(ground_stations)):
                most_path_changes_list.append((len(path_list_per_pair[src][dst]) - 1, src, dst))
        most_path_changes_list = sorted(most_path_changes_list, reverse=True)
        f_out.write("MOST PATH CHANGES TOP-10 WITHOUT DUPLICATE NODES\n")
        f_out.write("-------------------------------------\n")
        f_out.write("#      Pair           Number of path changes\n")
        already_plotted_nodes = set()
        num_plotted = 0
        for i in range(len(most_path_changes_list)):
            if most_path_changes_list[i][1] not in already_plotted_nodes \
                    and most_path_changes_list[i][2] not in already_plotted_nodes:
                f_out.write("%-3d    %-4d -> %4d   %d\n" % (
                    i + 1,
                    len(satellites) + most_path_changes_list[i][1],
                    len(satellites) + most_path_changes_list[i][2],
                    most_path_changes_list[i][0]
                ))
                satgen.print_routes_and_rtt(base_output_dir, config['satellite_network_dir'],
                                        config['dynamic_state_update_interval_ms'], config['simulation_end_time_s'],
                                        len(satellites) + most_path_changes_list[i][1],
                                        len(satellites) + most_path_changes_list[i][2],
                                        config['satgenpy_dir_with_ending_slash'])
                already_plotted_nodes.add(most_path_changes_list[i][1])
                already_plotted_nodes.add(most_path_changes_list[i][2])
                num_plotted += 1
                if num_plotted >= 10:
                    break
        f_out.write("---------------------------------------\n")
        f_out.write("\n")

    print("Done")
