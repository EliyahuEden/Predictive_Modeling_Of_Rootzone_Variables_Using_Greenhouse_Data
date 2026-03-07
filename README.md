# Predictive Modeling of Rootzone Variables Using Greenhouse Data

This project develops a machine learning soft-sensor for greenhouse root-zone chemistry.
The soft-sensor predicts:
- `pH` (acidity)
- `EC` (electrical conductivity / salinity)

The practical goal is to replace or reduce dependence on expensive, drifting, or hard-to-maintain physical root-zone sensors by inferring chemical state from available greenhouse signals.

## End Goal

Build a robust, deployment-ready soft-sensor that:
- Predicts current root-zone `pH` and `EC` continuously.
- Remains stable under noisy agricultural data.
- Handles irregular sampling gaps between lab/sensor measurements.
- Learns online (walk-forward retraining) as new true measurements arrive.
- Provides actionable confidence for fertigation and irrigation control decisions.

## Why This Problem Is Hard

Root-zone chemistry behaves like a partially observed dynamic system:
- Time gaps between true `pH/EC` labels are uneven.
- Irrigation/fertigation effects are delayed (biophysical lag and mixing/settling time).
- Greenhouse data is noisy and contains operational disturbances.
- Label count is small relative to high-frequency environmental logs.

In the current `master.csv`, labeled samples are sparse (`109` joint pH/EC points; `108` transitions), with highly variable gaps (median about `6.1h`, long-tail gaps up to about `408h`).

## Modeling Strategy

Core modeling choices used in current root-zone notebooks:
- Walk-forward validation: train on past transitions, predict forward, retrain whenever a new actual root-zone reading arrives.
- Delta modeling: predict `target(t1) - target(t0)` rather than absolute value.
- Anchor-state conditioning: include `ph0` and `ec0` as system state at start of each interval.
- Windowed drivers: irrigation, fertigation, ET0, climate, canopy, event recency, and diurnal features extracted on `[t0, t1)` windows.
- Robust EC objective: pseudohuber loss for EC to reduce sensitivity to outliers/noise.

## Repository Structure

```
data/
  raw/         source files (do not edit)
  processed/   derived datasets, predictions, metrics
scripts/       Jupyter notebooks (.ipynb) and local working CSV copy
plots/         saved figures
```

## Data Overview

### Raw Data (`data/raw/`)

Primary sources used across the pipeline:
- `bet_dagan_weather.csv`: external weather.
- `bet_dagan_radiation.csv`: external radiation.
- `radiation.csv`: internal greenhouse radiation observations.
- `Data Final OG.csv`: original dataset used for soil-temperature modeling.
- `Data Logger Final.xlsx`: greenhouse logger export.
- `T&RH&ETo_10min&daily_10Aug_18Sep.xlsx`: micro-climate base signals.
- `PH+EC Final.xlsx`: sparse pH/EC measurements.
- `Irrigation + ALL Elemental Fractions schedule for one plant (100N).xlsx`: irrigation/fertigation schedule.
- `Daily Canopy Cover Values.xlsx`: crop canopy progression.
- `Nitrogen Samples - one group.xlsx`: additional agronomic sampling.

### Processed Data (`data/processed/`)

Key artifacts already produced:
- `micro_climate_rh_t_et0.xlsx`
- `rh_et0.csv`
- `soil_temp_predictions_full_range.csv`
- `internal_radiation_predictions_full_weather_range.csv`
- `xgb_predictions_full_weather_range.csv`
- `master.csv`
- `rootzone_continuous_model_predictions.csv`
- `rootzone_continuous_model_eval_actual_rows.csv`
- `rf_rootzone_model_predictions.csv`
- `Rootzone_per_interval_errors.csv`
- `MicroClimate_metrics_all_targets_1day.csv`
- `MicroClimate_predictions_all_targets_1day.csv`
- `metrics_all_targets_3day_3daystep.csv`
- `predictions_all_targets_3day_3daystep.csv`

## Scripts and Their Role

### Upstream Feature/Signal Builders

- `scripts/soil_temp_C_pred.ipynb`
  - Predicts soil temperature from weather/radiation context.
  - Produces `data/processed/soil_temp_predictions_full_range.csv`.

- `scripts/micro_climate_internal_radiation_model.ipynb`
  - Models internal radiation from external drivers.
  - Produces `data/processed/internal_radiation_predictions_full_weather_range.csv`.

- `scripts/micro_climate_model.ipynb`
  - Predicts micro-climate targets (ET0, temperature, RH) over full horizon.
  - Produces `data/processed/xgb_predictions_full_weather_range.csv`.

- `scripts/micro_climate_real_time_1day.ipynb`
  - Real-time 1-day walk-forward greenhouse forecasting.
  - Produces `MicroClimate_metrics_all_targets_1day.csv` and `MicroClimate_predictions_all_targets_1day.csv`.

- `scripts/micro_climate_real_time_3day.ipynb`
  - Real-time 3-day walk-forward greenhouse forecasting.

- `scripts/greenhouse_time_series_walkforward_3day.ipynb`
  - 3-day walk-forward evaluation framework.
  - Produces `metrics_all_targets_3day_3daystep.csv` and `predictions_all_targets_3day_3daystep.csv`.

### Root-Zone Modeling Notebooks

- `scripts/Interval_Rootzone_Model.ipynb`
  - Earlier interval-based root-zone modeling baseline.

- `scripts/Continuous_Rootzone_Model_With_Past.ipynb`
  - Continuous root-zone setup with historical context.

- `scripts/Continuous_Rootzone_Only_t0_To_t1.ipynb`
  - Root-zone continuous walk-forward model (V1-style baseline).
  - Delta prediction from anchor `t0` to query time `t1`.

- `scripts/Continuous_Rootzone_Only_t0_To_t1_V2.ipynb`
  - Refined version with weighted recency features and tuned pH parameters.

- `scripts/Continuous_Rootzone_Only_t0_To_t1_V3.ipynb`
  - Current hybrid notebook:
  - pH model setup from V2 (best pH behavior).
  - EC model setup from V1 (best EC behavior).
  - Strict `[t0, t1)` feature window to avoid sample-time leakage.
  - Warmup sweep to select best warmup by target.

- `scripts/Rootzone_Rollout.ipynb`
  - Rollout-style analysis and visualization for root-zone predictions.

- `scripts/target_data_exploration.ipynb`
  - Exploratory analysis of sampling density, target behavior, and distributions.

## Process We Followed to Reach Current Models

1. Built high-frequency greenhouse context signals (micro-climate, radiation, soil temperature).
2. Merged these with irrigation/fertigation schedules and sparse pH/EC labels into `master.csv`.
3. Developed interval and continuous walk-forward root-zone baselines.
4. Switched from absolute target prediction to delta prediction for better state tracking.
5. Added physically meaningful drivers:
   - Irrigation and fertigation totals.
   - Salt/acid effects and concentration proxies.
   - ET0, VPD, canopy, transpiration pull.
   - Event recency and diurnal timing.
6. Added robust EC loss (`reg:pseudohubererror`) to handle noisy/outlier shifts.
7. Iterated V1 -> V2 -> V3 to separate what works best for pH vs EC.

## Current Performance Snapshot

From saved notebook outputs on the same walk-forward setup (`warmup=50`):
- V1 (`Continuous_Rootzone_Only_t0_To_t1.ipynb`)
  - `pH MAE = 0.4542`
  - `EC MAE = 0.1856`
  - Naive baseline: `pH 0.9063`, `EC 0.1918`
- V2 (`Continuous_Rootzone_Only_t0_To_t1_V2.ipynb`)
  - `pH MAE = 0.449994` (improved vs V1)
  - `EC MAE = 0.1875` (slightly worse vs V1)

Interpretation:
- pH gains more from richer climate/recency dynamics.
- EC is more noise-sensitive and benefits from conservative/robust setup.

## What Still Needs to Be Done

Primary next workstream is model optimization and interpretability:
- Re-run and benchmark V3 end-to-end against V1 and V2 using identical folds.
- Expand warmup and retraining strategy search with strict walk-forward boundaries.
- Perform feature-ablation by target to quantify marginal contribution.
- Quantify directional effect size:
  - Which features push pH/EC up or down.
  - How effect changes with gap length and growth stage.
- Improve uncertainty handling:
  - Confidence bands or quantile models.
  - Alerting when the model is extrapolating beyond observed dynamics.
- Add drift monitoring and scheduled recalibration policy for season shifts.
- Package model outputs for operational greenhouse decision support.

## Recommended Rebuild Order

If rebuilding from raw inputs:
1. `scripts/soil_temp_C_pred.ipynb`
2. `scripts/micro_climate_internal_radiation_model.ipynb`
3. `scripts/micro_climate_model.ipynb`
4. `scripts/micro_climate_real_time_1day.ipynb` and/or `scripts/micro_climate_real_time_3day.ipynb`
5. `scripts/greenhouse_time_series_walkforward_3day.ipynb`
6. Root-zone notebooks in sequence:
   - `scripts/Interval_Rootzone_Model.ipynb`
   - `scripts/Continuous_Rootzone_Only_t0_To_t1.ipynb`
   - `scripts/Continuous_Rootzone_Only_t0_To_t1_V2.ipynb`
   - `scripts/Continuous_Rootzone_Only_t0_To_t1_V3.ipynb`

## Notes

- `data/raw/` should remain immutable.
- `data/processed/` files are reproducible artifacts and can be regenerated.
- Keep notebook outputs versioned only when they represent benchmark checkpoints.

