import os
import pickle
import sys
from pathlib import Path

import exputil

PROJECT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_DIR))
from config import (
    LEGACY_STARLINK_SHELL_NAME,
    PROJECT_DIR as PROJECT_ROOT_DIR,
    STARLINK_DATA_NAME,
    legacy_starlink_graph_dir,
    paper_network_dir,
)


DEFAULT_CONFIG = {
    "graph_directory": str(legacy_starlink_graph_dir()),
    "output_data_dir": str(PROJECT_ROOT_DIR / "satellite_networks" / "gen_data" / LEGACY_STARLINK_SHELL_NAME / "satellite_gs_ranking"),
    "total_output_file_path": str(PROJECT_ROOT_DIR / "total_satellite_gs_ranking.txt"),
    "simulation_end_time_s": 200,
    "dynamic_state_update_interval_ms": 1000,
    "satellite_network_dir": str(paper_network_dir(STARLINK_DATA_NAME)),
    "satellite_count": 1584,
    "ground_station_count": 100,
}


def analyze_satellite_ground_station_connectivity(config=None):
    """Count how many ground stations each satellite can connect to per time step."""
    config = dict(DEFAULT_CONFIG if config is None else config)
    os.makedirs(config["output_data_dir"], exist_ok=True)

    simulation_end_time_ns = config["simulation_end_time_s"] * 1000 * 1000 * 1000
    dynamic_state_update_interval_ns = config["dynamic_state_update_interval_ms"] * 1000 * 1000

    description = exputil.PropertiesConfig(os.path.join(config["satellite_network_dir"], "description.txt"))
    max_gsl_length_m = exputil.parse_positive_float(description.get_property_or_fail("max_gsl_length_m"))

    satellite_nodes = set(range(config["satellite_count"]))
    ground_station_nodes = set(
        range(config["satellite_count"], config["satellite_count"] + config["ground_station_count"])
    )
    satellite_ground_station_counts = {sat: 0 for sat in satellite_nodes}

    for t in range(0, simulation_end_time_ns, dynamic_state_update_interval_ns):
        print(f"Generating data for t={t} ns (= {t / 1e9} seconds)")
        graph_path = os.path.join(config["graph_directory"], f"graph_at_{t}.pkl")

        if not os.path.exists(graph_path):
            print(f"Graph file {graph_path} does not exist.")
            continue

        with open(graph_path, "rb") as f:
            graph = pickle.load(f)

        satellite_usage = {sat: 0 for sat in satellite_nodes}
        for sat in satellite_nodes:
            for ground_station in ground_station_nodes:
                if graph.has_edge(sat, ground_station):
                    distance = graph[sat][ground_station]["weight"]
                    if distance <= max_gsl_length_m:
                        satellite_ground_station_counts[sat] += 1
                        satellite_usage[sat] += 1

        output_file_path = os.path.join(config["output_data_dir"], f"satellite_gs_ranking_at_{t}.txt")
        with open(output_file_path, "w") as file:
            file.write("Satellites ranked by gs:\n")
            ranked_satellites = sorted(satellite_usage, key=satellite_usage.get, reverse=True)
            for rank, sat in enumerate(ranked_satellites, start=1):
                file.write(f"Rank {rank}: Satellite {sat} connects {satellite_usage[sat]} ground stations\n")

        print("Satellite gs counts and rankings have been written to", output_file_path)

    with open(config["total_output_file_path"], "w") as file:
        file.write("Satellites ranked by gs:\n")
        ranked_satellites = sorted(satellite_ground_station_counts, key=satellite_ground_station_counts.get, reverse=True)
        for rank, sat in enumerate(ranked_satellites, start=1):
            file.write(f"Rank {rank}: Satellite {sat} connects {satellite_ground_station_counts[sat]} ground stations\n")

    print("Total satellite usage counts and rankings have been written to", config["total_output_file_path"])
