"""Repository-level wrapper for project risk displacement first-step analysis."""

import sys
from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parent / "project"
sys.path.insert(0, str(PROJECT_DIR))

from satgen_analysis.risk_displacement.run_first_step import main


if __name__ == "__main__":
    main()
