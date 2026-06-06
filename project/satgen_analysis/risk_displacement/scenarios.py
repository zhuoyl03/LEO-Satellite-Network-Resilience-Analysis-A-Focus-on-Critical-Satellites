"""Ground-station loading and flow data structures for risk displacement runs."""

from __future__ import annotations

import csv
import warnings
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


@dataclass(frozen=True)
class GroundStation:
    """Fixed ground-station metadata used by traffic scenarios."""

    gid: int
    name: str
    latitude: float
    longitude: float
    population: float | None = None
    region: str | None = None


@dataclass(frozen=True)
class Flow:
    """Offered-load flow between two fixed ground stations."""

    scenario_name: str
    traffic_model: str
    seed: int
    flow_id: str
    src_gs: int
    dst_gs: int
    src_city: str | None
    dst_city: str | None
    demand_weight: float


def load_ground_stations(path: Path) -> tuple[list[GroundStation], bool]:
    """Load Hypatia basic ground-station rows.

    The current top-100 file has rows like:
    ``gid,name,latitude,longitude,elevation``. It does not carry population, so
    this loader warns once and returns ``population_available=False``.
    """

    if not path.exists():
        raise FileNotFoundError(f"Missing fixed top-100 ground station file: {path}")

    stations: list[GroundStation] = []
    population_available = False
    with open(path, newline="") as f:
        reader = csv.reader(f)
        for row in reader:
            if not row or len(row) < 4:
                continue
            try:
                gid = int(row[0])
                name = row[1] if row[1] else f"gs_{gid}"
                latitude = float(row[2])
                longitude = float(row[3])
            except ValueError as exc:
                raise ValueError(f"Invalid ground station row in {path}: {row}") from exc

            population = None
            if len(row) >= 6:
                try:
                    population = float(row[5])
                    population_available = True
                except ValueError:
                    population = None

            stations.append(
                GroundStation(
                    gid=gid,
                    name=name,
                    latitude=latitude,
                    longitude=longitude,
                    population=population,
                    region=infer_region(latitude, longitude),
                )
            )

    if not stations:
        raise ValueError(f"No ground stations loaded from {path}")
    if not population_available:
        warnings.warn(
            "Population is unavailable in the current ground station file; "
            "using uniform population weights.",
            RuntimeWarning,
            stacklevel=2,
        )
    return stations, population_available


def infer_region(latitude: float, longitude: float) -> str:
    """Assign a coarse region from latitude/longitude."""

    if -170 <= longitude <= -30 and latitude >= 5:
        return "North America"
    if -30 <= longitude <= 60 and latitude >= 35:
        return "Europe"
    if 95 <= longitude <= 150 and latitude >= 10:
        return "East Asia"
    if 60 < longitude < 95 and latitude >= 5:
        return "South Asia"
    if -90 <= longitude <= -30 and latitude < 15:
        return "Latin America"
    if -20 <= longitude <= 55 and latitude < 35:
        return "Africa"
    if 110 <= longitude <= 180 and latitude < 0:
        return "Oceania"
    return "Other"


def population_or_uniform(station: GroundStation) -> float:
    """Return population when available, otherwise a uniform weight."""

    if station.population is None or station.population <= 0:
        return 1.0
    return station.population


def flows_to_rows(flows: Iterable[Flow]) -> list[dict[str, object]]:
    """Serialize flows for CSV output."""

    return [
        {
            "scenario_name": flow.scenario_name,
            "traffic_model": flow.traffic_model,
            "seed": flow.seed,
            "flow_id": flow.flow_id,
            "src_gs": flow.src_gs,
            "dst_gs": flow.dst_gs,
            "src_city": flow.src_city,
            "dst_city": flow.dst_city,
            "demand_weight": flow.demand_weight,
        }
        for flow in flows
    ]
