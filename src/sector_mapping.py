"""
src/sector_mapping.py

Canonical sector taxonomy and extraction logic.

This module defines the mapping between OWID raw dataset columns
(coal_co2, oil_co2, etc.) and the canonical sector names used throughout
the analysis.

It also provides extraction functions to convert the wide-format OWID data
into a long-format sectoral dataset.
"""

from __future__ import annotations

import pandas as pd

from src.utils import log


# =====================================================================
# Canonical sector mapping
# =====================================================================

SECTOR_MAPPING = {
    "coal_co2": "Coal",
    "oil_co2": "Oil",
    "gas_co2": "Gas",
    "cement_co2": "Cement",
    "flaring_co2": "Flaring",
    "other_industry_co2": "Other industry",
}

SECTOR_COLUMNS = list(SECTOR_MAPPING.keys())
CANONICAL_SECTORS = list(SECTOR_MAPPING.values())


# =====================================================================
# Extraction functions
# =====================================================================

def extract_sector_long(df_world: pd.DataFrame) -> pd.DataFrame:
    """
    Extract sectoral CO₂ data from OWID wide format to long format.

    Converts OWID world data (with columns coal_co2, oil_co2, etc.)
    into a long-format table with one row per (year, sector) pair.

    Parameters
    ----------
    df_world : pd.DataFrame
        OWID world aggregate data with sector columns (coal_co2, oil_co2, etc.).

    Returns
    -------
    pd.DataFrame
        Long-format DataFrame with columns: year, sector, emissions_mtco2.
        Rows with NaN emissions are dropped.
        Sorted by year, then sector.

    Notes
    -----
    - The returned DataFrame excludes NaN emission values.
    - All emissions are coerced to float.
    """
    log("Extracting sectoral CO₂ emissions to long format")

    # Select relevant columns and melt to long format
    df_melt = df_world[["year"] + SECTOR_COLUMNS].copy()

    df_long = df_melt.melt(
        id_vars=["year"],
        value_vars=SECTOR_COLUMNS,
        var_name="sector_col",
        value_name="emissions_mtco2",
    )

    # Map column names to canonical sector names
    df_long["sector"] = df_long["sector_col"].map(SECTOR_MAPPING)
    df_long = df_long.drop(columns=["sector_col"])

    # Coerce to float and drop NaN
    df_long["emissions_mtco2"] = pd.to_numeric(
        df_long["emissions_mtco2"], errors="coerce"
    )

    df_long = df_long.dropna(subset=["emissions_mtco2"])

    # Sort and reset index
    df_long = df_long.sort_values(["year", "sector"]).reset_index(drop=True)

    log(
        f"Extracted {len(df_long)} sector-year records "
        f"across {len(CANONICAL_SECTORS)} sectors"
    )

    return df_long
