import os
import sys
import matplotlib.pyplot as plt
from mpl_toolkits.basemap import Basemap
import numpy as np
from adjustText import adjust_text
from pathlib import Path
PROJECT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_DIR))
from config import LEGACY_STARLINK_SHELL_NAME, PROJECT_FIGURES_DIR, PROJECT_NETWORKS_DIR, STARLINK_DATA_NAME, analysis_window_dir

simulation_end_time_s = 200
dynamic_state_update_interval_ms = 1000
simulation_end_time_ns = simulation_end_time_s * 1000 * 1000 * 1000
dynamic_state_update_interval_ns = dynamic_state_update_interval_ms * 1000 * 1000

latlon_dir = PROJECT_NETWORKS_DIR / LEGACY_STARLINK_SHELL_NAME / "satellite_lat_lon"
usage_ranking_dir = analysis_window_dir(STARLINK_DATA_NAME) / "usage" / "satellite_usage_ranking"

output_data_dir = PROJECT_FIGURES_DIR / "lat_lon_plot"
def plot_top_satellites_by_usage():
    if not os.path.exists(output_data_dir):
        os.makedirs(output_data_dir)

    # Function to read the data from the files
    def read_usage_data(file_path):
        usage_data = {}
        with open(file_path, 'r') as file:
            lines = file.readlines()[2:]  # Skip the header lines
            for line in lines:
                parts = line.strip().split(':')
                if len(parts) == 2:
                    satellite_part = parts[1].strip()
                    satellite_id = int(satellite_part.split(" ")[1])
                    usage_count = int(satellite_part.split(" ")[3])
                    usage_data[satellite_id] = usage_count
                    if len(usage_data) >= 10:
                        break
        return usage_data

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

    # Loop through each time interval and plot the top 10 satellites
    for t in range(0, simulation_end_time_ns, dynamic_state_update_interval_ns):
        usage_file = os.path.join(usage_ranking_dir, 'satellite_usage_ranking_at_' + str(t) + '.txt')
        latlon_file = os.path.join(latlon_dir, 'satellites_latlon_at_' + str(t) + '.txt')
    
        if os.path.exists(usage_file) and os.path.exists(latlon_file):
            usage_data = read_usage_data(usage_file)
            satellite_positions = read_satellite_positions(latlon_file)
        
            # Filter to get the top 10 satellites
            top_10_satellites = sorted(usage_data.keys(), key=lambda k: usage_data[k], reverse=True)[:10]
            top_10_positions = {sat: satellite_positions[sat] for sat in top_10_satellites if sat in satellite_positions}
        
            # Plot the positions on the world map
            plt.figure(figsize=(16, 9))  # Adjusted figure size
            m = Basemap(projection='cyl', llcrnrlat=-90, urcrnrlat=90, llcrnrlon=-180, urcrnrlon=180, resolution='c')
            m.drawcoastlines()
            m.drawcountries()
            m.drawmapboundary(fill_color='aqua')
            m.drawparallels(np.arange(-90., 91., 30.), labels=[1, 0, 0, 0])
            m.drawmeridians(np.arange(-180., 181., 60.), labels=[0, 0, 0, 1])
        
            texts = []
            for sat, (lat, lon) in top_10_positions.items():
                x, y = m(lon, lat)
                m.scatter(x, y, marker='o', color='red', zorder=5)
                texts.append(plt.text(x, y, f'Sat {sat}', fontsize=8, ha='left', va='bottom', color='blue'))
        
            adjust_text(texts, only_move={'points':'y', 'texts':'y'}, arrowprops=dict(arrowstyle='->', color='gray'))
        
            plt.title(f'Top 10 Satellites by Usage at Time {t}')
        
            # Save the plot to the output directory
            output_filename = os.path.join(output_data_dir, f'satellites_top_10_usage_at_{t}.png')
            plt.savefig(output_filename)
            plt.close()
