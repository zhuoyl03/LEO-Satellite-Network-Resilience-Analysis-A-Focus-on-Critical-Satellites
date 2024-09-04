import sys
sys.path.append(os.path.expanduser("~") + "/hypatia/satgenpy")
import os
import pickle
import matplotlib.pyplot as plt
import networkx as nx
import satgen
import exputil
from astropy import units as u
import random

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

def construct_graph_random_delete(directory, usage_data_file_path, satellite_network_dir, deletion_of_satellites, simulation_end_time_ns, dynamic_state_update_interval_ns):
    # Ensure the directory exists
    if not os.path.exists(directory):
        os.makedirs(directory)

    if not os.path.exists(usage_data_file_path):
        print("usage_data_file_path error")
        usage_data = []
    else:
        usage_data = read_usage_data(usage_data_file_path, deletion_of_satellites)

    # Variables (load in for each thread such that they don't interfere)
    ground_stations = satgen.read_ground_stations_extended(os.path.join(satellite_network_dir, "ground_stations.txt"))
    tles = satgen.read_tles(os.path.join(satellite_network_dir, "tles.txt"))
    satellites = tles["satellites"]
    list_isls = satgen.read_isls(os.path.join(satellite_network_dir, "isls.txt"), len(satellites))
    epoch = tles["epoch"]
    description = exputil.PropertiesConfig(os.path.join(satellite_network_dir, "description.txt"))

    max_gsl_length_m = exputil.parse_positive_float(description.get_property_or_fail("max_gsl_length_m"))
    max_isl_length_m = exputil.parse_positive_float(description.get_property_or_fail("max_isl_length_m"))

    num_iterations = simulation_end_time_ns / dynamic_state_update_interval_ns
    it = 1
    for t in range(0, simulation_end_time_ns, dynamic_state_update_interval_ns):
        # Randomly select satellites to delete
        deleted_satellites = random.sample(range(len(satellites)), deletion_of_satellites)

        # Construct the graph with pre-computed edge lengths
        graph_with_distance = construct_graph_with_distances(epoch, t, satellites, ground_stations,
                                                             list_isls, max_gsl_length_m, max_isl_length_m, deleted_satellites)
        print(graph_with_distance)

        # File path for the graph
        graph_filename = os.path.join(directory, f'graph_at_{t}.pkl')

        # Save the graph to a file using pickle
        with open(graph_filename, 'wb') as f:
            pickle.dump(graph_with_distance, f)

        it += 1

