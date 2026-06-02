from figures.plots_with_scaling import plot_satellite_positions
from figures.plots_with_scaling_delete import plot_satellite_usage
import os
from config import DEFAULT_GROUND_STATIONS_FILE, KUIPER_DATA_NAME, PROJECT_FIGURES_DIR, PROJECT_NETWORKS_DIR, analysis_window_dir

# Satellite network data configuration
satellite_data_name = KUIPER_DATA_NAME

# Base directory of the script
base_directory = os.path.dirname(os.path.abspath(__file__))

# Simulation parameters
simulation_end_time_seconds = 200 
dynamic_state_update_interval_ms = 1000  
simulation_end_time_ns = simulation_end_time_seconds * 1e9  
dynamic_state_update_interval_ns = dynamic_state_update_interval_ms * 1e6  

# Path to ground stations file
ground_stations_file = DEFAULT_GROUND_STATIONS_FILE

# Paths for satellite data
latlon_output_path = PROJECT_NETWORKS_DIR / satellite_data_name / "satellite_lat_lon"
usage_data_dir = analysis_window_dir(satellite_data_name) / "satellite_usage_ranking" / "delete_0"
total_usage_data_file_path = os.path.join(usage_data_dir, "total_satellite_usage_ranking.txt")

# Directory for plotting satellite positions
plots_with_scaling_output_dir = PROJECT_FIGURES_DIR / satellite_data_name / "usage_plots_with_scaling"

def generate_figures():
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
        current_usage_dir = analysis_window_dir(satellite_data_name) / "satellite_usage_ranking" / deletion_label
        last_usage_dir = analysis_window_dir(satellite_data_name) / "satellite_usage_ranking" / last_deletion_label
    
        # Output directory for plots with scaling for each deletion scenario
        plots_with_scaling_delete_output_dir = PROJECT_FIGURES_DIR / satellite_data_name / f"usage_plots_with_scaling_{deletion_label}"
    
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
