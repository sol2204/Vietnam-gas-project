# src/clean_data.py

import pandas as pd
from .config import load_config



def merge_units_to_plants(df: pd.DataFrame) -> pd.DataFrame:
    """
    Merge multiple units of the same plant into a single plant record.
    
    Groups by plant name and aggregates:
    - Sums capacity_mw across all units
    - Combines unit_id and unit_name into lists
    - Takes first value for location, plant info, etc.
    - Combines status, technology, fuel info appropriately
    
    Args:
        df: DataFrame with cleaned gas plant data (may have multiple units per plant)
    
    Returns:
        DataFrame with one row per plant (units merged)
    """
    if df.empty:
        return df
    
    # Create a copy to avoid modifying the original
    df_merged = df.copy()
    
    # Group by plant name (or plant ID if name is missing)
    # Use plant_name as primary grouping key, fallback to id if name is missing
    group_key = "plant_name"
    if group_key not in df_merged.columns or df_merged[group_key].isna().all():
        group_key = "id"
    
    # Define aggregation functions for each column
    agg_dict = {}
    
    # Numeric: sum capacity
    if "capacity_mw" in df_merged.columns:
        agg_dict["capacity_mw"] = "sum"
    
    # Unit identifiers: combine into lists
    if "unit_id" in df_merged.columns:
        agg_dict["unit_id"] = lambda x: list(x.dropna().unique())
    if "unit_name" in df_merged.columns:
        agg_dict["unit_name"] = lambda x: list(x.dropna().unique())
    
    # Plant identifiers: take first (should be same for all units)
    for col in ["id", "plant_name", "plant_name_local"]:
        if col in df_merged.columns:
            agg_dict[col] = "first"
    
    # Location: take first (should be same for all units of a plant)
    for col in ["lat", "lon", "city", "province", "region"]:
        if col in df_merged.columns:
            agg_dict[col] = "first"
    
    # Status: combine unique statuses
    if "status" in df_merged.columns:
        agg_dict["status"] = lambda x: ", ".join(x.dropna().unique())
    
    # Technology: combine unique technologies
    if "technology" in df_merged.columns:
        agg_dict["technology"] = lambda x: ", ".join(x.dropna().unique())
    
    # Fuel: combine unique fuels
    if "fuel" in df_merged.columns:
        agg_dict["fuel"] = lambda x: ", ".join(x.dropna().unique())
    if "fuel_class" in df_merged.columns:
        agg_dict["fuel_class"] = lambda x: ", ".join(x.dropna().unique())
    
    # Years: take min for start_year, max for retired_year/planned_retire
    if "start_year" in df_merged.columns:
        agg_dict["start_year"] = "min"
    if "retired_year" in df_merged.columns:
        agg_dict["retired_year"] = lambda x: x.max() if x.notna().any() else None
    if "planned_retire" in df_merged.columns:
        agg_dict["planned_retire"] = lambda x: x.max() if x.notna().any() else None
    
    # Owner/Operator: combine unique values
    if "owner" in df_merged.columns:
        agg_dict["owner"] = lambda x: ", ".join(x.dropna().unique())
    if "operator" in df_merged.columns:
        agg_dict["operator"] = lambda x: ", ".join(x.dropna().unique())
    
    # Group and aggregate
    df_merged = df_merged.groupby(group_key, as_index=False).agg(agg_dict)
    
    # Convert list columns to comma-separated strings for readability
    for col in ["unit_id", "unit_name"]:
        if col in df_merged.columns and df_merged[col].dtype == object:
            # Check if it's a list column
            if df_merged[col].notna().any() and isinstance(df_merged[col].iloc[0], list):
                df_merged[col] = df_merged[col].apply(
                    lambda x: ", ".join(map(str, x)) if isinstance(x, list) else x
                )
    
    # Add count of units per plant
    unit_counts = df.groupby(group_key).size().reset_index(name="num_units")
    df_merged = df_merged.merge(unit_counts, on=group_key, how="left")
    
    # Reset index
    df_merged = df_merged.reset_index(drop=True)
    
    return df_merged



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
    
    keep_statuses = [
    'operating',
    'construction',
    'pre-construction',
    'announced']
    

    df_clean = df_clean[df_clean['status'].isin(keep_statuses)]
    breakpoint()
    df_clean = merge_units_to_plants(df_clean)
    breakpoint()

    return df_clean



if __name__ == "__main__":
    # Quick test: run via `python -m src.clean_data`
    from src.read_data import load_raw_gem_data

    df_raw = load_raw_gem_data()
    df_clean = clean_gas_plant_data(df_raw)
    breakpoint()

    print(df_clean.head())
    print(f"\nRows after cleaning: {len(df_clean)}")
