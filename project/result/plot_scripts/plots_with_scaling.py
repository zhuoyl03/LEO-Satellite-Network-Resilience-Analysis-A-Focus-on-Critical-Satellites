import os
import sys
import matplotlib.pyplot as plt
from mpl_toolkits.basemap import Basemap
import numpy as np
from pathlib import Path
PROJECT_DIR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_DIR))
from config import SATGENPY_DIR
sys.path.append(str(SATGENPY_DIR))
import satgen

def plot_satellite_positions(latlon_dir, usage_ranking_dir, output_data_dir, ground_stations_file, simulation_end_time_ns, dynamic_state_update_interval_ns):

    # Ensure the output directory exists
    if not os.path.exists(output_data_dir):
        os.makedirs(output_data_dir)

    # Function to read usage data from file
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
        return usage_data

    # Function to read satellite positions from file
    def read_satellite_positions(file_path):
        satellite_dict = {}
        with open(file_path, 'r') as file:
            for line in file:
                name, coords = line.split(':')
                latitude, longitude = map(float, coords.split(','))
                satellite_number = int(name.split()[1])
                satellite_dict[satellite_number] = (latitude, longitude)
        return satellite_dict

    # Read ground stations data
    ground_stations = satgen.read_ground_stations_basic(ground_stations_file)

    # Extract coordinates of ground stations
    ground_station_coordinates = {gs['name']: (float(gs['latitude_degrees_str']), float(gs['longitude_degrees_str'])) for gs in ground_stations}

    # Main loop to process each time interval
    for t in range(0, simulation_end_time_ns, dynamic_state_update_interval_ns):
        usage_file = os.path.join(usage_ranking_dir, f'satellite_usage_ranking_at_{t}.txt')
        latlon_file = os.path.join(latlon_dir, f'satellites_latlon_at_{t}.txt')
        
        if os.path.exists(usage_file) and os.path.exists(latlon_file):
            usage_data = read_usage_data(usage_file)
            satellite_positions = read_satellite_positions(latlon_file)
            
            filtered_usage_data = {sat: usage for sat, usage in usage_data.items() if usage > 0}
            
            plt.figure(figsize=(16, 9))  # Adjusted figure size
            m = Basemap(projection='cyl', llcrnrlat=-90, urcrnrlat=90, llcrnrlon=-180, urcrnrlon=180, resolution='c')
            m.drawcoastlines(color='gray')
            m.drawcountries(color='lightgray')
            m.drawmapboundary(fill_color='white')
            m.fillcontinents(color='lightgray', lake_color='white')
            m.drawparallels(np.arange(-90., 91., 30.), labels=[1, 0, 0, 0], color='gray', fontsize=20)
            m.drawmeridians(np.arange(-180., 181., 60.), labels=[0, 0, 0, 1], color='gray', fontsize=20)
            
            satellite_marker = m.scatter([], [], marker='o', color='red', s=50, zorder=5, alpha=0.6, label='Satellites')
            ground_station_marker = m.scatter([], [], marker='x', color='blue', s=50, zorder=5, alpha=0.7, label='Ground Stations')

            for sat, usage in filtered_usage_data.items():
                if sat in satellite_positions:
                    lat, lon = satellite_positions[sat]
                    x, y = m(lon, lat)
                    m.scatter(x, y, marker='o', color='red', s=usage, zorder=5, alpha=0.6)

            for station, (lat, lon) in ground_station_coordinates.items():
                x, y = m(lon, lat)
                m.scatter(x, y, marker='x', color='blue', s=50, zorder=5, alpha=0.7)

            plt.legend(handles=[satellite_marker, ground_station_marker], loc='upper right', fontsize=12)
            plt.title('Two-Dimensional Geographical Distribution of Satellites and Ground Stations')
            output_filename = os.path.join(output_data_dir, f'satellites_usage_at_{t}.pdf')
            plt.savefig(output_filename, format='pdf')
            plt.close()
            
            print(f"Satellite positions plotted for time {t}")
