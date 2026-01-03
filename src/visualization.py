"""
src/visualization.py

Visualization module for sectoral CO₂ emissions analysis.

This module generates high-quality publication-ready figures for the historical
sectoral emissions analysis, including:

A) total_co2_timeseries.png — line plot of total world CO2 over time
B) sector_emissions_timeseries.png — multi-line plot for 6 sectors
C) sector_shares_stacked_area.png — stacked area chart of sector shares
D) sector_contribution_yoy_latest20.png — sector contributions to YoY change (last ~20 years)
E) kaya_lmdi_waterfall.png — waterfall charts showing LMDI effects

All figures use matplotlib for consistency and clarity.
No external styling frameworks or seaborn; pure matplotlib defaults.
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, Optional

import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

from src.config import Config
from src.utils import log


# =====================================================================
# Figure utilities
# =====================================================================

def _save_figure(fig: plt.Figure, path: Path) -> None:
    """
    Save a matplotlib figure to disk.

    Parameters
    ----------
    fig : plt.Figure
        Figure object to save.
    path : Path
        Destination path (should end in .png or .pdf).
    """
    fig.savefig(str(path), bbox_inches="tight", dpi=150)
    plt.close(fig)
    log(f"Figure saved: {path}")


# =====================================================================
# Figure A: Total CO2 timeseries
# =====================================================================

def plot_total_co2_timeseries(
    total_by_year: pd.DataFrame,
    config: Config,
) -> None:
    """
    Plot total world CO2 emissions over time as a line chart.

    Parameters
    ----------
    total_by_year : pd.DataFrame
        DataFrame with columns: year, co2.
    config : Config
        Project configuration.
    """
    log("Generating total CO₂ timeseries figure")

    df = total_by_year.sort_values("year")

    fig, ax = plt.subplots(figsize=(10, 6))

    ax.plot(df["year"], df["co2"], linewidth=2, color="black", label="Total CO₂")

    ax.set_title("Global CO₂ Emissions Over Time", fontsize=14, fontweight="bold")
    ax.set_xlabel("Year", fontsize=12)
    ax.set_ylabel("Emissions (MtCO₂)", fontsize=12)
    ax.grid(True, alpha=0.3)
    ax.legend()

    path = config.paths.figures_dir / "total_co2_timeseries.png"
    _save_figure(fig, path)


# =====================================================================
# Figure B: Sector emissions timeseries
# =====================================================================

def plot_sector_emissions_timeseries(
    sector_long: pd.DataFrame,
    config: Config,
) -> None:
    """
    Plot sectoral CO₂ emissions over time (multi-line chart).

    Parameters
    ----------
    sector_long : pd.DataFrame
        Sectoral emissions in long format (year, sector, emissions_mtco2).
    config : Config
        Project configuration.
    """
    log("Generating sector emissions timeseries figure")

    df = sector_long.sort_values(["sector", "year"])

    fig, ax = plt.subplots(figsize=(12, 7))

    for sector, group in df.groupby("sector"):
        ax.plot(
            group["year"],
            group["emissions_mtco2"],
            linewidth=2,
            label=sector,
            marker="o",
            markersize=3,
            alpha=0.8,
        )

    ax.set_title("Sectoral CO₂ Emissions Over Time", fontsize=14, fontweight="bold")
    ax.set_xlabel("Year", fontsize=12)
    ax.set_ylabel("Emissions (MtCO₂)", fontsize=12)
    ax.grid(True, alpha=0.3)
    ax.legend(loc="best", framealpha=0.9)

    path = config.paths.figures_dir / "sector_emissions_timeseries.png"
    _save_figure(fig, path)


# =====================================================================
# Figure C: Sector shares stacked area
# =====================================================================

def plot_sector_shares_stacked_area(
    sector_shares: pd.DataFrame,
    config: Config,
) -> None:
    """
    Plot sector shares of total emissions as a stacked area chart.

    Parameters
    ----------
    sector_shares : pd.DataFrame
        DataFrame with columns: year, sector, share_of_total.
    config : Config
        Project configuration.
    """
    log("Generating sector shares stacked area figure")

    # Pivot to wide format for stacked area
    df_pivot = sector_shares.pivot(
        index="year",
        columns="sector",
        values="share_of_total",
    ).fillna(0)

    # Ensure consistent sector order (Coal, Oil, Gas, Cement, Flaring, Other)
    desired_order = ["Coal", "Oil", "Gas", "Cement", "Flaring", "Other industry"]
    available_cols = [c for c in desired_order if c in df_pivot.columns]
    df_pivot = df_pivot[available_cols]

    fig, ax = plt.subplots(figsize=(12, 7))

    ax.stackplot(
        df_pivot.index,
        df_pivot.T.values,
        labels=df_pivot.columns,
        alpha=0.8,
    )

    ax.set_title("Sectoral Shares of Global CO₂ Emissions", fontsize=14, fontweight="bold")
    ax.set_xlabel("Year", fontsize=12)
    ax.set_ylabel("Share of Total Emissions", fontsize=12)
    ax.set_ylim([0, 1])
    ax.legend(loc="upper left", framealpha=0.9)
    ax.grid(True, alpha=0.3, axis="y")

    path = config.paths.figures_dir / "sector_shares_stacked_area.png"
    _save_figure(fig, path)


# =====================================================================
# Figure D: Sector contribution to YoY change (last 20 years)
# =====================================================================

def plot_sector_contribution_yoy_latest(
    contribution_to_yoy: pd.DataFrame,
    config: Config,
    n_years: int = 20,
) -> None:
    """
    Plot sector contributions to year-on-year total change (most recent years).

    Parameters
    ----------
    contribution_to_yoy : pd.DataFrame
        DataFrame with columns: year, sector, delta_mtco2, contribution_share.
    config : Config
        Project configuration.
    n_years : int, default 20
        Number of most recent years to display.
    """
    log(f"Generating sector contribution to YoY figure (last {n_years} years)")

    df = contribution_to_yoy.sort_values("year").copy()

    # Get most recent n_years
    max_year = df["year"].max()
    min_year = max(df["year"].min(), max_year - n_years + 1)
    df = df[df["year"] >= min_year].copy()

    # Pivot for stacked bar chart
    df_pivot = df.pivot(
        index="year",
        columns="sector",
        values="delta_mtco2",
    ).fillna(0)

    # Ensure consistent sector order
    desired_order = ["Coal", "Oil", "Gas", "Cement", "Flaring", "Other industry"]
    available_cols = [c for c in desired_order if c in df_pivot.columns]
    df_pivot = df_pivot[available_cols]

    fig, ax = plt.subplots(figsize=(12, 6))

    x_pos = np.arange(len(df_pivot.index))
    width = 0.7

    # Create stacked bar chart
    bottom = np.zeros(len(df_pivot.index))
    for col in df_pivot.columns:
        ax.bar(
            x_pos,
            df_pivot[col].values,
            width,
            label=col,
            bottom=bottom,
            alpha=0.8,
        )
        bottom += df_pivot[col].values

    ax.set_title(
        f"Sector Contributions to Annual CO₂ Change (Last {n_years} Years)",
        fontsize=14,
        fontweight="bold",
    )
    ax.set_xlabel("Year", fontsize=12)
    ax.set_ylabel("Change in Emissions (MtCO₂)", fontsize=12)
    ax.set_xticks(x_pos)
    ax.set_xticklabels(df_pivot.index.astype(int))
    ax.axhline(0, color="black", linewidth=0.8)
    ax.legend(loc="upper left", framealpha=0.9)
    ax.grid(True, alpha=0.3, axis="y")

    path = config.paths.figures_dir / "sector_contribution_yoy_latest20.png"
    _save_figure(fig, path)


# =====================================================================
# Figure E: Kaya LMDI waterfall
# =====================================================================

def plot_kaya_lmdi_waterfall(
    lmdi_decomposition: pd.DataFrame,
    config: Config,
) -> None:
    """
    Plot LMDI decomposition effects as waterfall charts (one per period).

    Parameters
    ----------
    lmdi_decomposition : pd.DataFrame
        DataFrame with columns: period, effect_population, effect_affluence,
        effect_intensity, delta_co2.
    config : Config
        Project configuration.
    """
    log("Generating Kaya LMDI waterfall figures")

    # Create one figure with subplots (one per period)
    n_periods = len(lmdi_decomposition)

    if n_periods == 0:
        log("No LMDI data to visualize")
        return

    fig, axes = plt.subplots(1, n_periods, figsize=(5 * n_periods, 6))

    # Handle single period case
    if n_periods == 1:
        axes = [axes]

    for idx, (ax, row) in enumerate(zip(axes, lmdi_decomposition.itertuples())):
        period = row.period
        effect_p = row.effect_population
        effect_a = row.effect_affluence
        effect_i = row.effect_intensity
        delta_total = row.delta_co2

        # Data for waterfall: [population, affluence, intensity, total]
        categories = ["Population", "Affluence", "Intensity", "Total"]
        values = [effect_p, effect_a, effect_i, delta_total]

        # Create waterfall logic: cumulative positions
        x_pos = np.arange(len(categories))
        colors = ["#2ecc71" if v > 0 else "#e74c3c" for v in values]
        colors[-1] = "#3498db"  # Total in different color

        ax.bar(x_pos, values, color=colors, alpha=0.8, edgecolor="black", linewidth=1)

        ax.set_title(f"LMDI Decomposition: {period}", fontsize=12, fontweight="bold")
        ax.set_ylabel("Effect on ΔCO₂ (MtCO₂)", fontsize=11)
        ax.set_xticks(x_pos)
        ax.set_xticklabels(categories, rotation=0)
        ax.axhline(0, color="black", linewidth=0.8)
        ax.grid(True, alpha=0.3, axis="y")

    plt.tight_layout()
    path = config.paths.figures_dir / "kaya_lmdi_waterfall.png"
    _save_figure(fig, path)


# =====================================================================
# Main orchestration
# =====================================================================

def generate_all_figures(
    total_by_year: pd.DataFrame,
    sector_long: pd.DataFrame,
    sector_shares: pd.DataFrame,
    contribution_to_yoy: pd.DataFrame,
    lmdi_decomposition: pd.DataFrame,
    config: Config,
) -> None:
    """
    Generate all required visualization figures.

    Parameters
    ----------
    total_by_year : pd.DataFrame
        Total CO2 by year.
    sector_long : pd.DataFrame
        Sectoral emissions in long format.
    sector_shares : pd.DataFrame
        Sector shares by year.
    contribution_to_yoy : pd.DataFrame
        Sector contributions to YoY change.
    lmdi_decomposition : pd.DataFrame
        LMDI decomposition results.
    config : Config
        Project configuration.
    """
    log("Starting figure generation")

    plot_total_co2_timeseries(total_by_year, config)
    plot_sector_emissions_timeseries(sector_long, config)
    plot_sector_shares_stacked_area(sector_shares, config)
    plot_sector_contribution_yoy_latest(contribution_to_yoy, config)
    plot_kaya_lmdi_waterfall(lmdi_decomposition, config)

    log("All figures generated successfully")