import os
import matplotlib.pyplot as plt
import numpy as np
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import sys
from adjustText import adjust_text  
sys.path.append("/home/leo/hypatia/satgenpy")
import satgen

output_data_dir = '/home/leo/hypatia/ECE227/figures'
output_filename = os.path.join(output_data_dir, 'ground_stations.png')

# Path to ground stations file
ground_stations_file = '/home/leo/hypatia/paper/satellite_networks_state/input_data/ground_stations_cities_sorted_by_estimated_2025_pop_top_100.basic.txt'

# Read ground stations data
ground_stations = satgen.read_ground_stations_basic(ground_stations_file)

# Extract coordinates of ground stations
ground_station_coordinates = {gs['name']: (float(gs['latitude_degrees_str']), float(gs['longitude_degrees_str'])) for gs in ground_stations}

# Select 100 ground stations (or all if less than 100)
selected_ground_stations = list(ground_station_coordinates.keys())[:100]

# Plotting the ground stations
fig = plt.figure(figsize=(16, 9))
ax = plt.axes(projection=ccrs.PlateCarree())
ax.add_feature(cfeature.COASTLINE)
ax.add_feature(cfeature.BORDERS)
ax.set_global()

# Plot the ground stations
texts = []  
for station, (lat, lon) in ground_station_coordinates.items():
    ax.plot(lon, lat, marker='o', color='red', markersize=3, transform=ccrs.PlateCarree())





plt.title('Ground Stations')


plt.savefig(output_filename)
plt.close()

print("Done")
