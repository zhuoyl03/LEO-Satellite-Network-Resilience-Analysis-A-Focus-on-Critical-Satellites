import os
import sys
import matplotlib.pyplot as plt
from mpl_toolkits.basemap import Basemap
import numpy as np

simulation_end_time_s = 200
dynamic_state_update_interval_ms = 1000
simulation_end_time_ns = simulation_end_time_s * 1000 * 1000 * 1000
dynamic_state_update_interval_ns = dynamic_state_update_interval_ms * 1000 * 1000

latlon_dir = "/home/leo/hypatia/ECE227/satellite_networks/gen_data/72_22_53_550_starlinkshell1/satellite_lat_lon"

# Path to the connection file
connection_file = '/home/leo/hypatia/ECE227/1593_to_1590_path_changes.txt'


output_data_dir = "/home/leo/hypatia/ECE227/figures/end_to_end_path_plot"
if not os.path.exists(output_data_dir):
    os.makedirs(output_data_dir)

def read_satellite_positions(file_path):
    satellite_dict = {}
    with open(file_path, 'r') as file:
        for line in file:
            name, coords = line.split(':')
            latitude, longitude = map(float, coords.split(','))
            satellite_number = int(name.split()[1])
            satellite_dict[satellite_number] = (latitude, longitude)
    return satellite_dict

def read_connection_file(file_path):
    connections = set()
    with open(file_path, 'r') as file:
        for line in file:
            parts = line.strip().split(',')
            if len(parts) == 2:
                path = parts[1].split('-')
                for sat_id in path:
                    connections.add(int(sat_id))
    return connections


# Loop through each time interval and plot the satellites
for t in range(0, simulation_end_time_ns, dynamic_state_update_interval_ns):
    latlon_file = os.path.join(latlon_dir, 'satellites_latlon_at_' + str(t) + '.txt')
    
    if os.path.exists(latlon_file):
        satellite_positions = read_satellite_positions(latlon_file)
        connected_satellites = read_connection_file(connection_file)
        
        plt.figure(figsize=(16, 9))  # Adjusted figure size
        m = Basemap(projection='cyl', llcrnrlat=-90, urcrnrlat=90, llcrnrlon=-180, urcrnrlon=180, resolution='c')
        m.drawcoastlines()
        m.drawcountries()
        m.drawmapboundary(fill_color='aqua')
        m.drawparallels(np.arange(-90., 91., 30.), labels=[1, 0, 0, 0])
        m.drawmeridians(np.arange(-180., 181., 60.), labels=[0, 0, 0, 1])
        
        for sat, (lat, lon) in satellite_positions.items():
            x, y = m(lon, lat)
            if sat in connected_satellites:
                m.scatter(x, y, marker='o', color='blue', s=50, zorder=5, alpha=0.7)
            else:
                m.scatter(x, y, marker='o', color='red', s=15, zorder=5, alpha=0.7)

        plt.title(f'Satellites at Time {t}')
        
        # Save the plot to the output directory
        output_filename = os.path.join(output_data_dir, f'satellites_at_{t}.png')
        plt.savefig(output_filename)
        plt.close()
