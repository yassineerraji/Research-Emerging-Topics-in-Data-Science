"""
src/utils.py

Utility functions shared across the sectoral emissions analysis pipeline.

This module contains small, reusable helpers that:
- manage filesystem concerns (directories, file existence),
- standardize saving of outputs (tables and figures),
- provide lightweight validation and logging utilities,
- handle safe numerical operations (e.g., division).

Design principles:
- No domain-specific logic (no climate, no scenarios, no modeling).
- Functions should be generic, predictable, and side-effect aware.
- Utilities should simplify other scripts, not hide complexity.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Iterable, Optional, Union

import numpy as np
import pandas as pd


def ensure_directories_exist(directories: Iterable[Path]) -> None:
    """
    Ensure that a collection of directories exists on disk.

    Parameters
    ----------
    directories : Iterable[pathlib.Path]
        Directories to create if they do not already exist.

    Notes
    -----
    - Directories are created with parents=True and exist_ok=True.
    - This function is idempotent and safe to call multiple times.
    """
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)


def validate_file_exists(path: Path, description: Optional[str] = None) -> None:
    """
    Validate that a required file exists.

    Parameters
    ----------
    path : pathlib.Path
        Path to the file to check.
    description : str, optional
        Human-readable description of the file (used in error messages).

    Raises
    ------
    FileNotFoundError
        If the file does not exist.
    """
    if not path.exists():
        label = description or str(path)
        raise FileNotFoundError(f"Required file not found: {label}")


def save_dataframe(
    df: pd.DataFrame,
    path: Path,
    *,
    index: bool = False
) -> None:
    """
    Save a DataFrame to disk based on file extension.

    Supported formats:
    - .csv
    - .parquet

    Parameters
    ----------
    df : pandas.DataFrame
        DataFrame to save.
    path : pathlib.Path
        Destination file path.
    index : bool, default False
        Whether to write row indices.

    Raises
    ------
    ValueError
        If the file extension is not supported.
    """
    if path.suffix == ".csv":
        df.to_csv(path, index=index)
    elif path.suffix == ".parquet":
        df.to_parquet(path, index=index)
    else:
        raise ValueError(
            f"Unsupported file format for saving DataFrame: {path.suffix}"
        )


def safe_divide(
    numerator: Union[float, np.ndarray, pd.Series],
    denominator: Union[float, np.ndarray, pd.Series],
    default: Union[float, np.ndarray] = np.nan,
) -> Union[float, np.ndarray, pd.Series]:
    """
    Perform safe division, replacing division by zero with a default value.

    Parameters
    ----------
    numerator : float, ndarray, or Series
        Numerator(s).
    denominator : float, ndarray, or Series
        Denominator(s).
    default : float or ndarray, default np.nan
        Default value to use when denominator is zero.

    Returns
    -------
    float, ndarray, or Series
        Result of division with safe handling of zero denominators.
    """
    with np.errstate(divide="ignore", invalid="ignore"):
        result = np.divide(numerator, denominator)
    
    # Replace inf and nan values with default
    if isinstance(result, (np.ndarray, pd.Series)):
        result = np.where(np.isfinite(result), result, default)
    elif not np.isfinite(result):
        result = default
    
    return result


def log(message: str) -> None:
    """
    Print a standardized log message to stdout.

    Parameters
    ----------
    message : str
        Message to log.

    Notes
    -----
    This is intentionally simple. For a course project, a lightweight
    logger is preferable to introducing logging frameworks.
    """
    print(f"[INFO] {message}", file=sys.stdout)