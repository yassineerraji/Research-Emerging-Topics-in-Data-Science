"""
src/data_ingestion.py

Data ingestion module for loading Our World in Data (OWID) CO₂ emissions.

This module loads and validates the OWID historical CO₂ dataset,
filtering to the World aggregate and verifying required columns.

The dataset serves as the single source of truth for all sectoral analysis.
"""

from __future__ import annotations

import pandas as pd

from src.config import Config
from src.utils import log, validate_file_exists


def load_owid_data(config: Config) -> pd.DataFrame:
    """
    Load and validate OWID CO₂ dataset (World aggregate only).

    Loads the CSV file specified in configuration, filters to the World aggregate,
    validates that all required columns exist, and sorts by year.

    Parameters
    ----------
    config : Config
        Project configuration containing path to OWID CSV.

    Returns
    -------
    pd.DataFrame
        Filtered DataFrame with columns: country, year, iso_code, co2, population, gdp,
        coal_co2, oil_co2, gas_co2, cement_co2, flaring_co2, other_industry_co2.
        Sorted by year ascending.

    Raises
    ------
    FileNotFoundError
        If the OWID CSV file does not exist.
    ValueError
        If required columns are missing from the dataset.

    Notes
    -----
    The dataset should contain sectoral decomposition columns (coal_co2, oil_co2, etc.)
    that sum to the total co2 (to within rounding in recent years).
    """
    log(f"Loading OWID CO₂ dataset from {config.owid_co2_csv}")

    # Validate file exists
    validate_file_exists(config.owid_co2_csv, "OWID CO₂ CSV")

    # Load CSV
    df = pd.read_csv(config.owid_co2_csv)

    log(f"OWID dataset loaded: {df.shape[0]:,} rows, {df.shape[1]} columns")

    # ===================================================================
    # Validate required columns
    # ===================================================================
    required_cols = {
        "country",
        "year",
        "iso_code",
        "co2",
        "population",
        "gdp",
        "coal_co2",
        "oil_co2",
        "gas_co2",
        "cement_co2",
        "flaring_co2",
        "other_industry_co2",
    }

    missing = required_cols - set(df.columns)
    if missing:
        raise ValueError(
            f"OWID dataset missing required columns: {missing}"
        )

    log(f"All required columns present: {sorted(required_cols)}")

    # ===================================================================
    # Filter to World aggregate
    # ===================================================================
    df_world = df[df["country"] == "World"].copy()
    
    if df_world.empty:
        raise ValueError("No 'World' aggregate found in OWID dataset")

    log(f"Filtered to World aggregate: {df_world.shape[0]} rows")

    # ===================================================================
    # Sort by year and validate year range
    # ===================================================================
    df_world = df_world.sort_values("year").reset_index(drop=True)

    min_year = df_world["year"].min()
    max_year = df_world["year"].max()
    log(f"Year range: {min_year} – {max_year} ({df_world.shape[0]} years)")

    # ===================================================================
    # Validate and log component sum check (latest year)
    # ===================================================================
    latest_year_data = df_world[df_world["year"] == max_year].iloc[0]
    total_co2 = latest_year_data["co2"]
    component_sum = (
        latest_year_data["coal_co2"]
        + latest_year_data["oil_co2"]
        + latest_year_data["gas_co2"]
        + latest_year_data["cement_co2"]
        + latest_year_data["flaring_co2"]
        + latest_year_data["other_industry_co2"]
    )
    
    diff = abs(total_co2 - component_sum)
    pct_diff = (diff / total_co2 * 100) if total_co2 != 0 else 0
    
    log(
        f"Component sum check (year {max_year}): "
        f"total_co2={total_co2:.2f}, "
        f"sum(components)={component_sum:.2f}, "
        f"diff={diff:.4f} ({pct_diff:.3f}%)"
    )

    return df_world