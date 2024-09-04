from figures.plots_with_scaling import plot_satellite_positions
from figures.plots_with_scaling_delete import plot_satellite_usage
import os

# Satellite network data configuration
satellite_data_name = "kuiper_590_isls_plus_grid_ground_stations_top_100_algorithm_free_one_only_over_isls"

# Base directory of the script
base_directory = os.path.dirname(os.path.abspath(__file__))

# Simulation parameters
simulation_end_time_seconds = 200 
dynamic_state_update_interval_ms = 1000  
simulation_end_time_ns = simulation_end_time_seconds * 1e9  
dynamic_state_update_interval_ns = dynamic_state_update_interval_ms * 1e6  

# Path to ground stations file
ground_stations_file = os.path.expanduser("~/hypatia/paper/satellite_networks_state/input_data/ground_stations_cities_sorted_by_estimated_2025_pop_top_100.basic.txt")

# Paths for satellite data
latlon_output_path = os.path.join(base_directory, "satellite_networks/gen_data/", satellite_data_name, "satellite_lat_lon")
usage_data_dir = os.path.join(base_directory, "satgen_analysis", satellite_data_name, "1000ms_for_200s/satellite_usage_ranking/delete_0")
total_usage_data_file_path = os.path.join(usage_data_dir, "total_satellite_usage_ranking.txt")

# Directory for plotting satellite positions
plots_with_scaling_output_dir = os.path.join(base_directory, "figures/starlink_550_isls_plus_grid_ground_stations_top_100_algorithm_free_one_only_over_isls/usage_plots_with_scaling")

# Plot satellite positions using scaling
plot_satellite_positions(latlon_output_path, usage_data_dir, plots_with_scaling_output_dir, ground_stations_file, simulation_end_time_ns, dynamic_state_update_interval_ns)

# Different deletion scenarios to simulate
deletion_scenarios = [50, 100]
previous_deletion_scenarios = [0, 50]  # Corresponding previous deletions for comparisons

# Iterate through deletion scenarios and plot results
for deletion, last_deletion in zip(deletion_scenarios, previous_deletion_scenarios):
    deletion_label = f"delete_{deletion}"
    last_deletion_label = f"delete_{last_deletion}"
    
    # Paths for current and previous usage data
    current_usage_dir = os.path.join(base_directory, "satgen_analysis", satellite_data_name, "1000ms_for_200s", "satellite_usage_ranking", deletion_label)
    last_usage_dir = os.path.join(base_directory, "satgen_analysis", satellite_data_name, "1000ms_for_200s", "satellite_usage_ranking", last_deletion_label)
    
    # Output directory for plots with scaling for each deletion scenario
    plots_with_scaling_delete_output_dir = os.path.join(base_directory, "figures", satellite_data_name, f"usage_plots_with_scaling_{deletion_label}")
    
    # Plot satellite usage considering deletions
    plot_satellite_usage(
        latlon_output_path,
        total_usage_data_file_path,
        last_usage_dir,
        current_usage_dir,
        plots_with_scaling_delete_output_dir,
        deletion,
        simulation_end_time_ns,
        dynamic_state_update_interval_ns
    )
