"""
src/modeling.py

Modeling module for historical sectoral emissions analysis.

Purpose
-------
This module computes advanced metrics and decompositions from raw sectoral data:
- Rolling smoothing of time series
- Smoothed time-series artifacts (for visualization)
- Kaya identity LMDI (Log Mean Divisia Index) decomposition
- Component analysis of CO₂ change into population, affluence, and intensity effects

LMDI Methodology
---------------
The Kaya identity: CO2 = Population × (GDP/Population) × (CO2/GDP)
                      = P × A × I
                      where A = affluence (GDP per capita)
                            I = intensity (CO2/GDP)

LMDI additive decomposition splits the change in CO2 into effects:
  ΔCO2 = Effect_P + Effect_A + Effect_I

where each effect represents the contribution of that factor's change,
holding others at their baseline values.

For a factor X:
  Effect_X = L(CO2_t, CO2_0) × ln(X_t / X_0)
  
  L(a, b) = (a - b) / (ln(a) - ln(b))  [geometric mean of the two values]
            or a (if a ≈ b)

This provides a clear, interpretable decomposition without requiring
any scenario assumptions.
"""

from __future__ import annotations

from typing import Optional, List

import numpy as np
import pandas as pd

from src.config import Config
from src.utils import log, safe_divide, save_dataframe


# =====================================================================
# Smoothing utility
# =====================================================================

def smooth_timeseries(
    series: pd.Series,
    window: int = 5,
) -> pd.Series:
    """
    Smooth a time series using centered rolling mean.

    Parameters
    ----------
    series : pd.Series
        Series to smooth.
    window : int, default 5
        Rolling window size (must be odd).

    Returns
    -------
    pd.Series
        Smoothed series.

    Raises
    ------
    ValueError
        If window is not odd.
    """
    if window <= 1:
        return series.copy()

    if window % 2 == 0:
        raise ValueError("Smoothing window must be odd")

    return series.rolling(window=window, center=True, min_periods=1).mean()


# =====================================================================
# Kaya/LMDI Decomposition
# =====================================================================

def _log_mean_divisia_index(
    value_start: float,
    value_end: float,
    co2_start: float,
    co2_end: float,
) -> float:
    """
    Compute the LMDI weighting factor.

    The LMDI approach uses a geometric mean-based weighting:
      L = (CO2_end - CO2_start) / (ln(CO2_end) - ln(CO2_start))
    
    If the change is very small or both values are equal, returns the start CO2 value.

    Parameters
    ----------
    value_start : float
        Initial value of the factor (e.g., population, GDP/capita, CO2/GDP).
    value_end : float
        Final value of the factor.
    co2_start : float
        Initial total CO2.
    co2_end : float
        Final total CO2.

    Returns
    -------
    float
        LMDI weighting factor.
    """
    if abs(co2_end - co2_start) < 1e-9:
        # No change in CO2, return start value
        return co2_start if co2_start != 0 else 1.0

    ln_ratio = np.log(co2_end) - np.log(co2_start)
    if abs(ln_ratio) < 1e-9:
        return co2_start if co2_start != 0 else 1.0

    return (co2_end - co2_start) / ln_ratio


def compute_kaya_lmdi(
    world_df: pd.DataFrame,
    periods: Optional[List[tuple]] = None,
) -> pd.DataFrame:
    """
    Compute Kaya identity LMDI decomposition for specified periods.

    The Kaya identity: CO2 = P × (GDP/P) × (CO2/GDP)
    
    LMDI decomposes changes in CO2 into:
    - Effect_P: population growth effect
    - Effect_A: affluence (GDP per capita) effect
    - Effect_I: intensity (CO2/GDP) effect

    Parameters
    ----------
    world_df : pd.DataFrame
        World data with columns: year, co2, population, gdp.
    periods : list of tuples, optional
        List of (start_year, end_year) tuples for analysis.
        If None, uses default periods: [(1990, latest), (2000, 2019), (2019, latest)]

    Returns
    -------
    pd.DataFrame
        Table with columns: period, effect_population, effect_affluence, effect_intensity, delta_co2.
        All effects and delta_co2 are in MtCO₂.

    Notes
    -----
    - Years outside the dataset range are logged with a warning but analysis continues.
    - If a required year is missing, the closest available year is substituted.
    """
    df = world_df.copy().sort_values("year").reset_index(drop=True)

    if periods is None:
        max_year = df["year"].max()
        periods = [
            (1990, max_year),
            (2000, 2019),
            (2019, max_year),
        ]

    log(f"Computing LMDI decomposition for {len(periods)} periods")

    results = []

    for start_year, end_year in periods:
        # Find closest available years
        start_data = df.loc[(df["year"] - start_year).abs().idxmin()]
        end_data = df.loc[(df["year"] - end_year).abs().idxmin()]

        actual_start_year = int(start_data["year"])
        actual_end_year = int(end_data["year"])

        if actual_start_year != start_year or actual_end_year != end_year:
            log(
                f"Period {start_year}–{end_year}: adjusted to {actual_start_year}–{actual_end_year}"
            )

        # Extract Kaya factors
        p_start = start_data["population"]
        p_end = end_data["population"]

        a_start = safe_divide(start_data["gdp"], start_data["population"])
        a_end = safe_divide(end_data["gdp"], end_data["population"])

        i_start = safe_divide(start_data["co2"], start_data["gdp"])
        i_end = safe_divide(end_data["co2"], end_data["gdp"])

        co2_start = start_data["co2"]
        co2_end = end_data["co2"]

        # Compute LMDI weighting
        L = _log_mean_divisia_index(p_start, p_end, co2_start, co2_end)

        # Compute effects
        effect_p = L * np.log(p_end / p_start) if p_start > 0 else np.nan
        effect_a = L * np.log(a_end / a_start) if a_start > 0 else np.nan
        effect_i = L * np.log(i_end / i_start) if i_start > 0 else np.nan

        delta_co2 = co2_end - co2_start

        results.append({
            "period": f"{actual_start_year}–{actual_end_year}",
            "effect_population": effect_p,
            "effect_affluence": effect_a,
            "effect_intensity": effect_i,
            "delta_co2": delta_co2,
        })

    lmdi_table = pd.DataFrame(results)

    log(f"LMDI decomposition computed for {len(results)} periods")

    return lmdi_table


# =====================================================================
# Unified modeling interface
# =====================================================================

def run_modeling(
    owid_world: pd.DataFrame,
    sector_long: pd.DataFrame,
    config: Config,
) -> dict[str, pd.DataFrame]:
    """
    Run all modeling steps and return artifacts.

    This includes:
    - smoothed sectoral time series
    - Kaya identity LMDI decomposition

    Parameters
    ----------
    owid_world : pd.DataFrame
        Full OWID world data (required for LMDI).
    sector_long : pd.DataFrame
        Sectoral emissions in long format (year, sector, emissions_mtco2).
    config : Config
        Project configuration.

    Returns
    -------
    dict[str, pd.DataFrame]
        Dictionary with keys:
        - sector_smoothed: smoothed sectoral timeseries
        - lmdi_decomposition: Kaya LMDI results
    """
    log("Starting modeling: smoothing + LMDI decomposition")

    # ===================================================================
    # Smoothed sectoral series
    # ===================================================================
    sector_smoothed = sector_long.copy()

    sector_smoothed = sector_smoothed.sort_values(["sector", "year"]).reset_index(drop=True)

    sector_smoothed["emissions_smoothed"] = sector_smoothed.groupby("sector")[
        "emissions_mtco2"
    ].transform(lambda x: smooth_timeseries(x, window=5))

    log(f"Smoothed {len(sector_smoothed)} sector-year records")

    # ===================================================================
    # Kaya LMDI decomposition
    # ===================================================================
    lmdi = compute_kaya_lmdi(owid_world)

    log("Modeling step completed")

    return {
        "sector_smoothed": sector_smoothed,
        "lmdi_decomposition": lmdi,
    }
