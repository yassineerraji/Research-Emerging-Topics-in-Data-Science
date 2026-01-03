"""
src/data_processing.py

Raw data processing and metric computation.

This module transforms OWID world data into a suite of processed artifacts:
- sector_long: sectoral emissions in long format
- sector_shares: sector shares of total emissions
- yoy_changes: year-on-year changes in emissions
- contribution_to_yoy_total: sector contribution to annual total change

All metrics are computed deterministically from OWID data only.
"""

from __future__ import annotations

import pandas as pd
import numpy as np

from src.config import Config
from src.utils import log, safe_divide
from src.sector_mapping import extract_sector_long, CANONICAL_SECTORS


def compute_sector_shares(
    sector_long: pd.DataFrame,
    total_by_year: pd.Series,
) -> pd.DataFrame:
    """
    Compute sector shares of total CO₂ emissions by year.

    Parameters
    ----------
    sector_long : pd.DataFrame
        Sectoral emissions in long format (year, sector, emissions_mtco2).
    total_by_year : pd.Series
        Total CO₂ by year (from OWID co2 column), indexed by year.

    Returns
    -------
    pd.DataFrame
        Table with columns: year, sector, share_of_total.
        share_of_total is in (0, 1) and represents the fraction of total emissions.
    """
    df = sector_long.copy()

    # Merge in total emissions for each year
    df = df.merge(
        total_by_year.rename("total_co2").reset_index(),
        on="year",
        how="left",
    )

    # Compute share
    df["share_of_total"] = safe_divide(df["emissions_mtco2"], df["total_co2"])

    return df[["year", "sector", "share_of_total"]].sort_values(["year", "sector"]).reset_index(drop=True)


def compute_yoy_changes(sector_long: pd.DataFrame) -> pd.DataFrame:
    """
    Compute year-on-year changes in sectoral emissions.

    Parameters
    ----------
    sector_long : pd.DataFrame
        Sectoral emissions in long format (year, sector, emissions_mtco2).

    Returns
    -------
    pd.DataFrame
        Table with columns: year, sector, emissions_mtco2, yoy_change_mtco2, yoy_change_pct.
        First year for each sector has NaN changes (no prior year).
    """
    df = sector_long.copy()

    # Group by sector and compute change
    df = df.sort_values(["sector", "year"]).reset_index(drop=True)

    df["yoy_change_mtco2"] = df.groupby("sector")["emissions_mtco2"].diff()
    df["yoy_change_pct"] = safe_divide(
        df["yoy_change_mtco2"],
        df.groupby("sector")["emissions_mtco2"].shift(1)
    )

    return df.sort_values(["year", "sector"]).reset_index(drop=True)


def compute_contribution_to_total_change(
    sector_yoy: pd.DataFrame,
    total_yoy: pd.DataFrame,
) -> pd.DataFrame:
    """
    Compute each sector's contribution to total annual CO₂ change.

    Parameters
    ----------
    sector_yoy : pd.DataFrame
        Sectoral YoY changes (year, sector, yoy_change_mtco2).
    total_yoy : pd.DataFrame
        Total CO₂ YoY changes (year, yoy_change_mtco2).

    Returns
    -------
    pd.DataFrame
        Table with columns: year, sector, delta_mtco2, contribution_share.
        contribution_share = delta_sector / delta_total.
        Where delta_total == 0, contribution_share is NaN.
    """
    df = sector_yoy[["year", "sector", "yoy_change_mtco2"]].copy()
    df = df.rename(columns={"yoy_change_mtco2": "delta_mtco2"})

    # Merge total change
    total_rename = total_yoy[["year", "yoy_change_mtco2"]].copy()
    total_rename = total_rename.rename(columns={"yoy_change_mtco2": "delta_total"})

    df = df.merge(total_rename, on="year", how="left")

    # Compute contribution share
    df["contribution_share"] = safe_divide(df["delta_mtco2"], df["delta_total"])

    return df.sort_values(["year", "sector"]).reset_index(drop=True)


def process_raw_data(
    owid_world: pd.DataFrame,
    config: Config,
) -> dict[str, pd.DataFrame]:
    """
    Process OWID world data into all required downstream artifacts.

    Parameters
    ----------
    owid_world : pd.DataFrame
        Loaded and validated OWID world data.
    config : Config
        Project configuration (unused but kept for consistency).

    Returns
    -------
    dict[str, pd.DataFrame]
        Dictionary with keys:
        - sector_long: long-format sectoral emissions
        - sector_shares: sector shares by year
        - yoy_changes: year-on-year changes with absolute and percentage
        - contribution_to_yoy: sector contributions to total annual change
    """
    log("Starting data processing")

    # ===================================================================
    # Extract sectoral emissions (long format)
    # ===================================================================
    sector_long = extract_sector_long(owid_world)

    # ===================================================================
    # Compute total by year (from OWID co2 column)
    # ===================================================================
    total_by_year = owid_world.set_index("year")["co2"]

    log(f"Total emissions range: {total_by_year.min():.1f}–{total_by_year.max():.1f} MtCO₂")

    # ===================================================================
    # Compute sector shares
    # ===================================================================
    sector_shares = compute_sector_shares(sector_long, total_by_year)
    log(f"Sector shares computed for {sector_shares['year'].nunique()} years")

    # ===================================================================
    # Compute YoY changes
    # ===================================================================
    sector_yoy = compute_yoy_changes(sector_long)
    log("Year-on-year changes computed")

    # Compute total YoY for reference
    total_yoy = pd.DataFrame({
        "year": owid_world["year"],
        "yoy_change_mtco2": owid_world["co2"].diff(),
    })

    # ===================================================================
    # Compute contributions
    # ===================================================================
    contribution = compute_contribution_to_total_change(sector_yoy, total_yoy)
    log("Sector contributions to annual change computed")

    log("Data processing completed")

    return {
        "sector_long": sector_long,
        "sector_shares": sector_shares,
        "yoy_changes": sector_yoy,
        "contribution_to_yoy": contribution,
        "total_by_year": total_by_year.reset_index(),
    }
