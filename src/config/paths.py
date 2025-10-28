"""Path configuration and utilities for output management."""
from datetime import datetime
from pathlib import Path
from typing import Tuple


# Base directories
BASE_DIR = Path(__file__).parent.parent.parent
OUTPUTS_DIR = BASE_DIR / "outputs"
SAMPLE_INPUTS_DIR = BASE_DIR / "sample_inputs"
DATA_DIR = BASE_DIR / "data"


def generate_run_directory(base_dir: Path = OUTPUTS_DIR) -> Tuple[str, Path, Path]:
    """
    Generate a timestamped run directory with reports and logs subdirectories.

    Args:
        base_dir: Base directory for outputs (default: OUTPUTS_DIR)

    Returns:
        Tuple of (timestamp_string, reports_dir_path, logs_dir_path)

    Example:
        >>> timestamp, reports_dir, logs_dir = generate_run_directory()
        >>> # Creates: outputs/run_20251028_143022/reports/
        >>> #          outputs/run_20251028_143022/logs/
    """
    # Generate timestamp
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")

    # Create run directory structure
    run_dir = base_dir / f"run_{timestamp}"
    reports_dir = run_dir / "reports"
    logs_dir = run_dir / "logs"

    # Create all directories
    reports_dir.mkdir(parents=True, exist_ok=True)
    logs_dir.mkdir(parents=True, exist_ok=True)

    return timestamp, reports_dir, logs_dir
