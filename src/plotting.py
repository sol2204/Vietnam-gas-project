from pathlib import Path
import logging
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import LogNorm
from scipy.interpolate import griddata

from src.clean_data import clean_gas_plant_data
from src.read_data import load_population_density_data, load_raw_gem_data 

from .config import load_config

logger = logging.getLogger(__name__)


def plot_plants_and_pop_density(df_plants: pd.DataFrame, df_pop: pd.DataFrame) -> None:
    """
    Plot gas plants and population density data.
    
    Args:
        df_plants: DataFrame with gas plant data containing 'lat' and 'lon' columns
        df_pop: DataFrame with population density data containing 'x', 'y' (coordinates) 
                and 'z' (People per km²) columns
    """
    try:
        logger.info("Starting plot generation: plants_and_pop_density")
        logger.info(f"df_plants shape: {df_plants.shape}, df_pop shape: {df_pop.shape}")
        
        cfg = load_config()
        figures_dir = Path(cfg["paths"]["figures"])
        figures_dir.mkdir(parents=True, exist_ok=True)
        
        # Validate required columns
        required_plant_cols = ["lat", "lon"]
        required_pop_cols = ["X", "Y", "Z"]
        
        missing_plant_cols = [col for col in required_plant_cols if col not in df_plants.columns]
        missing_pop_cols = [col for col in required_pop_cols if col not in df_pop.columns]
        
        if missing_plant_cols:
            raise ValueError(f"Missing required columns in df_plants: {missing_plant_cols}")
        if missing_pop_cols:
            raise ValueError(f"Missing required columns in df_pop: {missing_pop_cols}")
        
        # Filter out any NaN values
        df_plants_clean = df_plants.dropna(subset=["lat", "lon"]).copy()
        df_pop_clean = df_pop.dropna(subset=["X", "Y", "Z"]).copy()
        
        logger.info(f"After cleaning - plants: {len(df_plants_clean)}, pop: {len(df_pop_clean)}")
        
        if len(df_plants_clean) == 0:
            raise ValueError("No valid gas plant coordinates found")
        if len(df_pop_clean) == 0:
            raise ValueError("No valid population density data found")
        
        # Create figure
        fig, ax = plt.subplots(figsize=(12, 10))
        
        # Prepare population density data for visualization
        # Create a grid for interpolation
        x_min, x_max = df_pop_clean["X"].min(), df_pop_clean["X"].max()
        y_min, y_max = df_pop_clean["Y"].min(), df_pop_clean["Y"].max()
        
        # Create grid for contour/heatmap
        grid_resolution = 200
        xi = np.linspace(x_min, x_max, grid_resolution)
        yi = np.linspace(y_min, y_max, grid_resolution)
        xi_grid, yi_grid = np.meshgrid(xi, yi)
        
        # Interpolate population density onto grid
        z_grid = griddata(
            (df_pop_clean["X"], df_pop_clean["Y"]),
            df_pop_clean["Z"],
            (xi_grid, yi_grid),
            method="linear",
            fill_value=0
        )
        
        # Plot population density as filled contour/heatmap
        # Use log scale for better visualization of density variations
        z_positive = z_grid[z_grid > 0]
        if len(z_positive) > 0:
            vmin = max(z_positive.min(), 1)  # Avoid log(0)
            vmax = z_positive.max()
            im = ax.contourf(
                xi_grid, yi_grid, z_grid,
                levels=50,
                cmap="YlOrRd",
                norm=LogNorm(vmin=vmin, vmax=vmax),
                alpha=0.7
            )
            
            # Add colorbar
            cbar = plt.colorbar(im, ax=ax)
            cbar.set_label("Population Density (People per km²)", rotation=270, labelpad=20)
        else:
            logger.warning("No positive population density values found for visualization")
        
        # Plot gas plants as markers
        ax.scatter(
            df_plants_clean["lon"],
            df_plants_clean["lat"],
            c="red",
            marker="^",
            s=100,
            edgecolors="black",
            linewidths=1.5,
            label="Gas Plants",
            zorder=5
        )
        
        # Set labels and title
        ax.set_xlabel("Longitude", fontsize=12)
        ax.set_ylabel("Latitude", fontsize=12)
        ax.set_title("Gas Plants and Population Density in Vietnam", fontsize=14, fontweight="bold")
        ax.legend(loc="upper right", fontsize=10)
        ax.grid(True, alpha=0.3, linestyle="--")
        
        # Set equal aspect ratio for proper geographic representation
        ax.set_aspect("equal", adjustable="box")
        
        # Save figure
        output_path = figures_dir / "plants_and_pop_density.png"
        plt.tight_layout()
        plt.savefig(output_path, dpi=300, bbox_inches="tight")
        plt.close()
        
        logger.info(f"Plot saved successfully to: {output_path}")
        
    except Exception as e:
        logger.error(f"Error generating plot: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    # Set up logging to see what's happening
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    try:
        # Load and clean gas plant data
        logger.info("Loading raw GEM data...")
        df_raw = load_raw_gem_data()
        logger.info(f"Loaded {len(df_raw)} rows of raw GEM data")
        
        logger.info("Cleaning gas plant data...")
        df_plants = clean_gas_plant_data(df_raw)
        logger.info(f"Cleaned data: {len(df_plants)} gas plant units")
        
        # Load population density data
        logger.info("Loading population density data...")
        df_pop = load_population_density_data()
        logger.info(f"Loaded {len(df_pop)} rows of population density data")
        
        # Generate the plot
        logger.info("Generating plot...")
        plot_plants_and_pop_density(df_plants, df_pop)
        
        logger.info("Plot generation completed successfully!")
        print(f"\n✓ Plot saved to: figures/plants_and_pop_density.png")
        
    except Exception as e:
        logger.error(f"Failed to generate plot: {e}", exc_info=True)
        raise

