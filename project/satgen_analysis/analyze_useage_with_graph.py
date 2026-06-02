import os
import pickle
import sys
from pathlib import Path

import networkx as nx

PROJECT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_DIR))
from config import DEFAULT_SATELLITE_DATA_NAME, PROJECT_NETWORKS_DIR, analysis_window_dir


DEFAULT_CONFIG = {
    "graph_directory": str(PROJECT_NETWORKS_DIR / DEFAULT_SATELLITE_DATA_NAME / "graph" / "delete_0"),
    "simulation_end_time_s": 200,
    "dynamic_state_update_interval_ms": 1000,
    "output_data_dir": str(analysis_window_dir(DEFAULT_SATELLITE_DATA_NAME) / "usage" / "satellite_usage_ranking"),
    "satellite_count": 784,
    "ground_station_count": 100,
}


def analyze_usage_with_graph(config=None):
    """Compute per-time-step satellite usage rankings from precomputed graph files."""
    config = dict(DEFAULT_CONFIG if config is None else config)
    simulation_end_time_ns = config["simulation_end_time_s"] * 1000 * 1000 * 1000
    dynamic_state_update_interval_ns = config["dynamic_state_update_interval_ms"] * 1000 * 1000

    total_satellite_usage = {sat: 0 for sat in range(config["satellite_count"])}
    os.makedirs(config["output_data_dir"], exist_ok=True)

    for t in range(0, simulation_end_time_ns, dynamic_state_update_interval_ns):
        print(f"Generating data for t={t} ns (= {t / 1e9} seconds)")
        output_file_path = os.path.join(config["output_data_dir"], f"satellite_usage_ranking_at_{t}.txt")
        graph_path = os.path.join(config["graph_directory"], f"graph_at_{t}.pkl")

        if not os.path.exists(graph_path):
            print(f"Graph file {graph_path} does not exist.")
            continue

        with open(graph_path, "rb") as f:
            graph = pickle.load(f)

        satellite_nodes = set(range(config["satellite_count"]))
        ground_station_nodes = set(range(config["satellite_count"], config["satellite_count"] + config["ground_station_count"]))
        satellite_usage = {sat: 0 for sat in satellite_nodes}

        for start_station in ground_station_nodes:
            for end_station in ground_station_nodes:
                if start_station == end_station:
                    continue
                try:
                    subgraph = graph.copy()
                    subgraph.remove_nodes_from([n for n in ground_station_nodes if n not in [start_station, end_station]])
                    path = nx.shortest_path(subgraph, source=start_station, target=end_station, weight="weight")
                    for node in path:
                        if node in satellite_nodes:
                            satellite_usage[node] += 1
                            total_satellite_usage[node] += 1
                except nx.NetworkXNoPath:
                    print(f"No path exists between station {start_station} and station {end_station}.")

        with open(output_file_path, "w") as file:
            file.write("Satellites ranked by usage:\n")
            ranked_satellites = sorted(satellite_usage, key=satellite_usage.get, reverse=True)
            for rank, sat in enumerate(ranked_satellites, start=1):
                file.write(f"Rank {rank}: Satellite {sat} used {satellite_usage[sat]} times\n")

        print("Satellite usage counts and rankings have been written to", output_file_path)

    total_output_file_path = os.path.join(config["output_data_dir"], "total_satellite_usage_ranking.txt")
    with open(total_output_file_path, "w") as file:
        file.write("Satellites ranked by usage:\n")
        ranked_satellites = sorted(total_satellite_usage, key=total_satellite_usage.get, reverse=True)
        for rank, sat in enumerate(ranked_satellites, start=1):
            file.write(f"Rank {rank}: Satellite {sat} used {total_satellite_usage[sat]} times\n")

    print("Total satellite usage counts and rankings have been written to", total_output_file_path)
