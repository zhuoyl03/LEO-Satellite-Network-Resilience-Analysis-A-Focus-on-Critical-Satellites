"""Representative routing policies for demand-coupled link-stress analysis."""

from __future__ import annotations

from itertools import islice

import networkx as nx

from .link_stress import compute_link_load, compute_link_stress, edge_key, path_edges
from .scenarios import Flow


def infer_satellite_count(graph: nx.Graph, num_ground_stations: int) -> int:
    """Infer the satellite node offset from graph size and fixed GS count."""

    if graph.number_of_nodes() <= num_ground_stations:
        raise ValueError("Graph has too few nodes to contain the fixed ground stations")
    return max(graph.nodes) + 1 - num_ground_stations


def graph_for_flow(graph: nx.Graph, satellite_count: int, num_ground_stations: int, flow: Flow) -> nx.Graph:
    """Copy graph and remove non-endpoint ground-station transit nodes."""

    src_node = satellite_count + flow.src_gs
    dst_node = satellite_count + flow.dst_gs
    if src_node not in graph:
        raise ValueError(f"Source ground-station node {src_node} is missing from graph")
    if dst_node not in graph:
        raise ValueError(f"Destination ground-station node {dst_node} is missing from graph")

    flow_graph = graph.copy()
    ground_nodes = range(satellite_count, satellite_count + num_ground_stations)
    flow_graph.remove_nodes_from([node for node in ground_nodes if node not in (src_node, dst_node)])
    return flow_graph


def shortest_path_for_flow(
    graph: nx.Graph,
    satellite_count: int,
    num_ground_stations: int,
    flow: Flow,
    weight="weight",
) -> list[int] | None:
    """Route one flow with NetworkX shortest path."""

    flow_graph = graph_for_flow(graph, satellite_count, num_ground_stations, flow)
    try:
        return nx.shortest_path(
            flow_graph,
            source=satellite_count + flow.src_gs,
            target=satellite_count + flow.dst_gs,
            weight=weight,
        )
    except (nx.NetworkXNoPath, nx.NodeNotFound):
        return None


def route_shortest_path(graph: nx.Graph, flows: list[Flow], num_ground_stations: int) -> dict[str, list[int] | None]:
    """Route all flows with the baseline shortest path policy."""

    satellite_count = infer_satellite_count(graph, num_ground_stations)
    return {
        flow.flow_id: shortest_path_for_flow(graph, satellite_count, num_ground_stations, flow, weight="weight")
        for flow in flows
    }


def route_stress_aware_two_pass(
    graph: nx.Graph,
    flows: list[Flow],
    num_ground_stations: int,
    link_capacity: float,
    alpha: float = 2.0,
) -> dict[str, list[int] | None]:
    """Route once by shortest path, then reroute using demand-induced stress."""

    first_paths = route_shortest_path(graph, flows, num_ground_stations)
    first_load = compute_link_load(first_paths, flows, graph)
    first_stress = compute_link_stress(first_load, link_capacity)
    satellite_count = infer_satellite_count(graph, num_ground_stations)

    def stress_weight(u: int, v: int, attrs: dict[str, float]) -> float:
        base = float(attrs.get("weight", 1.0))
        return base * (1.0 + alpha * first_stress.get(edge_key(u, v, graph), 0.0))

    return {
        flow.flow_id: shortest_path_for_flow(graph, satellite_count, num_ground_stations, flow, weight=stress_weight)
        for flow in flows
    }


def route_k_shortest_load_balancing(
    graph: nx.Graph,
    flows: list[Flow],
    num_ground_stations: int,
    link_capacity: float,
    k_paths: int = 3,
) -> dict[str, list[int] | None]:
    """Choose among k shortest paths using current max link stress."""

    satellite_count = infer_satellite_count(graph, num_ground_stations)
    paths: dict[str, list[int] | None] = {}
    current_load: dict[tuple[int, int], float] = {}

    for flow in flows:
        flow_graph = graph_for_flow(graph, satellite_count, num_ground_stations, flow)
        src = satellite_count + flow.src_gs
        dst = satellite_count + flow.dst_gs
        try:
            candidates = list(islice(nx.shortest_simple_paths(flow_graph, src, dst, weight="weight"), k_paths))
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            candidates = []

        if not candidates:
            path = shortest_path_for_flow(graph, satellite_count, num_ground_stations, flow, weight="weight")
        else:
            path = min(
                candidates,
                key=lambda candidate: (
                    max(
                        (current_load.get(edge, 0.0) + flow.demand_weight) / link_capacity
                        for edge in path_edges(candidate, graph)
                    ),
                    sum(float(graph[u][v]["weight"]) for u, v in zip(candidate[:-1], candidate[1:])),
                ),
            )

        paths[flow.flow_id] = path
        if path:
            for edge in path_edges(path, graph):
                current_load[edge] = current_load.get(edge, 0.0) + flow.demand_weight

    return paths


def route_flows(
    policy: str,
    graph: nx.Graph,
    flows: list[Flow],
    num_ground_stations: int,
    link_capacity: float,
    alpha: float = 2.0,
    k_paths: int = 3,
) -> dict[str, list[int] | None]:
    """Dispatch to a named routing policy."""

    if policy == "shortest_path":
        return route_shortest_path(graph, flows, num_ground_stations)
    if policy == "stress_aware_two_pass":
        return route_stress_aware_two_pass(graph, flows, num_ground_stations, link_capacity, alpha=alpha)
    if policy == "k_shortest_load_balancing":
        return route_k_shortest_load_balancing(graph, flows, num_ground_stations, link_capacity, k_paths=k_paths)
    raise ValueError(f"Unknown routing policy: {policy}")
