import sys
import os
from pathlib import Path
PROJECT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_DIR))
from config import SATGENPY_DIR
sys.path.append(str(SATGENPY_DIR))
import satgen
import exputil
import numpy as np
from statsmodels.distributions.empirical_distribution import ECDF
import matplotlib.pyplot as plt
import pickle
import networkx as nx
import csv


speed_of_light_m_per_s = 299792458.0

# Function to save a list to a CSV file
def save_list_to_csv(filename, data):
    with open(filename, 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['Value'])
        for value in data:
            writer.writerow([value])

def analyze_rtt_with_graph(simulation_end_time_ns, dynamic_state_update_interval_ns, satellite_network_dir, satgenpy_dir_with_ending_slash, output_data_dir, output_name, paths_file, graph_directory, geodesic_ecdf_plot_cutoff_km):
    satellite_network_dir = str(satellite_network_dir)
    output_data_dir = str(output_data_dir)
    paths_file = str(paths_file)
    graph_directory = str(graph_directory)
        
    # Ensure the output directory exists
    if not os.path.exists(output_data_dir):
        os.makedirs(output_data_dir)

    # Local shell
    local_shell = exputil.LocalShell()
    core_network_folder_name = satellite_network_dir.split("/")[-1]
    base_output_dir = "%s/%s/%dms_for_%ds/%s" % (
        output_data_dir, core_network_folder_name, dynamic_state_update_interval_ns // 1e6, simulation_end_time_ns // 1e9, output_name
    )
    pdf_dir = base_output_dir + "/pdf"
    data_dir = base_output_dir + "/data"
    plot_dir = base_output_dir + "/hplot"
    local_shell.remove_force_recursive(pdf_dir)
    local_shell.remove_force_recursive(data_dir)
    local_shell.remove_force_recursive(plot_dir)
    local_shell.make_full_dir(pdf_dir)
    local_shell.make_full_dir(data_dir)
    local_shell.make_full_dir(plot_dir)
    # Variables (load in for each thread such that they don't interfere)
    ground_stations = satgen.read_ground_stations_extended(satellite_network_dir + "/ground_stations.txt")
    tles = satgen.read_tles(satellite_network_dir + "/tles.txt")
    satellites = tles["satellites"]
    epoch = tles["epoch"]
    description = exputil.PropertiesConfig(satellite_network_dir + "/description.txt")

    # Derivatives
    max_gsl_length_m = exputil.parse_positive_float(description.get_property_or_fail("max_gsl_length_m"))
    max_isl_length_m = exputil.parse_positive_float(description.get_property_or_fail("max_isl_length_m"))

    # Analysis
    rtt_list_per_pair = []
    unreachable_200ms_per_pair = np.zeros((len(ground_stations), len(ground_stations)), dtype=bool)  # Track if pair is unreachable for all 200ms
    for i in range(len(ground_stations)):
        temp_list = []
        for j in range(len(ground_stations)):
            temp_list.append([])
        rtt_list_per_pair.append(temp_list)
    unreachable_per_pair = np.zeros((len(ground_stations), len(ground_stations)))
    unreachable_200ms_count = 0
    unreachable_per_second = []
    ground_station_nodes = set(range(len(satellites), len(satellites) + len(ground_stations)))

    # Load all paths
    with open(paths_file, 'rb') as f:
        paths = pickle.load(f)

    it = 1
    current_unreachable_count = 0
    for t in range(0, simulation_end_time_ns, dynamic_state_update_interval_ns):
        graph_path = os.path.join(graph_directory, f'graph_at_{t}.pkl')

        if not os.path.exists(graph_path):
            print(f"Graph file {graph_path} does not exist.")
            continue

        # Load the graph from the pickle file
        with open(graph_path, 'rb') as f:
            graph_with_distance = pickle.load(f)

        # Ensure the loaded object is a NetworkX graph
        if not isinstance(graph_with_distance, nx.Graph):
            raise TypeError(f"Loaded object from {graph_path} is not a NetworkX graph.")

        # Use the precomputed paths
        paths_at_t = paths[t]
        for src in range(len(ground_stations)):
            for dst in range(src + 1, len(ground_stations)):
                src_node_id = len(satellites) + src
                dst_node_id = len(satellites) + dst
                path = paths_at_t.get((src, dst))
                if path:
                    length_path_m = satgen.compute_path_length_with_graph(path, graph_with_distance)
                    rtt = (2 * length_path_m) * 1e9 / speed_of_light_m_per_s
                    rtt_list_per_pair[src][dst].append(rtt)
                    if rtt >= 200 * 1e6:
                        current_unreachable_count += 1
                else:
                    unreachable_per_pair[src, dst] += 1
                    current_unreachable_count += 1
                    unreachable_200ms_per_pair[src, dst] = True

        # At the end of each second, record the number of unreachable pairs
        if (t + dynamic_state_update_interval_ns) % (1 * 1e9) == 0:
            unreachable_per_second.append(current_unreachable_count)
            current_unreachable_count = 0

        # Show progress a bit
        print(f"{it} / {simulation_end_time_ns // dynamic_state_update_interval_ns}")
        it += 1
    print("")

    # Calculate the number of pairs unreachable for the entire 200ms simulation period
    for src in range(len(ground_stations)):
        for dst in range(src + 1, len(ground_stations)):
            if unreachable_200ms_per_pair[src, dst] and unreachable_per_pair[src, dst] == (simulation_end_time_ns // dynamic_state_update_interval_ns):
                unreachable_200ms_count += 1

    # ECDF stuff, which is quick, so we do that first

    # Find all the lists
    list_min_rtt_ns = []
    list_max_rtt_ns = []
    list_max_minus_min_rtt_ns = []
    list_max_rtt_to_min_rtt_slowdown = []
    list_max_rtt_to_geodesic_slowdown = []
    for src in range(len(ground_stations)):
        for dst in range(src + 1, len(ground_stations)):
            if rtt_list_per_pair[src][dst]:  # Check if list is not empty
                min_rtt_ns = np.min(rtt_list_per_pair[src][dst])
                max_rtt_ns = np.max(rtt_list_per_pair[src][dst])
                max_rtt_slowdown = float(max_rtt_ns) / float(min_rtt_ns)
                list_min_rtt_ns.append(min_rtt_ns)
                list_max_rtt_ns.append(max_rtt_ns)
                list_max_minus_min_rtt_ns.append(max_rtt_ns - min_rtt_ns)
                list_max_rtt_to_min_rtt_slowdown.append(max_rtt_slowdown)
                geodesic_distance_m = satgen.geodesic_distance_m_between_ground_stations(
                    ground_stations[src],
                    ground_stations[dst]
                )
                # If the geodesic is under 500km, we do not consider it,
                # as one would use terrestrial networks vs. expending the effort to go up and down
                # Especially if populated cities are very close to each other, would this give a large geodesic slow-down
                if geodesic_distance_m >= geodesic_ecdf_plot_cutoff_km * 1000:
                    geodesic_rtt_ns = geodesic_distance_m * 2 * 1e9 / speed_of_light_m_per_s
                    list_max_rtt_to_geodesic_slowdown.append(float(max_rtt_ns) / float(geodesic_rtt_ns))

    # Write and plot ECDFs
    for element in [
        ("ecdf_pairs_min_rtt_ns", list_min_rtt_ns),
        ("ecdf_pairs_max_rtt_ns", list_max_rtt_ns),
        ("ecdf_pairs_max_minus_min_rtt_ns", list_max_minus_min_rtt_ns),
        ("ecdf_pairs_max_rtt_to_min_rtt_slowdown", list_max_rtt_to_min_rtt_slowdown),
        ("ecdf_pairs_max_rtt_to_geodesic_slowdown", list_max_rtt_to_geodesic_slowdown),
    ]:
        name = element[0]
        ecdf = ECDF(element[1])
        
        txt_file_path = os.path.join(data_dir, f"{name}.txt")
        with open(txt_file_path, "w+") as f_out:
            for i in range(len(ecdf.x)):
                f_out.write(f"{ecdf.x[i]},{ecdf.y[i]}\n")
        
        # Plotting the ECDF
        plt.figure()
        plt.step(ecdf.x, ecdf.y, where='post')
        plt.xlabel(name)
        plt.ylabel('ECDF')
        plt.title(f'ECDF of {name}')
        pdf_file_path = os.path.join(pdf_dir, f"{name}.pdf")
        plt.savefig(pdf_file_path)
        plt.close()
    lists_to_save = [
        ("ecdf_pairs_min_rtt_ns.csv", list_min_rtt_ns),
        ("ecdf_pairs_max_rtt_ns.csv", list_max_rtt_ns),
        ("ecdf_pairs_max_minus_min_rtt_ns.csv", list_max_minus_min_rtt_ns),
        ("ecdf_pairs_max_rtt_to_min_rtt_slowdown.csv", list_max_rtt_to_min_rtt_slowdown),
        ("ecdf_pairs_max_rtt_to_geodesic_slowdown.csv", list_max_rtt_to_geodesic_slowdown),
    ]

    for filename, data in lists_to_save:
        save_list_to_csv(os.path.join(plot_dir, filename), data)

    for element in [
        ("Minimum RTT (ns)", list_min_rtt_ns),
        ("Maximum RTT (ns)", list_max_rtt_ns),
        ("Max - Min RTT (ns)", list_max_minus_min_rtt_ns),
        ("Max RTT to Min RTT Slowdown", list_max_rtt_to_min_rtt_slowdown),
        ("Max RTT to Geodesic Slowdown", list_max_rtt_to_geodesic_slowdown),
    ]:
        data = element[1]
        name = element[0]
        # Plotting the Histogram
        plt.figure()
        counts, bin_edges = np.histogram(data, bins=50)
        plt.hist(data, bins=50, edgecolor='k', alpha=0.7)
        plt.xlabel(name)
        plt.ylabel('Frequency')
        plt.title(f'Histogram of {name}')
        histogram_pdf_file_path = os.path.join(pdf_dir, f"{name}_histogram.pdf")
        plt.savefig(histogram_pdf_file_path)
        plt.close()
    #################################################

    # Largest RTT delta
    with open(data_dir + "/top_10_largest_rtt_delta.txt", "w+") as f_out:
        largest_rtt_delta_list = []
        for src in range(len(ground_stations)):
            for dst in range(src + 1, len(ground_stations)):
                if rtt_list_per_pair[src][dst]:  # Check if list is not empty
                    min_rtt_ns = np.min(rtt_list_per_pair[src][dst])
                    max_rtt_ns = np.max(rtt_list_per_pair[src][dst])
                    largest_rtt_delta_list.append((max_rtt_ns - min_rtt_ns, min_rtt_ns, max_rtt_ns, src, dst))
        largest_rtt_delta_list = sorted(largest_rtt_delta_list, reverse=True)
        f_out.write("LARGEST RTT DELTA TOP-10 WITHOUT DUPLICATE NODES\n")
        f_out.write("---------------------------------------------------------------\n")
        f_out.write("#      Pair           Delta (ms)   Min. RTT (ms)   Max. RTT (ms)\n")
        already_plotted_nodes = set()
        num_plotted = 0
        for i in range(len(largest_rtt_delta_list)):
            if largest_rtt_delta_list[i][3] not in already_plotted_nodes \
                    and largest_rtt_delta_list[i][4] not in already_plotted_nodes:
                f_out.write("%-3d    %-4d -> %4d   %-8.2f     %-8.2f        %-8.2f\n" % (
                    i + 1,
                    len(satellites) + largest_rtt_delta_list[i][3],
                    len(satellites) + largest_rtt_delta_list[i][4],
                    largest_rtt_delta_list[i][0] / 1e6,
                    largest_rtt_delta_list[i][1] / 1e6,
                    largest_rtt_delta_list[i][2] / 1e6,
                ))
                satgen.print_routes_and_rtt(base_output_dir, satellite_network_dir, dynamic_state_update_interval_ns // 1e6,
                                        simulation_end_time_ns // 1e9, len(satellites) + largest_rtt_delta_list[i][3],
                                        len(satellites) + largest_rtt_delta_list[i][4], satgenpy_dir_with_ending_slash)
                already_plotted_nodes.add(largest_rtt_delta_list[i][3])
                already_plotted_nodes.add(largest_rtt_delta_list[i][4])
                num_plotted += 1
                if num_plotted >= 10:
                    break
        f_out.write("---------------------------------------------------------------\n")
        f_out.write("\n")

    # Most unreachable
    with open(data_dir + "/top_10_most_unreachable.txt", "w+") as f_out:
        most_unreachable_list = []
        for src in range(len(ground_stations)):
            for dst in range(src + 1, len(ground_stations)):
                most_unreachable_list.append((unreachable_per_pair[(src, dst)], src, dst))
        most_unreachable_list = sorted(most_unreachable_list, reverse=True)
        f_out.write("MOST UNREACHABLE DELTA TOP-10 WITHOUT DUPLICATE NODES\n")
        f_out.write("---------------------------------------\n")
        f_out.write("#      Pair           Times unreachable\n")
        already_plotted_nodes = set()
        num_plotted = 0
        for i in range(len(most_unreachable_list)):
            if most_unreachable_list[i][1] not in already_plotted_nodes \
                    and most_unreachable_list[i][2] not in already_plotted_nodes:
                f_out.write("%-3d    %-4d -> %4d   %d\n" % (
                    i + 1,
                    len(satellites) + most_unreachable_list[i][1],
                    len(satellites) + most_unreachable_list[i][2],
                    most_unreachable_list[i][0]
                ))
                satgen.print_routes_and_rtt(base_output_dir, satellite_network_dir, dynamic_state_update_interval_ns // 1e6,
                                        simulation_end_time_ns // 1e9, len(satellites) + most_unreachable_list[i][1],
                                        len(satellites) + most_unreachable_list[i][2], satgenpy_dir_with_ending_slash)
                already_plotted_nodes.add(most_unreachable_list[i][1])
                already_plotted_nodes.add(most_unreachable_list[i][2])
                num_plotted += 1
                if num_plotted >= 10:
                    break
        f_out.write("---------------------------------------\n")
        f_out.write("\n")

    def ecdf(data):
        x = np.sort(data)
        y = np.arange(1, len(data) + 1) / len(data)
        return x, y
    unreachable_counts = []
    for src in range(len(ground_stations)):
        for dst in range(src + 1, len(ground_stations)):
            count = unreachable_per_pair[(src, dst)]
            if count != 0:
                unreachable_counts.append(count)
                
    x, y = ecdf(unreachable_counts)
    plt.figure(figsize=(10, 6))
    plt.plot(x, y, marker='.', linestyle='none')
    plt.xlabel('Times unreachable')
    plt.ylabel('ECDF')
    plt.title('ECDF of Unreachable Times in 200 seconds')
    plt.grid(True)
    plt.savefig(data_dir + '/ecdf_unreachable_times.png')  
    plt.close()
    print("Done")
