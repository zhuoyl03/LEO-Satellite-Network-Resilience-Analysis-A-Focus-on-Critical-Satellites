from satellite_networks.construct_graph import construct_graph
from satellite_networks.gen_path import gen_path
from satellite_networks.calculate_lat_lon import calculate_lat_lon
from satgen_analysis.analyze_rtt_with_graph import analyze_rtt_with_graph
import os

# Configuration for the satellite network simulation
satellite_data_name = "kuiper_590_isls_plus_grid_ground_stations_top_100_algorithm_free_one_only_over_isls"
satellite_count = 784  # Number of satellites in the network
ground_station_count = 100  # Number of ground stations

# Simulation parameters
simulation_end_time_seconds = 200 
dynamic_state_update_interval_ms = 1000  
simulation_end_time_ns = simulation_end_time_seconds * 1e9  
dynamic_state_update_interval_ns = dynamic_state_update_interval_ms * 1e6  

# Geodesic ECDF plot cutoff in kilometers
geodesic_distance_cutoff_km = 500

# Directory paths setup
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
deletion_counts = [50, 100]  # List of deletion scenarios to simulate

# Paths to various input and output files
usage_ranking_file = os.path.join(current_dir, "satgen_analysis", satellite_data_name, "1000ms_for_200s/satellite_usage_ranking/delete_0/total_satellite_usage_ranking.txt")
satellite_network_data_dir = os.path.join(project_root_dir, "paper/satellite_networks_state/gen_data/", satellite_data_name)

satgenpy_dir = project_root_dir + "/satgenpy/"
output_rtt_data_dir = os.path.join(current_dir, "satgen_analysis")

# Output path for satellite latitude and longitude data
latlon_output_path = os.path.join(current_dir, "satellite_networks/gen_data/", satellite_data_name, "satellite_lat_lon")

# Calculate satellite latitude and longitude positions over the simulation period
calculate_lat_lon(satellite_network_data_dir, latlon_output_path, simulation_end_time_ns, dynamic_state_update_interval_ns)

# Iterate over each deletion scenario
for num_deletions in deletion_counts:
    # Construct the directory name for graph data based on the number of deletions
    graph_output_dir = os.path.join(current_dir, "satellite_networks", "gen_data", satellite_data_name, "graph")
    deletion_label = f"delete_{num_deletions}"  # Label for the deletion scenario
    graph_data_path = os.path.join(graph_output_dir, deletion_label)

    # Paths for usage output and path generation
    usage_output_dir = os.path.join(current_dir, "satgen_analysis", satellite_data_name, "1000ms_for_200s", "satellite_usage_ranking", deletion_label)
    path_output_path = os.path.join(current_dir, "satellite_networks", "gen_data", satellite_data_name, "path", deletion_label + ".txt")

    # Construct the network graph after satellite deletions
    construct_graph(graph_data_path, usage_ranking_file, satellite_network_data_dir, num_deletions, simulation_end_time_ns, dynamic_state_update_interval_ns)

    # Generate data of paths for the given network configuration
    gen_path(graph_data_path, simulation_end_time_ns, dynamic_state_update_interval_ns, usage_output_dir, satellite_count, ground_station_count, satellite_network_data_dir, path_output_path)

    # Analyze the RTT with the generated paths
    rtt_output_name = "rtt_" + deletion_label
    analyze_rtt_with_graph(
        simulation_end_time_ns,
        dynamic_state_update_interval_ns,
        satellite_network_data_dir,
        satgenpy_dir,
        output_rtt_data_dir,
        rtt_output_name,
        path_output_path,
        graph_data_path,
        geodesic_distance_cutoff_km
    )
