# Predictive Modeling of Rootzone Variables Using Greenhouse Data

This repository is a notebook-first machine learning project for building greenhouse soft sensors.
The main objective is to estimate root-zone chemistry from greenhouse measurements and operational logs, with a focus on:

- `pH`
- `EC` (`ec_ms`, electrical conductivity)

The project also includes upstream models that reconstruct greenhouse context signals such as soil temperature, internal radiation, air temperature, relative humidity, and ET0. Those signals are then merged into a single timeline used by the root-zone models.

## What Is In This Repo

At a high level, the repository contains:

- Raw greenhouse, weather, fertigation, canopy, and root-zone measurement files
- Processed datasets used for modeling
- Jupyter notebooks for feature building, forecasting, validation, and root-zone modeling
- Saved CSV exports from the latest committed root-zone run
- Plots and an HTML presentation summarizing the work
- A written report in Hebrew (`.docx` and `.pdf`) at the repository root

## Repository Snapshot

Key facts from the committed files:

- Canonical merged dataset: `data/processed/master.csv`
- Duplicate working copy for notebooks: `scripts/master.csv`
- `data/processed/master.csv` and `scripts/master.csv` are identical in the current commit
- `master.csv` contains `16,682` timestamped rows and `20` columns
- Non-null labeled targets in `master.csv`:
  - `ph`: `109`
  - `ec_ms`: `109`
- Timestamp range in `master.csv`: `2025-01-06 00:00:00` to `2025-21-09 23:50:00`

This means the project is solving a sparse-label learning problem: dense greenhouse telemetry with relatively few true root-zone measurements.

## Repository Layout

```text
data/
  raw/                  Original source files
  processed/            Derived datasets and committed prediction artifacts
plots/
  micro climate results/
  model architecture and workflow/
  ph model results/
rootzone presentation/
  rootzone_presentation.html
scripts/
  *.ipynb               All modeling notebooks
  exports/              Root-zone evaluation / feature importance CSVs
  master.csv            Notebook-local copy of the merged dataset
README.md
*.docx, *.pdf           Written report artifacts
```

## Data Files

### Raw Data (`data/raw/`)

The raw directory contains the source files used throughout the pipeline:

- `bet_dagan_weather.csv`
- `bet_dagan_radiation.csv`
- `radiation.csv`
- `Data Final OG.csv`
- `Data Logger Final.xlsx`
- `T&RH&ETo_10min&daily_10Aug_18Sep.xlsx`
- `T&RH&ETo_10min&daily_10Aug_18Sep_UPDATED.xlsx`
- `PH+EC Final.xlsx`
- `Irrigation + ALL Elemental Fractions schedule for one plant (100N).xlsx`
- `Daily Canopy Cover Values.xlsx`
- `Nitrogen Samples - one group.xlsx`

These represent the external weather context, greenhouse logger measurements, agronomic interventions, canopy development, and sparse laboratory or field measurements of root-zone chemistry.

### Processed Data (`data/processed/`)

Committed processed outputs currently include:

- `master.csv`
- `micro_climate_rh_t_et0.xlsx`
- `rh_et0.csv`
- `soil_temp_predictions_full_range.csv`
- `internal_radiation_predictions_full_weather_range.csv`
- `internal_radiation_predictions_until_aug10.csv`
- `xgb_predictions_full_weather_range.csv`
- `xgb_predictions_until_aug10.csv`
- `MicroClimate_metrics_all_targets_1day.csv`
- `MicroClimate_predictions_all_targets_1day.csv`
- `MicroClimate_metrics_all_targets_3day.csv`
- `MicroClimate_predictions_all_targets_3day.csv`

The processed directory is the main handoff between the upstream feature-building notebooks and the root-zone notebooks.

## Modeling Pipeline

The project is organized as a staged pipeline:

1. Build or validate external weather inputs.
2. Predict greenhouse support signals:
   - soil temperature
   - internal radiation
   - internal air temperature
   - internal RH
   - ET0
3. Merge those signals with irrigation, fertilizer composition, canopy, and sparse root-zone labels into `master.csv`.
4. Train walk-forward root-zone models that predict the change from anchor time `t0` to future query time `t1`.
5. Export evaluation tables, predictions, feature importances, and training-set growth summaries.

## Notebook Inventory

### Upstream Signal Builders

- `scripts/soil_temp_C_pred.ipynb`
  - Predicts soil temperature from outer weather and radiation.
  - Saved notebook output reports `MAE: 0.393` and `R^2: 0.935`.
  - Writes `soil_temp_predictions_full_range.csv`.

- `scripts/micro_climate_internal_radiation_model.ipynb`
  - Predicts internal greenhouse radiation from external signals.
  - Writes `internal_radiation_predictions_full_weather_range.csv`.

- `scripts/micro_climate_model.ipynb`
  - XGBoost model for `ET0`, internal air temperature, and RH.
  - Writes `xgb_predictions_full_weather_range.csv`.

- `scripts/micro_climate_real_time_1day.ipynb`
  - One-day rolling greenhouse forecast notebook.
  - Writes:
    - `MicroClimate_metrics_all_targets_1day.csv`
    - `MicroClimate_predictions_all_targets_1day.csv`
  - Tracks `internal_air_temp_c`, `internal_radiation`, `ET0`, and `internal_rh_pct`.

- `scripts/micro_climate_real_time_3day.ipynb`
  - Three-day rolling greenhouse forecast notebook.
  - The committed processed outputs are:
    - `MicroClimate_metrics_all_targets_3day.csv`
    - `MicroClimate_predictions_all_targets_3day.csv`

- `scripts/et0_daily_calc.ipynb`
  - Small utility notebook for exporting daily ET0 from the micro-climate workbook.

### Validation and Exploration

- `scripts/validate_openmeteo.ipynb`
  - Compares Open-Meteo features against Bet Dagan / IMS observations.
  - Includes bias-correction experiments and ground-temperature validation.

- `scripts/validate_openmeteo_full.ipynb`
  - Extended validation of weather-derived microclimate features.

- `scripts/target_data_exploration.ipynb`
  - Explores the sparsity and temporal structure of root-zone targets using `master.csv`.

### Root-Zone Model Line

The committed notebook sequence shows an iterative evolution of the soft-sensor:

- `scripts/Continuous_Rootzone_V1.ipynb`
  - Baseline continuous root-zone model.

- `scripts/Continuous_Rootzone_V2.ipynb`
  - Improved pH behavior relative to V1.

- `scripts/Continuous_Rootzone_V3.ipynb`
  - First version that clearly exports evaluation, prediction, feature-importance, gap, and training-size CSVs under `scripts/exports/`.

- `scripts/Continuous_Rootzone_V4.ipynb`
  - "XGBoost + Pre-t0 History Features"
  - Adds a 24-hour history window before `t0` and removes redundant features.

- `scripts/Continuous_Rootzone_V5.ipynb`
  - "XGBoost + Pre-t1 History Features"
  - Shifts the history anchoring toward `t1`.

- `scripts/Continuous_Rootzone_V5_Full.ipynb`
  - Full export-oriented run of the V5 setup.

- `scripts/Continuous_Rootzone_V6.ipynb`
  - "Skip Expanded + Morning Flags + Deep Features"
  - Adds a stronger pH configuration and includes holdout analysis.

- `scripts/Continuous_Rootzone_V7_24h.ipynb`
  - 24-hour rolling holdout evaluation on unseen pairs.

- `scripts/Continuous_Rootzone_V7_48h.ipynb`
  - 48-hour holdout with a 48-hour training cap on unseen pairs.

## Latest Committed Root-Zone Exports

The only committed root-zone export set in `scripts/exports/` is the V6-named set:

- `v6_eval_ph.csv`
- `v6_eval_ec.csv`
- `v6_pred_ph.csv`
- `v6_pred_ec.csv`
- `v6_fi_ph.csv`
- `v6_fi_ec.csv`
- `v6_train_sizes_ph.csv`
- `v6_train_sizes_ec.csv`

These files contain:

- Per-timestamp evaluation rows for pH and EC
- Point predictions
- Feature importances
- Training set size over time

Top committed feature-importance signals in the V6 exports:

- pH:
  - `t1_morning`
  - `t0_morning`
  - `photo_temp_interaction`
  - `transpiration_pull`
  - `ph0`

- EC:
  - `hist_acid_decay`
  - `hist_hrs_since_fert`
  - `log_ec_drive`
  - `ec0`
  - `hist_hrs_since_irr`

## Performance Snapshot From Saved Notebook Outputs

The table below reflects metrics embedded in the committed notebook outputs. These numbers were not recomputed during this `README` update; they were extracted from the saved notebooks.

| Notebook | Evaluation note | pH MAE | pH R2 | EC MAE | EC R2 |
| --- | --- | ---: | ---: | ---: | ---: |
| `Continuous_Rootzone_V1.ipynb` | walk-forward | 0.4637 | 0.8444 | 0.1763 | 0.8137 |
| `Continuous_Rootzone_V2.ipynb` | walk-forward | 0.4410 | 0.8517 | 0.1763 | 0.8137 |
| `Continuous_Rootzone_V3.ipynb` | walk-forward | 0.4000 | 0.8628 | 0.1756 | 0.8185 |
| `Continuous_Rootzone_V4.ipynb` | walk-forward | 0.3896 | 0.8735 | 0.1801 | 0.8202 |
| `Continuous_Rootzone_V5.ipynb` | walk-forward | 0.3942 | 0.8837 | 0.1790 | 0.8211 |
| `Continuous_Rootzone_V6.ipynb` | walk-forward | 0.3360 | 0.9267 | 0.1790 | 0.8211 |
| `Continuous_Rootzone_V7_24h.ipynb` | 43 unseen holdout pairs | 0.3439 | 0.9194 | 0.1790 | 0.8211 |
| `Continuous_Rootzone_V7_48h.ipynb` | 68 unseen holdout pairs | 0.3412 | 0.9214 | 0.1790 | 0.8211 |

Interpretation from the committed runs:

- pH modeling improves materially across versions and clearly beats the naive baseline.
- EC is much harder: the model is only slightly better than the naive carry-forward baseline in the committed outputs.
- The later notebooks focus more on realistic holdout design, not just in-sample walk-forward gains.

## Micro-Climate Evaluation Artifacts

The committed micro-climate evaluation files contain rolling-run metrics for:

- `internal_air_temp_c`
- `internal_radiation`
- `ET0`
- `internal_rh_pct`

Current committed coverage:

- `MicroClimate_metrics_all_targets_1day.csv`: `104` evaluation runs
- `MicroClimate_metrics_all_targets_3day.csv`: `34` evaluation runs

The stored columns include train/test windows, train/test row counts, and MAE/RMSE/R2 per target.

## Plots and Presentation Assets

The `plots/` directory is organized into three groups:

- `plots/micro climate results/`
- `plots/model architecture and workflow/`
- `plots/ph model results/`

Examples include:

- micro-climate prediction figures
- parity plots
- architecture diagrams
- walk-forward workflow visuals
- pH time-series and holdout scatter plots

There is also an HTML presentation at:

- `rootzone presentation/rootzone_presentation.html`

That file is a standalone interactive summary of the root-zone work.

## Environment and Dependencies

This repository does not currently include a pinned environment file such as `requirements.txt`, `environment.yml`, or `pyproject.toml`.

The notebooks import the following Python packages:

- `pandas`
- `numpy`
- `matplotlib`
- `seaborn`
- `scikit-learn`
- `xgboost`
- `lightgbm`
- `shap`
- `openpyxl`
- `openmeteo_requests`
- `requests_cache`
- `retry_requests`

Recommended practical setup:

1. Create a dedicated Python 3.12 environment.
2. Install Jupyter and the packages listed above.
3. Run notebooks from Jupyter Lab or VS Code with the working directory set appropriately.

Example install command:

```bash
pip install jupyterlab pandas numpy matplotlib seaborn scikit-learn xgboost lightgbm shap openpyxl openmeteo-requests requests-cache retry-requests
```

## Reproduction Notes

If you want to rebuild the project from the committed raw data, use this order:

1. `scripts/soil_temp_C_pred.ipynb`
2. `scripts/micro_climate_internal_radiation_model.ipynb`
3. `scripts/micro_climate_model.ipynb`
4. `scripts/micro_climate_real_time_1day.ipynb`
5. `scripts/micro_climate_real_time_3day.ipynb`
6. Build or verify `data/processed/master.csv`
7. Run the root-zone notebooks from `V1` through `V7`

Practical caveats discovered from the committed notebooks:

- The root-zone notebooks read `master.csv` using a relative path, so they expect to run from the `scripts/` directory or require path adjustment.
- `scripts/master.csv` is currently a duplicate of `data/processed/master.csv`; keeping those two files synchronized matters.
- The later root-zone notebooks (`V7_24h` and `V7_48h`) still write export filenames under the `v6_*` naming convention.
- The repository contains committed processed outputs, but not a fully automated rebuild script.

## Current Limitations

This repo is a research workspace rather than a packaged application.

Current limitations:

- Notebook-first workflow instead of a reusable Python package
- No pinned environment file
- Sparse root-zone labels relative to the full telemetry timeline
- EC performance remains close to the naive baseline in the committed runs
- Some output naming conventions have drifted across notebook versions

## Suggested Next Cleanup Steps

If this repository is going to be maintained or shared more broadly, the highest-value cleanup tasks are:

1. Add a real environment file (`requirements.txt` or `environment.yml`).
2. Move shared feature-building logic out of notebooks into reusable Python modules.
3. Make `data/processed/master.csv` the single source of truth and stop duplicating it under `scripts/`.
4. Standardize export filenames so notebook version and output version match.
5. Add a short script or notebook that rebuilds `master.csv` end to end.

## Notes

- Treat `data/raw/` as immutable source data.
- Treat `data/processed/` and `scripts/exports/` as reproducible artifacts.
- The written report files and the HTML presentation are useful summary artifacts, but the notebooks remain the source of truth for the modeling workflow.
