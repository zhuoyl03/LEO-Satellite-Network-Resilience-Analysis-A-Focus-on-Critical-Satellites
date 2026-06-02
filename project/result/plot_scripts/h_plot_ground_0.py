import matplotlib.pyplot as plt
import os
import numpy as np
from mpl_toolkits.basemap import Basemap
from mpl_toolkits.axes_grid1.inset_locator import inset_axes
import sys
from pathlib import Path
PROJECT_DIR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_DIR))
from config import LEGACY_STARLINK_SHELL_NAME, PROJECT_RESULT_GENERATED_DIR, PROJECT_NETWORKS_DIR, STARLINK_DATA_NAME, analysis_window_dir

# Define file paths
output_plot_dir = PROJECT_RESULT_GENERATED_DIR / "scatter_plots"
histogram_plot_dir = PROJECT_RESULT_GENERATED_DIR
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

def read_satellite_positions(file_path, map):
    satellite_dict = {}
    with open(file_path, 'r') as file:
        for line in file:
            name, coords = line.split(':')
            coords = coords.strip()  # Ensure no extra whitespace
            latitude, longitude = coords.split(',')
            latitude = float(latitude.strip())
            longitude = float(longitude.strip())
            satellite_number = int(name.split()[1])
           
            # Determine if the satellite is over land or sea
            x, y = map(longitude, latitude)
            is_land = map.is_land(x, y)
            
            # Add satellite number, coordinates, and land/sea info to the dictionary
            satellite_dict[satellite_number] = (latitude, longitude, is_land)
    return satellite_dict

# Create a Basemap instance for land/sea determination
map = Basemap(projection='cyl', resolution='l',
              llcrnrlat=-90, urcrnrlat=90,
              llcrnrlon=-180, urcrnrlon=180)

zero_gs_sea_usage_counts = []
zero_gs_land_usage_counts = []

def plot_zero_ground_station_land_sea_histogram():
    for t in range(0, simulation_end_time_ns, dynamic_state_update_interval_ns):

        usage_file = analysis_window_dir(STARLINK_DATA_NAME) / "usage" / "satellite_usage_ranking" / f"satellite_usage_ranking_at_{t}.txt"
        gs_file = PROJECT_NETWORKS_DIR / LEGACY_STARLINK_SHELL_NAME / "satellite_gs_ranking" / f"satellite_gs_ranking_at_{t}.txt"
        lat_lon_file = PROJECT_NETWORKS_DIR / LEGACY_STARLINK_SHELL_NAME / "satellite_lat_lon" / f"satellites_latlon_at_{t}.txt"
        # Ensure the output directory exists
        if not os.path.exists(output_plot_dir):
            os.makedirs(output_plot_dir)

        # Read the data
        usage_data = read_usage_data(usage_file)
        gs_data = read_gs_data(gs_file)

        # Ensure we only plot satellites that exist in both datasets
        satellites = set(usage_data.keys()).intersection(set(gs_data.keys()))

        # Read satellite positions with land/sea classification
        satellite_positions = read_satellite_positions(lat_lon_file, map)

        for sat in satellites:
            if sat in satellite_positions:
                lat, lon, is_land = satellite_positions[sat]
                if gs_data[sat] == 0:
                    if is_land:
                        zero_gs_land_usage_counts.append(usage_data[sat])
                    else:
                        zero_gs_sea_usage_counts.append(usage_data[sat])

    # Plot the histogram for zero ground station usage counts for sea and land
    plt.figure(figsize=(10, 6))
    bins = np.linspace(min(min(zero_gs_sea_usage_counts), min(zero_gs_land_usage_counts)),
                       max(max(zero_gs_sea_usage_counts), max(zero_gs_land_usage_counts)), 50)
    plt.hist(zero_gs_sea_usage_counts, bins=bins, edgecolor='k', alpha=0.5, label='Sea Usage Counts with 0 GS', color='b')
    plt.hist(zero_gs_land_usage_counts, bins=bins, edgecolor='k', alpha=0.5, label='Land Usage Counts with 0 GS', color='r')

    plt.title('Histogram of Satellite Usage Counts with 0 Ground Stations: Sea vs Land')
    plt.xlabel('Usage Counts')
    plt.ylabel('Frequency')
    plt.legend(loc='upper right')
    plt.grid(True)

    # Add inset for usage counts greater than 200
    ax_inset = inset_axes(plt.gca(), width="50%", height="50%", loc='upper right')
    filtered_sea_usage_counts = [count for count in zero_gs_sea_usage_counts if count > 200]
    filtered_land_usage_counts = [count for count in zero_gs_land_usage_counts if count > 200]

    bins_inset = np.linspace(min(min(filtered_sea_usage_counts), min(filtered_land_usage_counts)),
                             max(max(filtered_sea_usage_counts), max(filtered_land_usage_counts)), 50)
    ax_inset.hist(filtered_sea_usage_counts, bins=bins_inset, edgecolor='k', alpha=0.5, label='Sea > 200', color='b')
    ax_inset.hist(filtered_land_usage_counts, bins=bins_inset, edgecolor='k', alpha=0.5, label='Land > 200', color='r')
    ax_inset.set_xlabel('Usage Counts')
    ax_inset.set_ylabel('Frequency')
    ax_inset.legend(loc='upper right')
    ax_inset.grid(True)

    # Save the histogram with inset
    histogram_file_path = os.path.join(histogram_plot_dir, 'histogram_zero_gs_sea_vs_land_usage_counts_with_inset.png')
    plt.savefig(histogram_file_path)
    print(f"Histogram with inset saved to {histogram_file_path}")

    # Optionally close the histogram plot if running in a script to free memory
    plt.close()
