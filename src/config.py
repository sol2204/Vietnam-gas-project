# src/config.py
from pathlib import Path
import yaml

# Locate project root (directory above /src/)
PROJECT_ROOT = Path(__file__).resolve().parents[1]


def load_config(path: Path = PROJECT_ROOT / "config" / "config.yaml") -> dict:
    """
    Load YAML config file and return as a dictionary.
    Also attaches absolute paths for convenience.
    """
    path = Path(path)

    if not path.exists():
        raise FileNotFoundError(f"Config file not found at: {path}")

    # Load YAML
    with open(path, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    # Add derived useful paths
    raw_dir = PROJECT_ROOT / cfg["data"]["raw_dir"]
    processed_dir = PROJECT_ROOT / cfg["data"]["processed_dir"]

    cfg["paths"] = {
        "root": PROJECT_ROOT,
        "raw": raw_dir,
        "processed": processed_dir,
        "gem_file": PROJECT_ROOT / cfg["data"]["gem_powerplants_file"],
        "cleaned_output": PROJECT_ROOT / cfg["output"]["cleaned_file"],
        "figures": PROJECT_ROOT / cfg["output"]["figures_dir"],
    }

    # Ensure data directories exist (optional but safe)
    raw_dir.mkdir(parents=True, exist_ok=True)
    processed_dir.mkdir(parents=True, exist_ok=True)
    (PROJECT_ROOT / cfg["output"]["figures_dir"]).mkdir(parents=True, exist_ok=True)

    return cfg
