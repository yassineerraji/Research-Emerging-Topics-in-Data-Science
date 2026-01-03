"""
src/config.py

Centralized configuration for the historical sectoral CO₂ emissions analysis.

This module provides the canonical configuration object used throughout the pipeline,
including paths to raw data (OWID only) and output directories.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


# =====================================================================
# Output paths
# =====================================================================
@dataclass(frozen=True)
class OutputPaths:
    """
    Paths for processed data and outputs.

    Attributes
    ----------
    processed_data_dir : Path
        Directory for processed (cleaned) data artifacts.
    output_dir : Path
        Root output directory.
    figures_dir : Path
        Directory for generated PNG figures.
    tables_dir : Path
        Directory for generated CSV tables.
    """
    processed_data_dir: Path
    output_dir: Path
    figures_dir: Path
    tables_dir: Path


# =====================================================================
# Main config object
# =====================================================================
@dataclass(frozen=True)
class Config:
    """
    Root configuration object for the entire pipeline.

    Attributes
    ----------
    owid_co2_csv : Path
        Path to the Our World in Data CO₂ dataset (CSV).
    paths : OutputPaths
        Output directory configuration.
    """
    owid_co2_csv: Path
    paths: OutputPaths


# =====================================================================
# Config factory
# =====================================================================
def get_config() -> Config:
    """
    Build and return the project configuration.

    Resolves all paths relative to the project root and ensures consistency.

    Returns
    -------
    Config
        Configuration object with dataset and output paths.
    """
    project_root = Path(__file__).resolve().parents[1]

    owid_csv = project_root / "data/owid-co2-data.csv"

    paths = OutputPaths(
        processed_data_dir=project_root / "output/processed",
        output_dir=project_root / "output",
        figures_dir=project_root / "output/figures",
        tables_dir=project_root / "output/tables",
    )

    return Config(
        owid_co2_csv=owid_csv,
        paths=paths,
    )