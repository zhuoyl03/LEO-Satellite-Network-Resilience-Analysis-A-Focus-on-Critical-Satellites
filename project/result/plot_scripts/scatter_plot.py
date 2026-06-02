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

all_sea_usage_counts = []
all_land_usage_counts = []

def plot_usage_ground_station_scatter():
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

        # Prepare the data for plotting
        usage_counts = [usage_data[sat] for sat in satellites]
        gs_counts = [gs_data[sat] for sat in satellites]

        # Read satellite positions with land/sea classification
        satellite_positions = read_satellite_positions(lat_lon_file, map)

        # Prepare lists for sea and land points
        sea_usage_counts = []
        sea_gs_counts = []
        land_usage_counts = []
        land_gs_counts = []
        satellite_usage_pairs = []

        for sat in satellites:
            if sat in satellite_positions:
                lat, lon, is_land = satellite_positions[sat]
                satellite_usage_pairs.append((sat, usage_data[sat]))
                if is_land:
                    land_usage_counts.append(usage_data[sat])
                    land_gs_counts.append(gs_data[sat])
                else:
                    sea_usage_counts.append(usage_data[sat])
                    sea_gs_counts.append(gs_data[sat])
                
        all_sea_usage_counts.extend(sea_usage_counts)
        all_land_usage_counts.extend(land_usage_counts)

        # Plot the scatter plot
        plt.figure(figsize=(12, 6))
        plt.scatter(sea_usage_counts, sea_gs_counts, color='b', label='Over Ocean')
        plt.scatter(land_usage_counts, land_gs_counts, color='r', label='Over Land')

        plt.title('# of Ground Stations Connected vs Usage Frequency per Satellite', fontsize=20)
        plt.xlabel('Usage Frequency per Satellite', fontsize=20)
        plt.ylabel('# of Ground Stations Connected per Satellite', fontsize=15)
        plt.legend()
        plt.grid(True)
        plt.xticks(fontsize=20)
        plt.yticks(fontsize=20)
        plt.legend(fontsize=17)
        # Save the plot as PDF
        plot_file_path = os.path.join(output_plot_dir, f'scatter_gs_connected_vs_usage_count_at_{t}.pdf')
        plt.savefig(plot_file_path, bbox_inches='tight', pad_inches=0.1)
        print(f"Plot saved to {plot_file_path}")

        # Optionally close the plot if running in a script to free memory
        plt.close()

    # Calculate ECDF for sea and land usage counts
    def ecdf(data):
        x = np.sort(data)
        y = np.arange(1, len(x) + 1) / len(x)
        return x, y

    # Plot the histogram for sea and land usage counts
    plt.figure(figsize=(10, 6))
    bins = np.linspace(min(min(all_sea_usage_counts), min(all_land_usage_counts)),
                       max(max(all_sea_usage_counts), max(all_land_usage_counts)), 50)
    plt.hist(all_sea_usage_counts, bins=bins, edgecolor='k', alpha=0.5, label='Sea Usage Counts', color='b')
    plt.hist(all_land_usage_counts, bins=bins, edgecolor='k', alpha=0.5, label='Land Usage Counts', color='r')

    plt.title('Histogram of Satellite Usage Counts: Sea vs Land')
    plt.xlabel('Usage Counts')
    plt.ylabel('Frequency')
    plt.legend(loc='upper right')
    plt.grid(True)

    # Add inset for usage counts greater than 200
    ax_inset = inset_axes(plt.gca(), width="50%", height="50%", loc='upper right')
    filtered_sea_usage_counts = [count for count in all_sea_usage_counts if count > 200]
    filtered_land_usage_counts = [count for count in all_land_usage_counts if count > 200]

    bins_inset = np.linspace(min(min(filtered_sea_usage_counts), min(filtered_land_usage_counts)),
                             max(max(filtered_sea_usage_counts), max(filtered_land_usage_counts)), 50)
    ax_inset.hist(filtered_sea_usage_counts, bins=bins_inset, edgecolor='k', alpha=0.5, label='Sea > 200', color='b')
    ax_inset.hist(filtered_land_usage_counts, bins=bins_inset, edgecolor='k', alpha=0.5, label='Land > 200', color='r')
    ax_inset.set_title('Usage Counts > 200')
    ax_inset.set_xlabel('Usage Counts')
    ax_inset.set_ylabel('Frequency')
    ax_inset.legend(loc='upper right')
    ax_inset.grid(True)

    # Save the histogram with inset as PDF
    histogram_file_path = os.path.join(histogram_plot_dir, 'histogram_sea_vs_land_usage_counts_with_inset.pdf')
    plt.savefig(histogram_file_path)
    print(f"Histogram with inset saved to {histogram_file_path}")

    # Optionally close the histogram plot if running in a script to free memory
    plt.close()

    # Filter out zero usage counts
    all_sea_usage_counts = [count for count in all_sea_usage_counts if count > 0]
    all_land_usage_counts = [count for count in all_land_usage_counts if count > 0]

    # Plot the histogram for sea and land usage counts without zero usage counts
    plt.figure(figsize=(10, 6))
    bins = np.linspace(min(min(all_sea_usage_counts), min(all_land_usage_counts)),
                       max(max(all_sea_usage_counts), max(all_land_usage_counts)), 50)
    plt.hist(all_sea_usage_counts, bins=bins, edgecolor='k', alpha=0.5, label='Sea Usage Counts', color='b')
    plt.hist(all_land_usage_counts, bins=bins, edgecolor='k', alpha=0.5, label='Land Usage Counts', color='r')

    plt.title('Histogram of Satellite Usage Counts: Sea vs Land')
    plt.xlabel('Usage Counts')
    plt.ylabel('Frequency')
    plt.legend(loc='upper right')
    plt.grid(True)

    # Add inset for usage counts greater than 200
    ax_inset = inset_axes(plt.gca(), width="50%", height="50%", loc='upper right')
    filtered_sea_usage_counts = [count for count in all_sea_usage_counts if count > 200]
    filtered_land_usage_counts = [count for count in all_land_usage_counts if count > 200]

    bins_inset = np.linspace(min(min(filtered_sea_usage_counts), min(filtered_land_usage_counts)),
                             max(max(filtered_sea_usage_counts), max(filtered_land_usage_counts)), 50)
    ax_inset.hist(filtered_sea_usage_counts, bins=bins_inset, edgecolor='k', alpha=0.5, label='Sea > 200', color='b')
    ax_inset.hist(filtered_land_usage_counts, bins=bins_inset, edgecolor='k', alpha=0.5, label='Land > 200', color='r')
    ax_inset.set_xlabel('Usage Counts')
    ax_inset.set_ylabel('Frequency')
    ax_inset.legend(loc='upper right')
    ax_inset.grid(True)

    # Save the histogram with inset as PDF
    histogram_file_path = os.path.join(histogram_plot_dir, 'histogram_sea_vs_land_usage_counts_no_0_with_inset.pdf')
    plt.savefig(histogram_file_path)
    print(f"Histogram with inset saved to {histogram_file_path}")

    # Optionally close the histogram plot if running in a script to free memory
    plt.close()
