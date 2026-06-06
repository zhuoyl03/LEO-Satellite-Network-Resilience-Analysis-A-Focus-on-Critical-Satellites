"""Demand-coupled link load and stress utilities."""

from __future__ import annotations

from collections import defaultdict
from typing import Iterable

import networkx as nx

from .scenarios import Flow


def edge_key(u: int, v: int, graph: nx.Graph | None = None) -> tuple[int, int]:
    """Return a stable edge key, normalizing undirected graph edges."""

    if graph is not None and graph.is_directed():
        return (u, v)
    return tuple(sorted((u, v)))


def path_edges(path: list[int], graph: nx.Graph | None = None) -> list[tuple[int, int]]:
    """Return normalized edge keys for a path."""

    return [edge_key(u, v, graph) for u, v in zip(path[:-1], path[1:])]


def compute_link_load(paths: dict[str, list[int] | None], flows: Iterable[Flow], graph: nx.Graph) -> dict[tuple[int, int], float]:
    """Sum offered demand over every edge used by routed flows."""

    link_load: dict[tuple[int, int], float] = defaultdict(float)
    flow_by_id = {flow.flow_id: flow for flow in flows}
    for flow_id, path in paths.items():
        if not path:
            continue
        demand = flow_by_id[flow_id].demand_weight
        for edge in path_edges(path, graph):
            link_load[edge] += demand
    return dict(link_load)


def compute_link_stress(link_load: dict[tuple[int, int], float], link_capacity: float) -> dict[tuple[int, int], float]:
    """Convert demand load to stress using a controlled capacity parameter."""

    if link_capacity <= 0:
        raise ValueError("link_capacity must be positive")
    return {edge: load / link_capacity for edge, load in link_load.items()}
