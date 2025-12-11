from pathlib import Path
import logging
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import LogNorm

try:
    import rasterio
    RASTERIO_AVAILABLE = True
except ImportError:
    RASTERIO_AVAILABLE = False
    logger = logging.getLogger(__name__)
    logger.warning("rasterio not available. TIFF file reading will not work.")

from src.clean_data import clean_gas_plant_data
from src.read_data import load_population_density_data, load_raw_gem_data 

from .config import load_config

logger = logging.getLogger(__name__)


def plot_plants_and_pop_density(df_plants: pd.DataFrame, df_pop: pd.DataFrame = None) -> None:
    """
    Plot gas plants and population density data from TIFF file.
    
    Args:
        df_plants: DataFrame with gas plant data containing 'lat' and 'lon' columns
        df_pop: Optional DataFrame (deprecated - TIFF file is used instead)
    """
    try:
        logger.info("Starting plot generation: plants_and_pop_density")
        logger.info(f"df_plants shape: {df_plants.shape}")
        
        if not RASTERIO_AVAILABLE:
            raise ImportError("rasterio is required to read TIFF files. Install it with: pip install rasterio")
        
        cfg = load_config()
        figures_dir = Path(cfg["paths"]["figures"])
        figures_dir.mkdir(parents=True, exist_ok=True)
        
        # Validate required columns for plants
        required_plant_cols = ["lat", "lon"]
        missing_plant_cols = [col for col in required_plant_cols if col not in df_plants.columns]
        
        if missing_plant_cols:
            raise ValueError(f"Missing required columns in df_plants: {missing_plant_cols}")
        
        # Filter out any NaN values
        df_plants_clean = df_plants.dropna(subset=["lat", "lon"]).copy()
        
        logger.info(f"After cleaning - plants: {len(df_plants_clean)}")
        
        if len(df_plants_clean) == 0:
            raise ValueError("No valid gas plant coordinates found")
        
        # Load TIFF file
        tiff_path = cfg["paths"]["population_tiff_file"]
        if not tiff_path.exists():
            raise FileNotFoundError(f"Population density TIFF file not found at: {tiff_path}")
        
        logger.info(f"Loading population density TIFF from: {tiff_path}")
        
        # Read TIFF file
        with rasterio.open(tiff_path) as src:
            # Read the raster data (first band)
            pop_data = src.read(1)
            
            # Get geographic bounds
            bounds = src.bounds
            transform = src.transform
            crs = src.crs
            
            logger.info(f"TIFF bounds: {bounds}")
            logger.info(f"TIFF CRS: {crs}")
            logger.info(f"TIFF shape: {pop_data.shape}")
            logger.info(f"TIFF data range: {np.nanmin(pop_data)} to {np.nanmax(pop_data)}")
        
        # Create figure
        fig, ax = plt.subplots(figsize=(12, 10))
        
        # Prepare population density data for visualization
        # Get extent in lat/lon coordinates
        x_min, y_min = bounds.left, bounds.bottom
        x_max, y_max = bounds.right, bounds.top
        
        # Mask no-data values (typically 0 or negative values)
        pop_data_masked = np.ma.masked_where(pop_data <= 0, pop_data)
        
        # Plot population density as image
        pop_positive = pop_data[pop_data > 0]
        if len(pop_positive) > 0:
            vmin = max(pop_positive.min(), 1)  # Avoid log(0)
            vmax = pop_positive.max()
            
            im = ax.imshow(
                pop_data_masked,
                extent=[x_min, x_max, y_min, y_max],
                cmap="YlOrRd",
                norm=LogNorm(vmin=vmin, vmax=vmax),
                alpha=0.7,
                origin="upper",
                interpolation="bilinear"
            )
            
            # Add colorbar
            cbar = plt.colorbar(im, ax=ax)
            cbar.set_label("Population Density (People per km²)", rotation=270, labelpad=20)
        else:
            logger.warning("No positive population density values found in TIFF file")
        
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
        
        # Generate the plot (TIFF file is loaded inside the function)
        logger.info("Generating plot...")
        plot_plants_and_pop_density(df_plants)
        
        logger.info("Plot generation completed successfully!")
        print(f"\n✓ Plot saved to: figures/plants_and_pop_density.png")
        
    except Exception as e:
        logger.error(f"Failed to generate plot: {e}", exc_info=True)
        raise

