import os
import matplotlib.pyplot as plt
import numpy as np
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import sys
from adjustText import adjust_text  
from pathlib import Path
PROJECT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_DIR))
from config import DEFAULT_GROUND_STATIONS_FILE, PROJECT_FIGURES_DIR, SATGENPY_DIR
sys.path.append(str(SATGENPY_DIR))
import satgen

output_data_dir = PROJECT_FIGURES_DIR
output_filename = os.path.join(output_data_dir, 'ground_stations.png')

# Path to ground stations file
ground_stations_file = DEFAULT_GROUND_STATIONS_FILE

def plot_ground_stations():
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
