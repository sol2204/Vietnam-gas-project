# src/clean_data.py

import pandas as pd
from .config import load_config


def clean_gas_plant_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean and standardise the GEM gas plant dataset.

    Steps:
      - Select only required columns (from config.yaml)
      - Rename them to snake_case
      - Convert capacity and years to numeric
      - Validate latitude/longitude
      - Deduplicate plant/unit entries
    """
    cfg = load_config()
    cols = cfg["columns"]

    # ---------------------------------------------------------
    # 0. Filter by country
    # ---------------------------------------------------------
    country_col = "Country/Area"
    target_country = cfg["filters"]["country"]
    df = df[df[country_col] == target_country]
    breakpoint()

    # ---------------------------------------------------------
    # 1. Select only columns defined in config.yaml
    # ---------------------------------------------------------
    selected_columns = [
        cols["id"],
        cols["unit_id"],
        cols["plant_name"],
        cols["plant_name_local"],
        cols["unit_name"],
        cols["fuel"],
        cols["fuel_class"],
        cols["capacity_mw"],
        cols["status"],
        cols["technology"],
        cols["lat"],
        cols["lon"],
        cols["city"],
        cols["province"],
        cols["region"],
        cols["start_year"],
        cols["retired_year"],
        cols["planned_retire"],
        cols["owner"],
        cols["operator"],
    ]

    df_clean = df[selected_columns].copy()

    # ---------------------------------------------------------
    # 2. Rename columns to clean, friendly names
    # ---------------------------------------------------------
    rename_map = {
        cols["id"]: "id",
        cols["unit_id"]: "unit_id",
        cols["plant_name"]: "plant_name",
        cols["plant_name_local"]: "plant_name_local",
        cols["unit_name"]: "unit_name",
        cols["fuel"]: "fuel",
        cols["fuel_class"]: "fuel_class",
        cols["capacity_mw"]: "capacity_mw",
        cols["status"]: "status",
        cols["technology"]: "technology",
        cols["lat"]: "lat",
        cols["lon"]: "lon",
        cols["city"]: "city",
        cols["province"]: "province",
        cols["region"]: "region",
        cols["start_year"]: "start_year",
        cols["retired_year"]: "retired_year",
        cols["planned_retire"]: "planned_retire",
        cols["owner"]: "owner",
        cols["operator"]: "operator",
    }

    df_clean = df_clean.rename(columns=rename_map)

    # ---------------------------------------------------------
    # 3. Convert numeric fields
    # ---------------------------------------------------------
    df_clean["capacity_mw"] = pd.to_numeric(df_clean["capacity_mw"], errors="coerce")
    df_clean["start_year"] = pd.to_numeric(df_clean["start_year"], errors="coerce")
    df_clean["retired_year"] = pd.to_numeric(df_clean["retired_year"], errors="coerce")
    df_clean["planned_retire"] = pd.to_numeric(df_clean["planned_retire"], errors="coerce")

    # ---------------------------------------------------------
    # 4. Validate coordinates
    # ---------------------------------------------------------
    df_clean = df_clean.dropna(subset=["lat", "lon"])
    df_clean = df_clean[
        df_clean["lat"].between(-90, 90) &
        df_clean["lon"].between(-180, 180)
    ]

    # ---------------------------------------------------------
    # 5. Standardise status strings ("Operating" → "operating")
    # ---------------------------------------------------------
    df_clean["status"] = (
        df_clean["status"]
        .astype(str)
        .str.strip()
        .str.lower()
        .str.replace(" ", "_")
    )

    # ---------------------------------------------------------
    # 6. Drop duplicates (GEM sometimes repeats units)
    # ---------------------------------------------------------
    df_clean = df_clean.drop_duplicates(subset=["id", "unit_id"]).reset_index(drop=True)
    breakpoint()

    return df_clean



if __name__ == "__main__":
    # Quick test: run via `python -m src.clean_data`
    from src.read_data import load_raw_gem_data

    df_raw = load_raw_gem_data()
    df_clean = clean_gas_plant_data(df_raw)

    print(df_clean.head())
    print(f"\nRows after cleaning: {len(df_clean)}")
