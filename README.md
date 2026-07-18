# Predictive Modeling of Root-Zone Variables Using Greenhouse Data

## Abstract

This repository contains the research code, datasets, model artifacts, visualizations, and final academic deliverables for Project 14: predictive modeling of root-zone pH and electrical conductivity (EC) in a greenhouse environment.

The study is framed as a soft-sensing problem. Manual pH and EC measurements in the root zone are sparse, while greenhouse climate, irrigation, fertigation, canopy, and crop-age data are available at a substantially higher temporal resolution. The objective is to estimate short-horizon root-zone chemistry from a recent trusted measurement and the greenhouse conditions observed over the prediction interval.

Final written reports are stored in `docs/`. Local LaTeX build outputs under `report_latex/` and distribution builds under `dist/` are intentionally ignored by Git.

## Project Snapshot

| Category | Description |
| --- | --- |
| Research domain | Greenhouse irrigation and fertigation decision support |
| Prediction targets | Root-zone pH and EC |
| Modeling formulation | Anchor-to-target interval prediction |
| Main dataset | `data/processed/master.csv` |
| Temporal resolution | 10-minute greenhouse timeline |
| Final exported model | 48h unified no-RH model |
| Primary validation | Walk-forward temporal evaluation and skipped-interval holdout |

## Contents

- [Research Objective](#research-objective)
- [Data Sources](#data-sources)
- [Methodology](#methodology)
- [Key Results](#key-results)
- [Repository Structure](#repository-structure)
- [Running the Prediction Notebook](#running-the-prediction-notebook)
- [Reproducing the Research Workflow](#reproducing-the-research-workflow)
- [Representative Figures](#representative-figures)
- [Generated and Local-Only Artifacts](#generated-and-local-only-artifacts)

## Research Objective

The study evaluates whether a data-driven model can provide accurate short-horizon forecasts of:

- root-zone pH
- root-zone EC, measured in mS/cm

The operational use case is decision support for irrigation and fertigation management. Given a trusted pH/EC measurement at anchor time `t0`, the model predicts the root-zone state at a later target time `t1`, using weather, greenhouse microclimate, irrigation, fertilizer, canopy, and crop-age information observed or forecast over the interval.

## Data Sources

The project integrates heterogeneous greenhouse and agronomic data sources:

| Data group | Examples |
| --- | --- |
| External climate | Weather and radiation files |
| Greenhouse microclimate | Internal temperature, relative humidity, radiation, ET0, and soil temperature |
| Operational management | Irrigation volume, fertilizer type, fertilizer mass, and acid inputs |
| Crop-state measurements | Canopy cover and days after planting |
| Laboratory/manual measurements | Sparse root-zone pH, EC, and nitrogen samples |

Main modeling dataset:

| Property | Value |
| --- | --- |
| File | `data/processed/master.csv` |
| Notebook copy | `scripts/master.csv` |
| Rows | 16,693 |
| Columns | 20 |
| Date range | `2025-05-29 01:00:00` to `2025-09-21 23:00:00` |
| Labeled pH samples | 109 |
| Labeled EC samples | 109 |
| Rows with both labels | 109 |

### Data Limitations

- The telemetry is dense, but the ground-truth pH/EC labels are sparse.
- Validation is based on chronological walk-forward splits and skipped labeled intervals rather than a large independent production dataset.
- The model estimates changes from a known anchor measurement; it does not replace direct sensing or agronomic judgment.
- Several notebooks rely on relative paths because the repository remains notebook-centered rather than packaged as a fully automated research pipeline.

## Methodology

The modeling workflow is organized into six stages:

1. **Data ingestion**  
   Raw weather, logger, fertigation, canopy, nitrogen, and pH/EC files are loaded from `data/raw/`.

2. **Microclimate modeling**  
   Supporting greenhouse signals are estimated or validated, including internal radiation, internal air temperature, relative humidity, ET0, and soil temperature.

3. **Master timeline construction**  
   Climate signals, irrigation volume, fertilizer inputs, canopy cover, plant age, and sparse root-zone labels are merged into a unified 10-minute dataset.

4. **Interval feature engineering**  
   Prediction rows are constructed from anchor-target intervals. Features include anchor pH/EC, elapsed time, irrigation and fertilizer totals, ET0 and radiation summaries, soil-temperature behavior, canopy state, plant age, salinity buildup indicators, fertilizer recency, and pre-anchor history.

5. **Unified pH/EC modeling**  
   The final model predicts pH change and EC log-change from a shared feature set. The exported no-RH variant removes dependence on internal relative humidity by using a climate-demand proxy derived from temperature, radiation, and ET0.

6. **Temporal validation**  
   Walk-forward validation preserves chronological ordering. Skipped-interval holdout tests evaluate performance on labeled intervals excluded from training.

## Key Results

Current exported summary: `scripts/exports/v8_final_unified_model_48h_no_rh_summary_with_ec_warmup30.csv`

| Target | Warmup | MAE | RMSE | Naive MAE | Gain | Gain % | R2 | N test | Holdout MAE | Holdout R2 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| pH | 52 | 0.3297 | 0.4143 | 0.8768 | 0.5472 | 62.40 | 0.9321 | 57 | 0.2877 | 0.9325 |
| EC | 52 | 0.1269 | 0.1707 | 0.1961 | 0.0692 | 35.28 | 0.9818 | 57 | 0.1314 | 0.9523 |
| EC warmup30 | 30 | 0.1702 | 0.2755 | 0.2467 | 0.0765 | 31.00 | 0.9456 | 79 | - | - |

Main findings:

- pH can be estimated from interval features, previous pH, climate, irrigation, and acid/fertilizer signals with a substantial improvement over the naive carry-forward baseline.
- EC prediction benefits from interval-level fertigation, irrigation, climate-demand, and salinity-history features.
- The 48h no-RH exported model preserves strong EC performance without requiring internal relative humidity at inference time.
- The EC warmup-30 stress check remains important because early intervals are sensitive to which labeled rows are excluded from training.

## Repository Structure

```text
data/
  raw/                         Original greenhouse, weather, fertigation, and lab files
  processed/                   Cleaned datasets and model-ready timelines

scripts/
  *.ipynb                      Data exploration, microclimate, and root-zone modeling notebooks
  master.csv                   Notebook-local copy of the final merged dataset
  exports/                     Final evaluation CSVs, predictions, and feature importances
  saved_model/                 Serialized 48h model package with RH dependency
  saved_model_no_rh/           Serialized 48h model package without RH dependency

plots/
  micro climate results/       Microclimate performance figures
  model architecture and workflow/
                               Pipeline, architecture, and validation diagrams
  PH& EC_Results_48H_Version/  Final root-zone evaluation plots and exports
  project_summary_visualizations/
                               Summary figures for project-level communication

poster/
  *.pptx, *.pdf                Final project poster

docs/
  *.pdf, *.docx                Final written reports and academic deliverables

README.md
```

## Running the Prediction Notebook

The most portable prediction package is:

```text
scripts/saved_model_no_rh/
```

It contains:

- `predict_rootzone.ipynb`
- `master.csv`
- `v8_unified_model_48h_no_rh_shared_model.joblib`
- `v8_unified_model_48h_no_rh_model_meta.json`
- `micro_climate_3day_unified_model.joblib`

Minimal package installation:

```bash
python -m pip install numpy pandas joblib scikit-learn xgboost
```

Typical execution:

1. Open `scripts/saved_model_no_rh/predict_rootzone.ipynb`.
2. Keep the model files, metadata file, and input CSV in the same folder.
3. Set `TARGET_TIME` or `ANCHOR_TIME` in the first notebook cell only if a specific prediction interval is required.
4. Run all cells and read the printed pH and EC prediction summary.

The model was trained for predictions up to 48 hours after a known pH/EC anchor measurement. The input CSV must include at least 48 hours of history before the selected anchor row.

## Reproducing the Research Workflow

The repository does not currently include a fully pinned research environment file. A practical local setup is:

```bash
python -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip
python -m pip install jupyterlab pandas numpy matplotlib seaborn scikit-learn xgboost lightgbm shap openpyxl openmeteo-requests requests-cache retry-requests joblib
```

Run notebooks from the `scripts/` directory because several notebooks read local files by relative path:

```bash
cd scripts
jupyter lab
```

Suggested notebook order:

1. `soil_temp_C_pred.ipynb`
2. `micro_climate_internal_radiation_model.ipynb`
3. `micro_climate_model.ipynb`
4. `micro_climate_real_time_1day.ipynb`
5. `micro_climate_real_time_3day.ipynb`
6. verify or rebuild `master.csv`
7. `Continuous_Rootzone_V8_Unified_Model.ipynb`
8. `Continuous_Rootzone_V8_Unified_Model_48H.ipynb`
9. `Continuous_Rootzone_V8_Unified_Model_48H_NoRH.ipynb`

## Representative Figures

Model architecture:

![Model architecture](plots/model%20architecture%20and%20workflow/model%20architecture.png)

Walk-forward validation:

![Walk-forward workflow](plots/model%20architecture%20and%20workflow/walk%20forward.png)

Combined 48h pH/EC prediction results:

![Combined 48h pH and EC true vs predicted](plots/PH%26%20EC_Results_48H_Version/combined_ph_ec_true_vs_pred_2x2.png)

48h pH time-indexed prediction:

![48h pH actual vs predicted by index](plots/PH%26%20EC_Results_48H_Version/PH/ph_actual_vs_pred_index.png)

48h EC time-indexed prediction:

![48h EC actual vs predicted by index](plots/PH%26%20EC_Results_48H_Version/EC/ec_actual_vs_pred_index.png)

48h holdout EC parity:

![48h holdout EC true vs predicted](plots/PH%26%20EC_Results_48H_Version/EC/holdout_ec_true_vs_pred.png)
