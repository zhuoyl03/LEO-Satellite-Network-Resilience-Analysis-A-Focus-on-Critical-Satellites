import os
import pickle
import sys
from pathlib import Path

import networkx as nx
import numpy as np

PROJECT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_DIR))
from config import PROJECT_DIR as PROJECT_ROOT_DIR, legacy_starlink_graph_dir


def read_satellite_usage_indices(usage_file, limit=100):
    """Read satellite IDs from a legacy usage ranking text file."""
    satellite_indices = []
    with open(usage_file, "r", encoding="utf-8") as file:
        for line in file:
            if len(satellite_indices) >= limit:
                break
            parts = line.split()
            if len(parts) >= 4 and parts[3].isdigit():
                satellite_indices.append(int(parts[3]))
    return satellite_indices


def analyze_important_node_deletion(
    graph_directory=None,
    usage_file=None,
    output_file=None,
    satellite_count=1583,
    ground_station_count=101,
    num_delete_nodes=10,
    max_graphs=3,
):
    """Compare path lengths before and after removing high-usage satellites."""
    graph_directory = Path(graph_directory or legacy_starlink_graph_dir())
    usage_file = Path(usage_file or PROJECT_ROOT_DIR / "sat_usage.txt")
    output_file = Path(output_file or PROJECT_ROOT_DIR / "important_node_delete_weighted.txt")

    graph_files = sorted(f for f in os.listdir(graph_directory) if f.endswith(".pkl"))
    graphs = []
    for filename in graph_files:
        with open(graph_directory / filename, "rb") as f:
            graphs.append(pickle.load(f))

    satellite_indices = read_satellite_usage_indices(usage_file)
    print(f"Satellite usage list read complete. top 10: {satellite_indices[:10]}")

    ground_station_nodes = list(range(satellite_count, satellite_count + ground_station_count))
    gs_num = len(ground_station_nodes)
    hop_list = np.zeros((len(graphs), int(gs_num * (gs_num - 1) / 2), 2))
    remove_node_list = satellite_indices[:num_delete_nodes]

    with open(output_file, "w", encoding="utf-8") as file:
        file.write(f"top {num_delete_nodes} node deleted\n")
        for i, graph in enumerate(graphs[:max_graphs]):
            deleted_graph = graph.copy()
            deleted_graph.remove_nodes_from(remove_node_list)
            k = 0
            gs_list = ground_station_nodes.copy()
            for start_station in ground_station_nodes:
                if not gs_list:
                    break
                gs_list.pop(0)
                for end_station in gs_list:
                    baseline_graph = graph.copy()
                    baseline_graph.remove_nodes_from(
                        [n for n in ground_station_nodes if n not in [start_station, end_station]]
                    )

                    try:
                        hop_list[i, k, 0] = nx.shortest_path_length(
                            deleted_graph, source=start_station, target=end_station, weight="weight"
                        )
                    except nx.NetworkXNoPath:
                        hop_list[i, k, 0] = -1

                    try:
                        hop_list[i, k, 1] = nx.shortest_path_length(
                            baseline_graph, source=start_station, target=end_station, weight="weight"
                        )
                    except nx.NetworkXNoPath:
                        hop_list[i, k, 1] = -1

                    file.write(
                        f"time: {i} ,start_gs: {start_station} ,end_gs: {end_station} "
                        f",before_delete: {hop_list[i, k, 0]} ,after_delete: {hop_list[i, k, 1]}\n"
                    )
                    k += 1
                print(f"time:{i}, start_node:{start_station}")

    return hop_list
