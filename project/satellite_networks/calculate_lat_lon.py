import ephem
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
PROJECT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_DIR))
from config import SATGENPY_DIR
sys.path.append(str(SATGENPY_DIR))
import satgen
import exputil

def dms_to_decimal(dms_str):
    sign = -1 if dms_str[0] == '-' else 1
    dms_str = dms_str[1:] if sign == -1 else dms_str
    degrees, minutes, seconds = map(float, dms_str.split(':'))
    return sign * (degrees + minutes / 60.0 + seconds / 3600.0)

def calculate_lat_lon(satellite_network_dir, output_path, simulation_end_time_ns, dynamic_state_update_interval_ns):
    # Ensure the output directory exists
    if not os.path.exists(output_path):
        os.makedirs(output_path)

    description = exputil.PropertiesConfig(os.path.join(satellite_network_dir, "description.txt"))
    max_gsl_length_m = exputil.parse_positive_float(description.get_property_or_fail("max_gsl_length_m"))

    # Read TLE data
    tles = satgen.read_tles(os.path.join(satellite_network_dir, "tles.txt"))
    satellites = tles["satellites"]
    epoch = tles['epoch']

    # Convert epoch to string format for ephem.Date
    epoch_str = epoch.strftime("%Y/%m/%d %H:%M:%S")
    time = ephem.Date(epoch_str)

    # Calculate and output satellite positions at each time point
    for t in range(0, simulation_end_time_ns, dynamic_state_update_interval_ns):
        current_time = ephem.Date(time + t / (24 * 3600 * 10**9))  # ephem.Date format, time increment in days
        output_filename = os.path.join(output_path, f'satellites_latlon_at_{t}.txt')
        with open(output_filename, 'w') as outfile:
            for satellite in satellites:
                name = satellite.name  # Extract satellite name
                satellite.compute(current_time)
                lat = dms_to_decimal(str(satellite.sublat))
                lon = dms_to_decimal(str(satellite.sublong))
                outfile.write(f"{name}: {lat}, {lon}\n")

    print(f"Satellite positions written to {output_path}")
