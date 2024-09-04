from .graph_tools import *
from satgen.distance_tools import *
from satgen.isls import *
from satgen.ground_stations import *
from satgen.tles import *
import exputil
import numpy as np
from .print_routes_and_rtt import print_routes_and_rtt
from statsmodels.distributions.empirical_distribution import ECDF


SPEED_OF_LIGHT_M_PER_S = 299792458.0

GEODESIC_ECDF_PLOT_CUTOFF_KM = 500

def save_graph_as_csv(graph, nodes_file_path, edges_file_path):
    
    with open(nodes_file_path, 'w', newline='') as nodes_file:
        writer = csv.writer(nodes_file)
        writer.writerow(["Node"])
        for node in graph.nodes():
            writer.writerow([node])
    
    with open(edges_file_path, 'w', newline='') as edges_file:
        writer = csv.writer(edges_file)
        writer.writerow(["Source", "Target", "Weight"])
        for u, v, data in graph.edges(data=True):
            writer.writerow([u, v, data['weight']])

def analyze_rtt(
        output_data_dir, satellite_network_dir, dynamic_state_update_interval_ms,
        simulation_end_time_s, satgenpy_dir_with_ending_slash
):

    # Dynamic state directory
    satellite_network_dynamic_state_dir = "%s/dynamic_state_%dms_for_%ds" % (
        satellite_network_dir, dynamic_state_update_interval_ms, simulation_end_time_s
    )

    # Local shell
    local_shell = exputil.LocalShell()
    core_network_folder_name = satellite_network_dir.split("/")[-1]
    base_output_dir = "%s/%s/%dms_for_%ds/rtt" % (
        output_data_dir, core_network_folder_name, dynamic_state_update_interval_ms, simulation_end_time_s
    )
    pdf_dir = base_output_dir + "/pdf"
    data_dir = base_output_dir + "/data"
    local_shell.remove_force_recursive(pdf_dir)
    local_shell.remove_force_recursive(data_dir)
    local_shell.make_full_dir(pdf_dir)
    local_shell.make_full_dir(data_dir)

    # Variables (load in for each thread such that they don't interfere)
    ground_stations = read_ground_stations_extended(satellite_network_dir + "/ground_stations.txt")
    tles = read_tles(satellite_network_dir + "/tles.txt")
    satellites = tles["satellites"]
    list_isls = read_isls(satellite_network_dir + "/isls.txt", len(satellites))
    epoch = tles["epoch"]
    description = exputil.PropertiesConfig(satellite_network_dir + "/description.txt")

    # Derivatives
    simulation_end_time_ns = simulation_end_time_s * 1000 * 1000 * 1000
    dynamic_state_update_interval_ns = dynamic_state_update_interval_ms * 1000 * 1000
    max_gsl_length_m = exputil.parse_positive_float(description.get_property_or_fail("max_gsl_length_m"))
    max_isl_length_m = exputil.parse_positive_float(description.get_property_or_fail("max_isl_length_m"))

    # Analysis
    rtt_list_per_pair = []
    for i in range(len(ground_stations)):
        temp_list = []
        for j in range(len(ground_stations)):
            temp_list.append([])
        rtt_list_per_pair.append(temp_list)
    unreachable_per_pair = np.zeros((len(ground_stations), len(ground_stations)))

    # For each time moment
    fstate = {}
    num_iterations = simulation_end_time_ns / dynamic_state_update_interval_ns
    it = 1
    for t in range(0, simulation_end_time_ns, dynamic_state_update_interval_ns):

        # Read in forwarding state
        with open(satellite_network_dynamic_state_dir + "/fstate_" + str(t) + ".txt", "r") as f_in:
            for line in f_in:
                spl = line.split(",")
                current = int(spl[0])
                destination = int(spl[1])
                next_hop = int(spl[2])
                fstate[(current, destination)] = next_hop

            # Given we are going to graph often, we can pre-compute the edge lengths
            graph_with_distance = construct_graph_with_distances(epoch, t, satellites, ground_stations,
                                                                 list_isls, max_gsl_length_m, max_isl_length_m)
            
        # Show progress a bit
        print("%d / %d" % (it, num_iterations))
        it += 1
    print("")