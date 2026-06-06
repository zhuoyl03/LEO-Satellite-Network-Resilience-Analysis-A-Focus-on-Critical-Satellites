"""Traffic matrix generators over a fixed top-100 ground-station set."""

from __future__ import annotations

import math
import random
from statistics import median

from .scenarios import Flow, GroundStation, population_or_uniform

EARTH_RADIUS_KM = 6371.0088


def haversine_km(a: GroundStation, b: GroundStation) -> float:
    """Return great-circle distance between two ground stations in kilometers."""

    lat1 = math.radians(a.latitude)
    lat2 = math.radians(b.latitude)
    dlat = lat2 - lat1
    dlon = math.radians(b.longitude - a.longitude)
    h = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    return 2 * EARTH_RADIUS_KM * math.asin(min(1.0, math.sqrt(h)))


def normalize_to_median_one(values: list[float]) -> list[float]:
    """Scale positive demand values so their median is 1.0."""

    if not values:
        return values
    med = median(values)
    if med <= 0:
        return [1.0 for _ in values]
    return [value / med for value in values]


def random_pairs(stations: list[GroundStation], num_pairs: int, seed: int) -> list[tuple[GroundStation, GroundStation]]:
    """Generate deterministic random source/destination pairs."""

    rng = random.Random(seed)
    if len(stations) < 2:
        raise ValueError("At least two ground stations are required")

    pairs: list[tuple[GroundStation, GroundStation]] = []
    shuffled = stations[:]
    while len(pairs) < num_pairs:
        rng.shuffle(shuffled)
        for idx in range(0, len(shuffled) - 1, 2):
            if len(pairs) >= num_pairs:
                break
            pairs.append((shuffled[idx], shuffled[idx + 1]))
    return pairs


def build_flows(
    traffic_model: str,
    seed: int,
    pairs: list[tuple[GroundStation, GroundStation]],
    demands: list[float],
    reciprocal: bool,
) -> list[Flow]:
    """Create directed flows from pairs and demand weights."""

    scenario_name = f"{traffic_model}_seed_{seed}"
    flows: list[Flow] = []
    for idx, ((src, dst), demand) in enumerate(zip(pairs, demands)):
        flow_id = f"{scenario_name}_flow_{idx}"
        flows.append(
            Flow(scenario_name, traffic_model, seed, flow_id, src.gid, dst.gid, src.name, dst.name, float(demand))
        )
        if reciprocal:
            flows.append(
                Flow(
                    scenario_name,
                    traffic_model,
                    seed,
                    f"{flow_id}_reverse",
                    dst.gid,
                    src.gid,
                    dst.name,
                    src.name,
                    float(demand),
                )
            )
    return flows


def random_permutation_equal(
    stations: list[GroundStation],
    seed: int,
    num_pairs: int,
    reciprocal: bool,
) -> list[Flow]:
    """Pair fixed ground stations randomly with equal offered demand."""

    pairs = random_pairs(stations, num_pairs, seed)
    return build_flows("random_permutation_equal", seed, pairs, [1.0] * len(pairs), reciprocal)


def population_weighted(
    stations: list[GroundStation],
    seed: int,
    num_pairs: int,
    reciprocal: bool,
) -> list[Flow]:
    """Pair fixed ground stations and weight demand by sqrt(pop_src * pop_dst)."""

    pairs = random_pairs(stations, num_pairs, seed)
    raw = [math.sqrt(population_or_uniform(src) * population_or_uniform(dst)) for src, dst in pairs]
    return build_flows("population_weighted", seed, pairs, normalize_to_median_one(raw), reciprocal)


def gravity_model(
    stations: list[GroundStation],
    seed: int,
    num_pairs: int,
    reciprocal: bool,
    beta: float = 1.0,
) -> list[Flow]:
    """Generate random pairs with gravity-style offered demand."""

    pairs = random_pairs(stations, num_pairs, seed)
    raw = []
    for src, dst in pairs:
        distance = max(haversine_km(src, dst), 1.0)
        raw.append(population_or_uniform(src) * population_or_uniform(dst) / (distance**beta))
    return build_flows("gravity_model", seed, pairs, normalize_to_median_one(raw), reciprocal)


def regional_hotspot(
    stations: list[GroundStation],
    seed: int,
    num_pairs: int,
    reciprocal: bool,
    hotspot_multiplier: float = 3.0,
) -> list[Flow]:
    """Increase demand on selected coarse inter-region corridors."""

    pairs = random_pairs(stations, num_pairs, seed)
    corridors = {
        frozenset(("North America", "Europe")),
        frozenset(("East Asia", "North America")),
        frozenset(("Europe", "East Asia")),
    }
    demands = []
    for src, dst in pairs:
        pair_region = frozenset((src.region or "Other", dst.region or "Other"))
        demands.append(hotspot_multiplier if pair_region in corridors else 1.0)
    return build_flows("regional_hotspot", seed, pairs, demands, reciprocal)


def generate_flows(
    model: str,
    stations: list[GroundStation],
    seed: int,
    num_pairs: int,
    reciprocal: bool,
    gravity_beta: float = 1.0,
    hotspot_multiplier: float = 3.0,
) -> list[Flow]:
    """Dispatch to a named traffic model."""

    if model == "random_permutation_equal":
        return random_permutation_equal(stations, seed, num_pairs, reciprocal)
    if model == "population_weighted":
        return population_weighted(stations, seed, num_pairs, reciprocal)
    if model == "gravity_model":
        return gravity_model(stations, seed, num_pairs, reciprocal, beta=gravity_beta)
    if model == "regional_hotspot":
        return regional_hotspot(stations, seed, num_pairs, reciprocal, hotspot_multiplier=hotspot_multiplier)
    raise ValueError(f"Unknown traffic model: {model}")
