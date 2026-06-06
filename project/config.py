"""Shared relative paths for the project experiments.

All paths are derived from this file location so the project can move between
machines without editing absolute user-specific paths.
"""

from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parent
REPO_ROOT = PROJECT_DIR.parent

SATGENPY_DIR = REPO_ROOT / "satgenpy"
PAPER_DIR = REPO_ROOT / "paper"
PAPER_NETWORK_STATE_DIR = PAPER_DIR / "satellite_networks_state"
PAPER_GENERATED_NETWORKS_DIR = PAPER_NETWORK_STATE_DIR / "gen_data"
PAPER_INPUT_DATA_DIR = PAPER_NETWORK_STATE_DIR / "input_data"

PROJECT_NETWORKS_DIR = PROJECT_DIR / "satellite_networks" / "gen_data"
PROJECT_ANALYSIS_DIR = PROJECT_DIR / "satgen_analysis"
PROJECT_RESULT_DIR = PROJECT_DIR / "result"
PROJECT_RESULT_GENERATED_DIR = PROJECT_RESULT_DIR / "generated"
PROJECT_PLOT_SCRIPTS_DIR = PROJECT_RESULT_DIR / "plot_scripts"
PROJECT_FIGURES_DIR = PROJECT_RESULT_GENERATED_DIR
PROJECT_OUTPUTS_DIR = PROJECT_DIR / "outputs"
PROJECT_PLOTS_DIR = PROJECT_ANALYSIS_DIR / "plots"

STARLINK_DATA_NAME = "starlink_550_isls_plus_grid_ground_stations_top_100_algorithm_free_one_only_over_isls"
KUIPER_DATA_NAME = "kuiper_590_isls_plus_grid_ground_stations_top_100_algorithm_free_one_only_over_isls"
LEGACY_STARLINK_SHELL_NAME = "72_22_53_550_starlinkshell1"

DEFAULT_SATELLITE_DATA_NAME = KUIPER_DATA_NAME
DEFAULT_GROUND_STATIONS_FILE = (
    PAPER_INPUT_DATA_DIR / "ground_stations_cities_sorted_by_estimated_2025_pop_top_100.basic.txt"
)


def paper_network_dir(data_name: str) -> Path:
    return PAPER_GENERATED_NETWORKS_DIR / data_name


def project_network_dir(data_name: str) -> Path:
    return PROJECT_NETWORKS_DIR / data_name


def analysis_window_dir(data_name: str, interval_ms: int = 1000, duration_s: int = 200) -> Path:
    return PROJECT_ANALYSIS_DIR / data_name / f"{interval_ms}ms_for_{duration_s}s"


def legacy_starlink_graph_dir() -> Path:
    return project_network_dir(LEGACY_STARLINK_SHELL_NAME) / "graph" / f"graph_{LEGACY_STARLINK_SHELL_NAME}"


def deletion_label(num_deletions: int) -> str:
    return f"delete_{num_deletions}"


def graph_dir(data_name: str, num_deletions: int) -> Path:
    return project_network_dir(data_name) / "graph" / deletion_label(num_deletions)


def path_dir(data_name: str, num_deletions: int) -> Path:
    return project_network_dir(data_name) / "path" / deletion_label(num_deletions)


def paths_file(data_name: str, num_deletions: int) -> Path:
    return path_dir(data_name, num_deletions) / "all_paths.pkl"


def usage_ranking_dir(data_name: str, num_deletions: int, interval_ms: int = 1000, duration_s: int = 200) -> Path:
    return analysis_window_dir(data_name, interval_ms, duration_s) / "satellite_usage_ranking" / deletion_label(num_deletions)


def rtt_dir(data_name: str, num_deletions: int, interval_ms: int = 1000, duration_s: int = 200) -> Path:
    return analysis_window_dir(data_name, interval_ms, duration_s) / f"rtt_{deletion_label(num_deletions)}"
