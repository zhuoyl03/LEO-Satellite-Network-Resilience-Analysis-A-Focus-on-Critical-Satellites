from satellite_networks.construct_graph import construct_graph
from satellite_networks.gen_path import gen_path
from satellite_networks.calculate_lat_lon import calculate_lat_lon
from satgen_analysis.analyze_rtt_with_graph import analyze_rtt_with_graph
import argparse
import csv
import json
import os
import pickle
from config import (
    DEFAULT_SATELLITE_DATA_NAME,
    PROJECT_ANALYSIS_DIR,
    PROJECT_NETWORKS_DIR,
    SATGENPY_DIR,
    analysis_window_dir,
    deletion_label,
    graph_dir,
    path_dir,
    paths_file,
    paper_network_dir,
    rtt_dir,
    usage_ranking_dir,
)

SPEED_OF_LIGHT_M_PER_S = 299792458.0


def run_analysis(
    satellite_data_name=DEFAULT_SATELLITE_DATA_NAME,
    satellite_count=784,
    ground_station_count=100,
    simulation_end_time_seconds=200,
    dynamic_state_update_interval_ms=1000,
    geodesic_distance_cutoff_km=500,
    deletion_counts=(50, 100),
):
    """Run the project satellite deletion, path generation, and RTT analysis pipeline."""
    simulation_end_time_ns = int(simulation_end_time_seconds * 1e9)
    dynamic_state_update_interval_ns = int(dynamic_state_update_interval_ms * 1e6)

    usage_ranking_file = usage_ranking_dir(
        satellite_data_name, 0, dynamic_state_update_interval_ms, simulation_end_time_seconds
    ) / "total_satellite_usage_ranking.txt"
    satellite_network_data_dir = paper_network_dir(satellite_data_name)

    satgenpy_dir = str(SATGENPY_DIR) + os.sep
    output_rtt_data_dir = PROJECT_ANALYSIS_DIR

    latlon_output_path = PROJECT_NETWORKS_DIR / satellite_data_name / "satellite_lat_lon"
    calculate_lat_lon(
        satellite_network_data_dir,
        latlon_output_path,
        simulation_end_time_ns,
        dynamic_state_update_interval_ns,
    )

    for num_deletions in deletion_counts:
        graph_data_path = graph_dir(satellite_data_name, num_deletions)
        usage_output_dir = usage_ranking_dir(
            satellite_data_name, num_deletions, dynamic_state_update_interval_ms, simulation_end_time_seconds
        )
        path_output_dir = path_dir(satellite_data_name, num_deletions)
        generated_paths_file = paths_file(satellite_data_name, num_deletions)

        construct_graph(
            graph_data_path,
            usage_ranking_file,
            satellite_network_data_dir,
            num_deletions,
            simulation_end_time_ns,
            dynamic_state_update_interval_ns,
        )
        gen_path(
            graph_data_path,
            simulation_end_time_ns,
            dynamic_state_update_interval_ns,
            usage_output_dir,
            satellite_count,
            ground_station_count,
            satellite_network_data_dir,
            path_output_dir,
        )
        analyze_rtt_with_graph(
            simulation_end_time_ns,
            dynamic_state_update_interval_ns,
            satellite_network_data_dir,
            satgenpy_dir,
            output_rtt_data_dir,
            f"rtt_{deletion_label(num_deletions)}",
            generated_paths_file,
            graph_data_path,
            geodesic_distance_cutoff_km,
        )


def path_length_m(graph, path):
    length = 0.0
    for src, dst in zip(path[:-1], path[1:]):
        length += float(graph[src][dst]["weight"])
    return length


def run_smoke_check(
    satellite_data_name=DEFAULT_SATELLITE_DATA_NAME,
    num_deletions=50,
    simulation_end_time_seconds=2,
    dynamic_state_update_interval_ms=1000,
):
    """Validate graph -> paths -> RTT output connectivity using existing project data."""
    simulation_end_time_ns = int(simulation_end_time_seconds * 1e9)
    dynamic_state_update_interval_ns = int(dynamic_state_update_interval_ms * 1e6)
    graph_data_path = graph_dir(satellite_data_name, num_deletions)
    generated_paths_file = paths_file(satellite_data_name, num_deletions)
    smoke_rtt_dir = rtt_dir(
        satellite_data_name,
        num_deletions,
        dynamic_state_update_interval_ms,
        simulation_end_time_seconds,
    )
    data_dir = smoke_rtt_dir / "data"
    data_dir.mkdir(parents=True, exist_ok=True)

    if not graph_data_path.exists():
        raise FileNotFoundError(f"Missing graph directory: {graph_data_path}")
    if not generated_paths_file.exists():
        raise FileNotFoundError(f"Missing paths file: {generated_paths_file}")

    with open(generated_paths_file, "rb") as f:
        paths_by_time = pickle.load(f)

    rows = []
    for t in range(0, simulation_end_time_ns, dynamic_state_update_interval_ns):
        graph_file = graph_data_path / f"graph_at_{t}.pkl"
        if not graph_file.exists():
            raise FileNotFoundError(f"Missing graph file: {graph_file}")
        if t not in paths_by_time:
            raise KeyError(f"Missing paths for t={t} in {generated_paths_file}")

        with open(graph_file, "rb") as f:
            graph = pickle.load(f)

        rtts = []
        unreachable = 0
        for pair, path in paths_by_time[t].items():
            if not path:
                unreachable += 1
                continue
            try:
                rtt_ns = 2 * path_length_m(graph, path) * 1e9 / SPEED_OF_LIGHT_M_PER_S
                rtts.append(rtt_ns)
            except KeyError:
                unreachable += 1

        avg_rtt_ns = sum(rtts) / len(rtts) if rtts else None
        rows.append(
            {
                "time_ns": t,
                "num_pairs": len(paths_by_time[t]),
                "reachable_pairs": len(rtts),
                "unreachable_pairs": unreachable,
                "avg_rtt_ns": avg_rtt_ns,
                "max_rtt_ns": max(rtts) if rtts else None,
            }
        )

    summary_path = data_dir / "smoke_rtt_summary.csv"
    with open(summary_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)

    manifest = {
        "graph_dir": str(graph_data_path),
        "paths_file": str(generated_paths_file),
        "rtt_dir": str(smoke_rtt_dir),
        "summary_csv": str(summary_path),
        "time_steps": len(rows),
    }
    manifest_path = smoke_rtt_dir / "smoke_manifest.json"
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)

    print("Smoke run completed.")
    print(f"graph_dir: {graph_data_path}")
    print(f"paths_file: {generated_paths_file}")
    print(f"rtt_dir: {smoke_rtt_dir}")
    print(f"summary_csv: {summary_path}")
    return manifest


def parse_args():
    parser = argparse.ArgumentParser(description="Run project satellite analysis pipeline.")
    parser.add_argument("--smoke", action="store_true", help="Run a 2-second graph/path/RTT connectivity smoke check.")
    parser.add_argument("--simulation_end_time_seconds", type=int, default=200)
    parser.add_argument("--dynamic_state_update_interval_ms", type=int, default=1000)
    parser.add_argument("--deletion_counts", type=int, nargs="+", default=[50, 100])
    return parser.parse_args()


def main():
    args = parse_args()
    if args.smoke:
        run_smoke_check(
            simulation_end_time_seconds=2,
            dynamic_state_update_interval_ms=args.dynamic_state_update_interval_ms,
            num_deletions=args.deletion_counts[0],
        )
        return
    run_analysis(
        simulation_end_time_seconds=args.simulation_end_time_seconds,
        dynamic_state_update_interval_ms=args.dynamic_state_update_interval_ms,
        deletion_counts=tuple(args.deletion_counts),
    )


if __name__ == "__main__":
    main()
