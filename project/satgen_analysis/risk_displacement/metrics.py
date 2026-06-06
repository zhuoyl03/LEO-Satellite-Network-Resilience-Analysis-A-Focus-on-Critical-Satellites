"""Latency and aggregate metrics for risk displacement first-step runs."""

from __future__ import annotations

from statistics import mean

import networkx as nx

from .link_stress import path_edges
from .scenarios import Flow

SPEED_OF_LIGHT_M_PER_S = 299792458.0


def percentile(values: list[float], pct: float) -> float | None:
    """Return a simple nearest-rank percentile for small experiment outputs."""

    if not values:
        return None
    ordered = sorted(values)
    index = min(len(ordered) - 1, max(0, int(round((pct / 100.0) * (len(ordered) - 1)))))
    return ordered[index]


def path_length_m(graph: nx.Graph, path: list[int]) -> float:
    """Sum graph edge weights along a path."""

    return sum(float(graph[u][v]["weight"]) for u, v in zip(path[:-1], path[1:]))


def propagation_latency_ns(graph: nx.Graph, path: list[int]) -> float:
    """Round-trip propagation latency proxy from path length.

    This is not an ns-3 simulation. It uses ``2 * path_length / c``.
    """

    return 2.0 * path_length_m(graph, path) * 1e9 / SPEED_OF_LIGHT_M_PER_S


def congestion_adjusted_latency_ns(base_latency_ns: float, max_link_stress_on_path: float, beta: float = 0.5) -> float:
    """Apply a lightweight congestion proxy to propagation latency.

    ``congested = base * (1 + beta * max_path_stress)``. This is only a
    controlled sensitivity proxy, not real queueing or Starlink/Kuiper traffic.
    """

    return base_latency_ns * (1.0 + beta * max_link_stress_on_path)


def top_10_link_load_share(link_load: dict[tuple[int, int], float]) -> float:
    """Return fraction of total load carried by the ten busiest links."""

    total = sum(link_load.values())
    if total <= 0:
        return 0.0
    return sum(sorted(link_load.values(), reverse=True)[:10]) / total


def summarize_policy(
    scenario_name: str,
    traffic_model: str,
    seed: int,
    routing_policy: str,
    flows: list[Flow],
    paths: dict[str, list[int] | None],
    graph: nx.Graph,
    link_load: dict[tuple[int, int], float],
    link_stress: dict[tuple[int, int], float],
    beta: float,
) -> tuple[dict[str, object], list[dict[str, object]], list[dict[str, object]]]:
    """Build aggregate, per-flow, and per-link output rows."""

    flow_by_id = {flow.flow_id: flow for flow in flows}
    base_latencies: list[float] = []
    congested_latencies: list[float] = []
    path_rows: list[dict[str, object]] = []

    for flow in flows:
        path = paths.get(flow.flow_id)
        if not path:
            path_rows.append(_path_row(flow, routing_policy, False))
            continue

        length_m = path_length_m(graph, path)
        base_latency = propagation_latency_ns(graph, path)
        max_path_stress = max((link_stress.get(edge, 0.0) for edge in path_edges(path, graph)), default=0.0)
        congested_latency = congestion_adjusted_latency_ns(base_latency, max_path_stress, beta=beta)
        base_latencies.append(base_latency)
        congested_latencies.append(congested_latency)
        path_rows.append(
            _path_row(
                flow,
                routing_policy,
                True,
                path=path,
                path_length_m_value=length_m,
                base_latency_ns=base_latency,
                congested_latency_ns=congested_latency,
                max_link_stress_on_path=max_path_stress,
            )
        )

    reachable = len(base_latencies)
    stresses = list(link_stress.values())
    metrics_row = {
        "scenario_name": scenario_name,
        "traffic_model": traffic_model,
        "seed": seed,
        "routing_policy": routing_policy,
        "num_flows": len(flows),
        "reachable_flows": reachable,
        "unreachable_flows": len(flows) - reachable,
        "total_demand": sum(flow.demand_weight for flow in flows),
        "avg_base_latency_ns": mean(base_latencies) if base_latencies else None,
        "p95_base_latency_ns": percentile(base_latencies, 95),
        "avg_congested_latency_ns": mean(congested_latencies) if congested_latencies else None,
        "p95_congested_latency_ns": percentile(congested_latencies, 95),
        "max_link_stress": max(stresses) if stresses else 0.0,
        "avg_link_stress": mean(stresses) if stresses else 0.0,
        "num_links_over_capacity": sum(1 for stress in stresses if stress > 1.0),
        "top_10_link_load_share": top_10_link_load_share(link_load),
    }

    link_rows = [
        {
            "scenario_name": scenario_name,
            "traffic_model": traffic_model,
            "seed": seed,
            "routing_policy": routing_policy,
            "edge_u": edge[0],
            "edge_v": edge[1],
            "link_load": link_load.get(edge, 0.0),
            "link_stress": stress,
            "over_capacity": stress > 1.0,
        }
        for edge, stress in sorted(link_stress.items())
    ]
    return metrics_row, path_rows, link_rows


def _path_row(
    flow: Flow,
    routing_policy: str,
    reachable: bool,
    path: list[int] | None = None,
    path_length_m_value: float | None = None,
    base_latency_ns: float | None = None,
    congested_latency_ns: float | None = None,
    max_link_stress_on_path: float | None = None,
) -> dict[str, object]:
    return {
        "scenario_name": flow.scenario_name,
        "traffic_model": flow.traffic_model,
        "seed": flow.seed,
        "routing_policy": routing_policy,
        "flow_id": flow.flow_id,
        "src_gs": flow.src_gs,
        "dst_gs": flow.dst_gs,
        "src_city": flow.src_city,
        "dst_city": flow.dst_city,
        "demand_weight": flow.demand_weight,
        "reachable": reachable,
        "path_hops": len(path) - 1 if path else None,
        "path_length_m": path_length_m_value,
        "base_latency_ns": base_latency_ns,
        "congested_latency_ns": congested_latency_ns,
        "max_link_stress_on_path": max_link_stress_on_path,
        "path": "-".join(str(node) for node in path) if path else "",
    }
