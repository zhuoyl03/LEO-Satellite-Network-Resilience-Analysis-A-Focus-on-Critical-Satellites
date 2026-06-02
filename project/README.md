# LEO Satellite Resilience Analysis

This directory contains the project code for analyzing critical satellites in LEO networks using Hypatia-generated network states. The current codebase focuses on the original resilience pipeline: construct graph snapshots, remove high-usage satellites, recompute paths, and analyze RTT/connectivity degradation.

## Structure

- `satellites_analysis.py` is the main entry point.
- `config.py` centralizes relative paths and dataset names.
- `satellite_networks/` contains graph construction, path generation, deletion, and satellite/ground-station analysis helpers.
- `satgen_analysis/` contains RTT, path-change, and usage analysis helpers.
- `figures/` contains plotting scripts.

Generated graph data, paths, analysis outputs, plots, and videos are intentionally ignored by git because they can be large.

## Environment

This project expects the Hypatia repository to be available one directory above this folder and a working `hypatia` conda environment:

```bash
conda activate hypatia
cd /home/leo/hypatia
```

The Hypatia build and tests were verified with:

```bash
conda run -n hypatia bash hypatia_build.sh
conda run -n hypatia bash hypatia_run_tests.sh
```

## Smoke Test

Use the smoke test to verify the graph -> path -> RTT analysis chain on a 2-second slice of existing local generated data:

```bash
conda run -n hypatia python project/satellites_analysis.py --smoke --deletion_counts 50
```

Expected outputs are written under:

```text
project/satgen_analysis/<dataset>/1000ms_for_2s/rtt_delete_50/
```

## Full Pipeline

The full default pipeline runs the configured deletion scenarios over the default 200-second window:

```bash
conda run -n hypatia python project/satellites_analysis.py
```

You can override the time window and deletion counts:

```bash
conda run -n hypatia python project/satellites_analysis.py \
  --simulation_end_time_seconds 2 \
  --deletion_counts 50
```

## Data Policy

The following are not committed to git:

- `satellite_networks/gen_data/`
- `satgen_analysis/<dataset>/`
- generated plots, PDFs, videos, and intermediate files under `figures/`

If another machine needs to reproduce results, regenerate these outputs from Hypatia or transfer the generated data separately.

## Notes

The current code is a cleaned baseline for passive resilience analysis. The next research step is to build a risk-aware SafeRoute-LEO prototype on top of this baseline, with expert routing policies, counterfactual labels, and budgeted deferral.
