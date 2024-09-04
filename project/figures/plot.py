import matplotlib.pyplot as plt
import os
import numpy as np

# Define file paths
output_plot_dir = '/home/leo/hypatia/ECE227/figures/plots'
latlon_dir = "/home/leo/hypatia/ECE227/satellite_networks/gen_data/72_22_53_550_starlinkshell1/satellite_lat_lon"

simulation_end_time_s = 200
dynamic_state_update_interval_ms = 1000

simulation_end_time_ns = simulation_end_time_s * 1000 * 1000 * 1000
dynamic_state_update_interval_ns = dynamic_state_update_interval_ms * 1000 * 1000

# Function to read the data from the files
def read_usage_data(file_path):
    usage_data = {}
    with open(file_path, 'r') as file:
        lines = file.readlines()[1:]  # Skip the header lines
        for line in lines:
            parts = line.strip().split(':')
            if len(parts) == 2:
                satellite_part = parts[1].strip()
                satellite_id = int(satellite_part.split(" ")[1])
                usage_count = int(satellite_part.split(" ")[3])
                usage_data[satellite_id] = usage_count
    return usage_data

def read_gs_data(file_path):
    gs_data = {}
    with open(file_path, 'r') as file:
        lines = file.readlines()[1:]  # Skip the header line
        for line in lines:
            parts = line.strip().split(':')
            if len(parts) == 2:
                gs_part = parts[1].strip()
                satellite_id = int(gs_part.split()[1])
                gs_count = int(gs_part.split()[3])
                gs_data[satellite_id] = gs_count
    return gs_data


def read_satellite_positions(file_path):
    # Define dictionary
    satellite_dict = {}

    # Open the file
    with open(file_path, 'r') as file:
        # Read each line
        for line in file:
            # Split the line to get satellite name and coordinates
            name, coords = line.split(':')
            latitude, longitude = map(float, coords.split(','))
            
            # Extract satellite number
            satellite_number = int(name.split()[1])
            
            # Add satellite number and coordinates to the dictionary
            satellite_dict[satellite_number] = (latitude, longitude)
    return satellite_dict

for t in range(0, simulation_end_time_ns, dynamic_state_update_interval_ns):

    usage_file = '"/home/leo/hypatia/ECE227/satgen_analysis/starlink_550_isls_plus_grid_ground_stations_top_100_algorithm_free_one_only_over_isls/1000ms_for_200s/usage/satellite_usage_ranking/satellite_usage_ranking_at_' + str(t) + '.txt'
    gs_file = '/home/leo/hypatia/ECE227/satellite_networks/gen_data/72_22_53_550_starlinkshell1/satellite_gs_ranking/satellite_gs_ranking_at_' + str(t) + '.txt'

    # Ensure the output directory exists
    if not os.path.exists(output_plot_dir):
        os.makedirs(output_plot_dir)



    # Read the data
    usage_data = read_usage_data(usage_file)
    gs_data = read_gs_data(gs_file)

    # Ensure we only plot satellites that exist in both datasets
    satellites = set(usage_data.keys()).intersection(set(gs_data.keys()))

    # Prepare the data for plotting
    usage_counts = [usage_data[sat] for sat in satellites]
    gs_counts = [gs_data[sat] for sat in satellites]

    # Define usage bins
    usage_bins = [(0, 200), (200, 400), (400, 600), (600, np.inf)]
    colors = ['b', 'g', 'r', 'c']

    # Plot the ECDFs
    plt.figure(figsize=(10, 6))
    for i, (low, high) in enumerate(usage_bins):
        filtered_gs_counts = [gs_data[sat] for sat in satellites if low <= usage_data[sat] < high]
        if filtered_gs_counts:
            filtered_gs_counts_sorted = np.sort(filtered_gs_counts)
            ecdf_y = np.arange(1, len(filtered_gs_counts_sorted) + 1) / len(filtered_gs_counts_sorted)
            plt.step(filtered_gs_counts_sorted, ecdf_y, label=f'Usage {low}-{high}', where='post', color=colors[i])

    plt.title('ECDF of Ground Stations Connected for Different Usage Counts')
    plt.xlabel('Number of Ground Stations Connected')
    plt.ylabel('ECDF')
    plt.legend()
    plt.grid(True)

    # Save the plot
    plot_file_path = os.path.join(output_plot_dir, f'ecdf_gs_connected_vs_usage_count_at_{t}.png')
    plt.savefig(plot_file_path)
    print(f"Plot saved to {plot_file_path}")

    # Optionally close the plot if running in a script to free memory
    plt.close()