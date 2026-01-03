# Global Sectoral CO₂ Emissions — A Data-Driven Historical Analysis

## Project Overview

This project is a **clean, reproducible, and data-driven analysis of global CO₂ emissions**, with a specific focus on **sectoral dynamics over time**.  
Rather than relying on complex scenario modeling or speculative projections, the objective is to extract **robust, interpretable insights** from a **high-quality, descriptive dataset**.

The project is designed for the course **“Research & Emerging Topics in Data Science”** and emphasizes:
- methodological clarity,
- data engineering best practices,
- analytical relevance,
- and high-quality visual storytelling.

---

## Central Research Question

> **How have global CO₂ emissions evolved historically across major emitting sectors, and what does this imply about the scale and pace of the decarbonization challenge?**

This question is intentionally **descriptive and diagnostic**, allowing us to:
- understand long-term structural patterns,
- identify sector-specific emission dynamics,
- and assess which sectors represent the largest challenges for future decarbonization.

---

## Data Source

### Primary Dataset (Single Source of Truth)

**Our World in Data — CO₂ and Greenhouse Gas Emissions**

- File: `data/owid-co2-data.csv`
- Maintained by: *Our World in Data (University of Oxford)*
- Coverage:
  - Long historical time series (1750–2024)
  - Global and country-level emissions
  - Sectoral breakdown of CO₂ emissions (coal, oil, gas, cement, flaring, other industry)

For this project:
- We focus exclusively on the **World aggregate** (`country == "World"`).
- We leverage **six sector-specific CO₂ columns**: `coal_co2`, `oil_co2`, `gas_co2`, `cement_co2`, `flaring_co2`, `other_industry_co2`.
- These components sum to the total `co2` column (verified to within 0.001% in recent years).
- No external scenario or projection datasets are used.

This choice ensures:
- maximum data reliability,
- minimal preprocessing ambiguity,
- and strong interpretability of results.

---

## Project Structure

The repository follows a **simple but rigorous structure**, designed for clarity and reproducibility:

```
FinalProject/
├── data/   
├── output/
│   ├── figures/        # Generated plots
│   └── tables/         # Derived summary tables
├── src/
│   ├── config.py       # Centralized configuration (paths)
│   ├── data_ingestion.py
│   ├── data_processing.py
│   ├── modeling.py
│   ├── visualization.py
│   ├── sector_mapping.py
│   └── utils.py
├── main.py             # Single executable entry point
├── requirements.txt
├── README.md
└── LICENSE
```

---

## Pipeline Logic (End-to-End)

The project runs through a **fully automated pipeline**, launched via:

```bash
python main.py
```

### 1. Data Ingestion
- Load the OWID dataset from `data/owid-co2-data.csv`
- Filter to global (World) emissions only
- Validate all required columns exist
- Log component sum verification (coal + oil + gas + cement + flaring + other_industry ≈ total CO₂)

### 2. Data Processing
- Extract sectoral emissions from wide to long format:
  - Input: 6 sector columns (coal_co2, oil_co2, gas_co2, cement_co2, flaring_co2, other_industry_co2)
  - Output: `year | sector | emissions_mtco2`
- Compute sector shares of total emissions by year
- Calculate year-on-year (YoY) changes (absolute and percentage)
- Compute each sector's contribution to annual total change

### 3. Modeling & Metrics
- **Smoothing**: Apply 5-year centered rolling mean to reduce noise
- **Kaya Identity LMDI Decomposition**: Decompose changes in CO₂ into:
  - **Population effect**: contribution from population growth
  - **Affluence effect**: contribution from GDP per capita growth
  - **Intensity effect**: contribution from CO₂/GDP improvement (technology & efficiency)
- Computed for three key periods:
  - 1990 → latest year (long-term trend)
  - 2000 → 2019 (pre-COVID structural change)
  - 2019 → latest year (recent transition including COVID recovery)

### 4. Visualization
Generate 5 publication-ready figures:
- **A)** `total_co2_timeseries.png` — Global CO₂ emissions over time (1750–2024)
- **B)** `sector_emissions_timeseries.png` — Multi-line chart for all 6 sectors
- **C)** `sector_shares_stacked_area.png` — Sectoral composition as stacked area chart
- **D)** `sector_contribution_yoy_latest20.png` — Sector contributions to annual change (last 20 years)
- **E)** `kaya_lmdi_waterfall.png` — Waterfall charts showing LMDI effects by period

All outputs are saved automatically to `output/figures/` and `output/tables/`.


## Methodological Philosophy

This project deliberately prioritizes:

	•	Data quality over model complexity
	•	Interpretability over speculative precision
	•	Reproducibility over ad-hoc analysis

By grounding the analysis in historical evidence, the project provides a solid empirical foundation for discussing climate transition challenges, without over-engineering or misleading scenario artifacts.

## Expected Contributions

By the end of the project, we deliver:

- **Clean, production-ready data pipeline** with full reproducibility
- **Rigorous sectoral emissions analysis** grounded in 275 years of historical data
- **5 high-quality publication-ready visualizations**:
  - Total emissions timeseries
  - Sectoral emissions trajectories  
  - Sectoral composition over time
  - Recent sectoral contributions to change
  - Kaya-LMDI decomposition analysis
- **6 structured CSV outputs**:
  - `world_sector_emissions_long.csv` — Sectoral emissions in long format
  - `world_sector_shares.csv` — Sector shares by year
  - `world_yoy_changes.csv` — Year-on-year changes (absolute & percentage)
  - `world_contribution_to_yoy_total.csv` — Sector contributions to annual Δ
  - `kaya_lmdi_decomposition.csv` — LMDI effects by period
  - `sector_emissions_smoothed.csv` — Smoothed sector timeseries
- **Clear analytical narrative** suitable for an academic report or presentation

---

## Output Files

### Generated Tables (`output/tables/`)
| File | Rows | Description |
|------|------|-------------|
| `world_sector_emissions_long.csv` | 1,083 | Year × Sector emissions |
| `world_sector_shares.csv` | 1,083 | Sector share of total by year |
| `world_yoy_changes.csv` | 1,083 | YoY changes with % |
| `world_contribution_to_yoy_total.csv` | 1,083 | Sector contribution to annual Δ |
| `kaya_lmdi_decomposition.csv` | 3 | LMDI effects for 3 periods |
| `sector_emissions_smoothed.csv` | 1,083 | 5-year smoothed series |

### Generated Figures (`output/figures/`)
- `total_co2_timeseries.png` — Global CO₂ over time
- `sector_emissions_timeseries.png` — 6-sector trajectories
- `sector_shares_stacked_area.png` — Sectoral composition
- `sector_contribution_yoy_latest20.png` — Recent sector contributions
- `kaya_lmdi_waterfall.png` — LMDI decomposition waterfall