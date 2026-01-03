"""
src/scenarios.py

Historical analysis helper module.

This module is kept for consistency with the pipeline structure but is intentionally
minimal. All scenario-based analysis has been removed in favor of a purely
descriptive historical analysis using OWID data.

The module serves as a placeholder for potential future scenario analysis,
but the current pipeline focuses exclusively on historical emissions trends
and decomposition analysis (Kaya/LMDI).

If scenario modeling is introduced in the future, this module can be repurposed
to handle scenario-based comparisons and metrics.
"""

from __future__ import annotations

from src.utils import log


def compute_scenario_metrics() -> None:
    """
    Placeholder function.
    
    The current pipeline uses only historical OWID data and does not perform
    scenario-based analysis. This function is retained for structural consistency.
    """
    log("Scenario metrics: skipped (historical analysis only)")