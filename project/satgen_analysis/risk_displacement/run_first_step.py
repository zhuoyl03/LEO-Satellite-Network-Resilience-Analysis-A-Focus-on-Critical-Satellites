"""CLI orchestration for first-step risk displacement analysis."""

from __future__ import annotations

import argparse
import csv
import json
import pickle
from pathlib import Path

import networkx as nx

from config import DEFAULT_GROUND_STATIONS_FILE, DEFAULT_SATELLITE_DATA_NAME, PROJECT_OUTPUTS_DIR, graph_dir

from .link_stress import compute_link_load, compute_link_stress
from .metrics import summarize_policy
from .routing_policies import route_flows
from .scenarios import flows_to_rows, load_ground_stations
from .traffic_models import generate_flows

DEFAULT_TRAFFIC_MODELS = [
    "random_permutation_equal",
    "population_weighted",
    "gravity_model",
    "regional_hotspot",
]
DEFAULT_ROUTING_POLICIES = [
    "shortest_path",
    "stress_aware_two_pass",
    "k_shortest_load_balancing",
]


def default_graph_path() -> Path:
    """Return the representative baseline graph snapshot."""

    return graph_dir(DEFAULT_SATELLITE_DATA_NAME, 0) / "graph_at_0.pkl"


def load_graph_snapshot(path: Path) -> nx.Graph:
    """Load and validate a NetworkX graph pickle."""

    if not path.exists():
        raise FileNotFoundError(
            f"Missing representative graph snapshot: {path}. "
            "Run the baseline graph generation first or pass --graph_path."
        )
    with open(path, "rb") as f:
        graph = pickle.load(f)
    if not isinstance(graph, nx.Graph):
        raise TypeError(f"Expected a NetworkX graph in {path}, got {type(graph)}")
    return graph


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    """Write dictionaries to CSV, creating parent directories."""

    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("")
        return
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def run_first_step(
    traffic_models: list[str],
    num_seeds: int,
    num_pairs: int,
    reciprocal: bool,
    routing_policies: list[str],
    link_capacity: float,
    alpha: float,
    beta: float,
    k_paths: int,
    graph_path: Path | None = None,
    ground_stations_file: Path = DEFAULT_GROUND_STATIONS_FILE,
    output_dir: Path | None = None,
) -> dict[str, object]:
    """Run traffic scenario generation, routing, link stress, and metrics."""

    output_dir = output_dir or PROJECT_OUTPUTS_DIR / "risk_displacement"
    graph_path = graph_path or default_graph_path()

    stations, population_available = load_ground_stations(ground_stations_file)
    graph = load_graph_snapshot(graph_path)

    all_flows = []
    scenario_manifest = {
        "ground_stations_file": str(ground_stations_file),
        "num_ground_stations": len(stations),
        "population_available": population_available,
        "traffic_models": traffic_models,
        "num_seeds": num_seeds,
        "num_pairs": num_pairs,
        "reciprocal": reciprocal,
    }

    flows_by_scenario: dict[str, list] = {}
    for model in traffic_models:
        for seed in range(num_seeds):
            flows = generate_flows(model, stations, seed, num_pairs, reciprocal)
            if flows:
                flows_by_scenario[flows[0].scenario_name] = flows
                all_flows.extend(flows)

    write_csv(output_dir / "flows_by_scenario.csv", flows_to_rows(all_flows))
    (output_dir / "traffic_scenario_manifest.json").write_text(json.dumps(scenario_manifest, indent=2))

    metrics_rows: list[dict[str, object]] = []
    path_rows: list[dict[str, object]] = []
    link_rows: list[dict[str, object]] = []

    for scenario_name, flows in flows_by_scenario.items():
        traffic_model = flows[0].traffic_model
        seed = flows[0].seed
        for policy in routing_policies:
            paths = route_flows(
                policy,
                graph,
                flows,
                num_ground_stations=len(stations),
                link_capacity=link_capacity,
                alpha=alpha,
                k_paths=k_paths,
            )
            link_load = compute_link_load(paths, flows, graph)
            link_stress = compute_link_stress(link_load, link_capacity)
            metrics_row, scenario_path_rows, scenario_link_rows = summarize_policy(
                scenario_name,
                traffic_model,
                seed,
                policy,
                flows,
                paths,
                graph,
                link_load,
                link_stress,
                beta,
            )
            metrics_rows.append(metrics_row)
            path_rows.extend(scenario_path_rows)
            link_rows.extend(scenario_link_rows)

    write_csv(output_dir / "per_policy_scenario_metrics.csv", metrics_rows)
    write_csv(output_dir / "path_summary_by_policy.csv", path_rows)
    write_csv(output_dir / "link_stress_by_policy.csv", link_rows)

    manifest = {
        "graph_path": str(graph_path),
        "output_dir": str(output_dir),
        "routing_policies": routing_policies,
        "link_capacity": link_capacity,
        "alpha": alpha,
        "beta": beta,
        "k_paths": k_paths,
        "outputs": [
            "flows_by_scenario.csv",
            "traffic_scenario_manifest.json",
            "per_policy_scenario_metrics.csv",
            "path_summary_by_policy.csv",
            "link_stress_by_policy.csv",
            "first_step_manifest.json",
        ],
    }
    (output_dir / "first_step_manifest.json").write_text(json.dumps(manifest, indent=2))
    print_summary(metrics_rows)
    return manifest


def print_summary(rows: list[dict[str, object]]) -> None:
    """Print a concise scenario/policy summary table."""

    print(
        "scenario, policy, avg congested latency ns, "
        "p95 congested latency ns, max link stress, links over capacity"
    )
    for row in rows:
        print(
            f"{row['scenario_name']}, {row['routing_policy']}, "
            f"{row['avg_congested_latency_ns']}, {row['p95_congested_latency_ns']}, "
            f"{row['max_link_stress']}, {row['num_links_over_capacity']}"
        )


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run first-step risk displacement analysis.")
    parser.add_argument("--traffic_models", nargs="+", default=DEFAULT_TRAFFIC_MODELS)
    parser.add_argument("--num_seeds", type=int, default=3)
    parser.add_argument("--num_pairs", type=int, default=50)
    parser.add_argument("--reciprocal", action="store_true")
    parser.add_argument("--routing_policies", nargs="+", default=DEFAULT_ROUTING_POLICIES)
    parser.add_argument("--link_capacity", type=float, default=10.0)
    parser.add_argument("--alpha", type=float, default=2.0)
    parser.add_argument("--beta", type=float, default=0.5)
    parser.add_argument("--k_paths", type=int, default=3)
    parser.add_argument("--graph_path", type=Path, default=None)
    parser.add_argument("--ground_stations_file", type=Path, default=DEFAULT_GROUND_STATIONS_FILE)
    parser.add_argument("--output_dir", type=Path, default=PROJECT_OUTPUTS_DIR / "risk_displacement")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> dict[str, object]:
    args = parse_args(argv)
    return run_first_step(
        traffic_models=args.traffic_models,
        num_seeds=args.num_seeds,
        num_pairs=args.num_pairs,
        reciprocal=args.reciprocal,
        routing_policies=args.routing_policies,
        link_capacity=args.link_capacity,
        alpha=args.alpha,
        beta=args.beta,
        k_paths=args.k_paths,
        graph_path=args.graph_path,
        ground_stations_file=args.ground_stations_file,
        output_dir=args.output_dir,
    )
