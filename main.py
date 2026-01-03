"""
main.py

Entry point for the historical sectoral CO₂ emissions analysis pipeline.

Running this file will:
1. Load the project configuration
2. Validate the presence of required input data (OWID CSV)
3. Ensure all output directories exist
4. Execute the full data pipeline:
   - data ingestion (OWID only)
   - data processing (sectoral decomposition, metrics)
   - modeling (smoothing, LMDI decomposition)
   - visualization (5 publication-ready figures)
5. Export all tables and figures

The pipeline is designed to be fully reproducible and deterministic.
All domain logic lives in src/ modules with clear separation of concerns.
"""

from __future__ import annotations

import sys

from src.config import get_config
from src.utils import (
    ensure_directories_exist,
    log,
    validate_file_exists,
    save_dataframe,
)

# Pipeline stages
from src.data_ingestion import load_owid_data
from src.data_processing import process_raw_data
from src.modeling import run_modeling
from src.visualization import generate_all_figures
from src.scenarios import compute_scenario_metrics


def main() -> None:
    """
    Run the full historical sectoral emissions analysis pipeline.

    This function orchestrates the entire workflow.
    All error handling is explicit and logged.
    """
    log("=" * 70)
    log("HISTORICAL SECTORAL CO₂ EMISSIONS ANALYSIS PIPELINE")
    log("=" * 70)

    try:
        # ===================================================================
        # 1. Load configuration
        # ===================================================================
        log("\n[STEP 1/6] Loading configuration")
        config = get_config()
        log(f"  OWID CSV: {config.owid_co2_csv}")
        log(f"  Output tables dir: {config.paths.tables_dir}")
        log(f"  Output figures dir: {config.paths.figures_dir}")

        # ===================================================================
        # 2. Ensure output directories exist
        # ===================================================================
        log("\n[STEP 2/6] Preparing output directories")
        ensure_directories_exist(
            [
                config.paths.processed_data_dir,
                config.paths.output_dir,
                config.paths.figures_dir,
                config.paths.tables_dir,
            ]
        )
        log("  Output directories ready")

        # ===================================================================
        # 3. Validate and load OWID data
        # ===================================================================
        log("\n[STEP 3/6] Loading and validating OWID data")
        validate_file_exists(config.owid_co2_csv, "OWID CO₂ CSV")

        owid_world = load_owid_data(config)

        log(f"  Loaded {owid_world.shape[0]} years of global data")

        # ===================================================================
        # 4. Data processing (sectoral decomposition + metrics)
        # ===================================================================
        log("\n[STEP 4/6] Processing raw data (sectoral analysis)")

        processed = process_raw_data(owid_world, config)

        sector_long = processed["sector_long"]
        sector_shares = processed["sector_shares"]
        yoy_changes = processed["yoy_changes"]
        contribution_to_yoy = processed["contribution_to_yoy"]
        total_by_year = processed["total_by_year"]

        log(f"  Sectoral long format: {sector_long.shape[0]} records")
        log(f"  Shares computed: {sector_shares.shape[0]} records")
        log(f"  YoY changes computed: {yoy_changes.shape[0]} records")
        log(f"  Contributions computed: {contribution_to_yoy.shape[0]} records")

        # ===================================================================
        # 5. Modeling (smoothing + LMDI decomposition)
        # ===================================================================
        log("\n[STEP 5/6] Running modeling (smoothing + LMDI)")

        modeling_outputs = run_modeling(owid_world, sector_long, config)

        sector_smoothed = modeling_outputs["sector_smoothed"]
        lmdi_decomposition = modeling_outputs["lmdi_decomposition"]

        log(f"  Smoothed sector timeseries: {sector_smoothed.shape[0]} records")
        log(f"  LMDI decomposition: {lmdi_decomposition.shape[0]} periods")

        # ===================================================================
        # 6. Visualization
        # ===================================================================
        log("\n[STEP 6/6] Generating visualizations")

        generate_all_figures(
            total_by_year=total_by_year,
            sector_long=sector_long,
            sector_shares=sector_shares,
            contribution_to_yoy=contribution_to_yoy,
            lmdi_decomposition=lmdi_decomposition,
            config=config,
        )

        # ===================================================================
        # 7. Export all tables to output/tables/
        # ===================================================================
        log("\n[EXPORT] Saving processed tables")

        tables_to_export = {
            "world_sector_emissions_long.csv": sector_long,
            "world_sector_shares.csv": sector_shares,
            "world_yoy_changes.csv": yoy_changes,
            "world_contribution_to_yoy_total.csv": contribution_to_yoy,
            "kaya_lmdi_decomposition.csv": lmdi_decomposition,
        }

        for table_name, df in tables_to_export.items():
            path = config.paths.tables_dir / table_name
            save_dataframe(df, path)
            log(f"  {table_name}: {df.shape[0]} rows exported")

        # Also export smoothed sector data for reference
        path_smoothed = config.paths.tables_dir / "sector_emissions_smoothed.csv"
        save_dataframe(sector_smoothed, path_smoothed)
        log(f"  sector_emissions_smoothed.csv: {sector_smoothed.shape[0]} rows exported")

        # ===================================================================
        # Summary
        # ===================================================================
        log("\n" + "=" * 70)
        log("PIPELINE COMPLETED SUCCESSFULLY")
        log("=" * 70)
        log(f"\nGenerated outputs:")
        log(f"  Tables (5): {config.paths.tables_dir}")
        log(f"  Figures (5): {config.paths.figures_dir}")
        log(f"\nKey results:")
        log(f"  - Total global CO2: {owid_world['co2'].min():.1f}–{owid_world['co2'].max():.1f} MtCO₂")
        log(f"  - Sectors analyzed: {sector_long['sector'].nunique()}")
        log(f"  - LMDI periods: {len(lmdi_decomposition)}")
        log("\n")

    except Exception as e:
        log(f"\nERROR: {type(e).__name__}: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()