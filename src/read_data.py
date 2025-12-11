from pathlib import Path
import pandas as pd 

from .config import load_config



def _read_gem_file(path: Path) -> pd.DataFrame:
    """Read GEM file into a pandas DataFrame."""

    suffix = path.suffix

    if suffix in [".xlsx", ".xls"]:
        return pd.read_excel(path)

    elif suffix in [".csv"]:
        return pd.read_csv(path)
    else:
        raise ValueError(f"Unsupported file format for GEM fiel: {suffix}")


def load_raw_gem_data() -> pd.DataFrame:
    """Load raw GEM data from file."""

    cfg = load_config()
    path = cfg["paths"]["gem_file"]

    if not path.exists():
        raise FileNotFoundError(f"GEM file not found at: {path}")


    df = _read_gem_file(path)
    return df


def _read_population_density_file(path: Path) -> pd.DataFrame:
    """Read population density file into a pandas DataFrame."""
    
    suffix = path.suffix
    if suffix in [".csv"]:
        return pd.read_csv(path)
    else:
        raise ValueError(f"Unsupported file format for population density file: {suffix}")


def load_population_density_data() -> pd.DataFrame:
    """Load population density data from file."""
    cfg = load_config()
    path = cfg["paths"]["population_density_file"]
    if not path.exists():
        raise FileNotFoundError(f"Population density file not found at: {path}")
    df = _read_population_density_file(path)
    breakpoint()
    return df


# if __name__ == "__main__":
#     df = load_population_density_data()







