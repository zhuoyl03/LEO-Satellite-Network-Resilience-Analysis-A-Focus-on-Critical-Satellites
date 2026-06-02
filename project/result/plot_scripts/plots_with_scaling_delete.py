import os
import matplotlib.pyplot as plt
from mpl_toolkits.basemap import Basemap
import numpy as np
import matplotlib.colors as mcolors

def plot_satellite_usage(latlon_dir, total_usage_data_dir, origin_usage_dir, usage_ranking_dir, output_data_dir, deletion_of_satellites, simulation_end_time_ns, dynamic_state_update_interval_ns):

    # Ensure the output directory exists
    if not os.path.exists(output_data_dir):
        os.makedirs(output_data_dir)

    # Function to read usage data from file
    def read_usage_data(file_path):
        usage_data = {}
        if not os.path.exists(file_path):
            print(f"File not found: {file_path}")
            return usage_data
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

    # Function to read the data from the files
    def read_total_usage_data(file_path, num):
        usage_data = []
        if not os.path.exists(file_path):
            print(f"File not found: {file_path}")
            return usage_data
        with open(file_path, 'r') as file:
            lines = file.readlines()[1:]  # Skip the header lines
            i = 0
            for line in lines:
                parts = line.strip().split(':')
                if len(parts) == 2:
                    satellite_part = parts[1].strip()
                    satellite_id = int(satellite_part.split(" ")[1])
                    usage_data.append(satellite_id)
                    i += 1
                    if i >= num:
                        break
        return usage_data

    # Function to read satellite positions from file
    def read_satellite_positions(file_path):
        satellite_dict = {}
        if not os.path.exists(file_path):
            print(f"File not found: {file_path}")
            return satellite_dict
        with open(file_path, 'r') as file:
            for line in file:
                name, coords = line.split(':')
                latitude, longitude = map(float, coords.split(','))
                satellite_number = int(name.split()[1])
                satellite_dict[satellite_number] = (latitude, longitude)
        return satellite_dict

    # Check and read total usage data
    if not os.path.exists(total_usage_data_dir):
        print("total_usage_data_dir error")
        total_usage_data = []
    else:
        total_usage_data = read_total_usage_data(total_usage_data_dir, deletion_of_satellites)  # Modify this parameter to change the number of deleted satellites
    print(total_usage_data)

    # Function to calculate arctangent scores for normalization
    def calculate_arctan_scores(values):
        max_abs_value = max(abs(v) for v in values)
        if max_abs_value == 0:
            return [0] * len(values)  # Avoid division by zero
        arctan_scores = [np.arctan(x / max_abs_value) for x in values]
        return arctan_scores

    # Main loop to process each time interval
    for t in range(0, simulation_end_time_ns, dynamic_state_update_interval_ns):
        usage_file = os.path.join(usage_ranking_dir, f'satellite_usage_ranking_at_{t}.txt')
        origin_file = os.path.join(origin_usage_dir, f'satellite_usage_ranking_at_{t}.txt')
        latlon_file = os.path.join(latlon_dir, f'satellites_latlon_at_{t}.txt')
        
        if os.path.exists(usage_file) and os.path.exists(latlon_file) and os.path.exists(origin_file):
            usage_data = read_usage_data(usage_file)
            satellite_positions = read_satellite_positions(latlon_file)
            origin_data = read_usage_data(origin_file)
            
            filtered_usage_data = {sat: usage for sat, usage in usage_data.items() if usage > 0 or sat in total_usage_data}

            # Calculate the increases
            increases = [filtered_usage_data[sat] - origin_data.get(sat, 0) for sat in filtered_usage_data]
            
            # Calculate arctan scores for the increases
            arctan_scores = calculate_arctan_scores(increases)
            
            fig, ax = plt.subplots(figsize=(16, 9))  # Adjusted figure size
            m = Basemap(projection='cyl', llcrnrlat=-90, urcrnrlat=90, llcrnrlon=-180, urcrnrlon=180, resolution='c', ax=ax)
            m.drawcoastlines(color='gray')
            m.drawcountries(color='lightgray')  # Set the country boundaries color to light gray
            m.drawmapboundary(fill_color='white')  # Changed the map boundary fill color to white
            m.fillcontinents(color='lightgray', lake_color='white')  # Changed continent color to light gray
            m.drawparallels(np.arange(-90., 91., 30.), labels=[1, 0, 0, 0], color='gray', fontsize=20)  # Increased fontsize
            m.drawmeridians(np.arange(-180., 181., 60.), labels=[0, 0, 0, 1], color='gray', fontsize=20)  # Increased fontsize
            
            max_arctan_score = max(arctan_scores) if arctan_scores else 1  # Avoid division by zero
            min_arctan_score = min(arctan_scores) if arctan_scores else -1  # Avoid division by zero
            
            scatter_list = []
            for idx, (sat, usage) in enumerate(filtered_usage_data.items()):
                if sat in total_usage_data:
                    lat, lon = satellite_positions[sat]
                    x, y = m(lon, lat)
                    scatter_list.append(m.scatter(x, y, marker='o', color='green', s=10, zorder=5, alpha=1))  # 's' is the size of the marker
                elif sat in satellite_positions:
                    lat, lon = satellite_positions[sat]
                    x, y = m(lon, lat)
                    if sat in origin_data:
                        arctan_score = arctan_scores[idx]
                        if arctan_score >= 0:
                            color = plt.cm.Reds(arctan_score)
                        else:
                            color = plt.cm.Blues(-arctan_score)
                        alpha = 0.2 + 0.5 * abs(arctan_score)  # Normalize to the range [0.2, 0.8]
                        scatter_list.append(m.scatter(x, y, marker='o', color=color, s=usage, zorder=5, alpha=0.7))  # Adjusted alpha usage
                    else:
                        scatter_list.append(m.scatter(x, y, marker='o', color='red', s=usage, zorder=5, alpha=0.7))  # 's' is the size of the marker
            
            # Create a custom colormap for the colorbar
            reds = plt.cm.Reds(np.linspace(0, 1, 128))
            blues = plt.cm.Blues(np.linspace(1, 0, 128))  # Reverse Blues
            colors = np.vstack((blues, reds))
            custom_cmap = mcolors.LinearSegmentedColormap.from_list("custom_cmap", colors, N=256)

            # Add colorbar
            sm = plt.cm.ScalarMappable(cmap=custom_cmap)
            sm.set_array(np.linspace(-np.pi / 2, np.pi / 2, 256))
            cbar = plt.colorbar(sm, orientation='vertical', shrink=0.5, ax=ax)
            cbar.set_label('Arctan Score of Increases', fontsize=20)
            cbar.set_ticks([-np.pi / 2, -np.pi / 4, 0, np.pi / 4, np.pi / 2])  # Manually set the ticks
            cbar.set_ticklabels(['-π/2', '-π/4', '0', 'π/4', 'π/2'])  # Manually set the tick labels

            plt.title('Satellites by Usage', fontsize=20)
            output_filename = os.path.join(output_data_dir, f'satellites_usage_at_{t}.pdf')  # Save as PDF
            plt.savefig(output_filename, format='pdf', bbox_inches='tight', pad_inches=0.1)
            plt.close()
            
            print(f"Satellite positions plotted for time {t}")
        else:
            print(f"Missing data for time {t}")
