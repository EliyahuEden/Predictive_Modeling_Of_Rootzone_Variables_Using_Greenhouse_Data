# Predictive Modeling of Rootzone Variables Using Greenhouse Data

This repository contains Jupyter notebooks for building time-series datasets from greenhouse + weather data and training/predicting different targets (micro-climate, internal radiation, soil temperature, and rootzone pH/EC).

## Repository structure

```
data/
  raw/         # source data (original exports; do not edit)
  processed/   # derived datasets, predictions, and metrics
scripts/       # Jupyter notebooks (.ipynb)
plots/         # saved figures (.png)
models/        # saved model artifacts (empty unless you export models)
```

All notebooks in `scripts/` include a small helper cell that defines `ROOT`, `RAW`, `PROCESSED`, `PLOTS`, so paths work even when running notebooks from inside the `scripts/` folder.

## Notebooks (scripts)

### `scripts/soil_temp_C_pred.ipynb` - Soil temperature prediction
Builds a soil temperature time-series prediction based on external weather + radiation.
- Inputs: `data/raw/Data Final OG.csv`, `data/raw/bet_dagan_weather.csv`, `data/raw/bet_dagan_radiation.csv`
- Output: `data/processed/soil_temp_predictions_full_range.csv`

### `scripts/micro_climate_internal_radiation_model.ipynb` - Internal radiation prediction (XGBoost)
Predicts internal greenhouse radiation using external weather + radiation.
- Inputs: `data/raw/radiation.csv`, `data/raw/bet_dagan_weather.csv`, `data/raw/bet_dagan_radiation.csv`
- Output: `data/processed/internal_radiation_predictions_full_weather_range.csv`

### `scripts/micro_climate_model.ipynb` - Micro-climate model (XGBoost)
Predicts greenhouse micro-climate targets (ETo / air temperature / RH) using external weather + radiation time series.
- Inputs: `data/raw/bet_dagan_weather.csv`, `data/raw/bet_dagan_radiation.csv`, `data/processed/rh_et0.csv`
- Output: `data/processed/xgb_predictions_full_weather_range.csv`

### `scripts/micro_climate_real_time_1day.ipynb` - Micro-climate real-time (1-day)
Real-time/rolling micro-climate forecasting on a 1-day horizon.
- Inputs: `data/raw/bet_dagan_weather.csv`, `data/raw/bet_dagan_radiation.csv`, `data/processed/micro_climate_rh_t_et0.xlsx`
- Outputs (current exports): `data/processed/MicroClimate_metrics_all_targets_1day.csv`, `data/processed/MicroClimate_predictions_all_targets_1day.csv`

### `scripts/greenhouse_time_series_walkforward_3day.ipynb` - Greenhouse time-series (3-day)
Walk-forward greenhouse time-series modeling (3-day setup).
- Inputs: `data/raw/bet_dagan_weather.csv`, `data/raw/bet_dagan_radiation.csv`, `data/processed/micro_climate_rh_t_et0.xlsx`
- Outputs (current exports): `data/processed/metrics_all_targets_3day_3daystep.csv`, `data/processed/predictions_all_targets_3day_3daystep.csv`

### `scripts/micro_climate_real_time_3day.ipynb` - Micro-climate real-time (3-day)
Real-time/rolling micro-climate forecasting on a 3-day horizon.
- Inputs: `data/raw/bet_dagan_weather.csv`, `data/raw/bet_dagan_radiation.csv`, `data/processed/micro_climate_rh_t_et0.xlsx`
- Outputs (current exports): `data/processed/metrics_all_targets_3day_3daystep.csv`, `data/processed/predictions_all_targets_3day_3daystep.csv`

### `scripts/RF_Rootzone_Model.ipynb` - Rootzone dataset + features + RF walk-forward
Creates a master dataset (10-minute timeline), engineers event/climate features, and trains a RandomForest to predict changes between pH/EC observation anchors (walk-forward evaluation).
- Inputs:
  - `data/processed/micro_climate_rh_t_et0.xlsx`
  - `data/raw/Irrigation + ALL Elemental Fractions schedule for one plant (100N).xlsx`
  - `data/raw/PH+EC Final.xlsx`
  - `data/raw/Daily Canopy Cover Values.xlsx`
  - `data/processed/soil_temp_predictions_full_range.csv`
- Outputs:
  - `data/processed/master.csv`
  - `data/processed/master_data.csv`
  - `data/processed/rf_rootzone_model_predictions.csv`
  - `data/processed/Rootzone_per_interval_errors.csv`

### `scripts/RF_Rootzone_Realtime.ipynb` - Rootzone real-time evaluation
Real-time/rolling evaluation for rootzone predictions.
- Inputs: same master data sources as `scripts/RF_Rootzone_Model.ipynb`
- Outputs (current exports): `data/processed/rf_rootzone_model_predictions.csv`, `data/processed/Rootzone_per_interval_errors.csv`

### `scripts/target_data_exploration.ipynb` - Target exploration
Explores raw target distributions and sampling behavior for pH/EC and micro-climate.

## Data files

### Raw inputs (`data/raw/`)
These are treated as the source of truth and should not be edited in-place.
- `bet_dagan_weather.csv`: external (Bet Dagan) weather time series used as model inputs.
- `bet_dagan_radiation.csv`: external (Bet Dagan) radiation time series used as model inputs.
- `radiation.csv`: internal radiation sensor/export used as the training target for internal radiation modeling.
- `Data Final OG.csv`: raw dataset used for soil temperature modeling (contains soil temperature observations).
- `Data Logger Final.xlsx`: greenhouse logger export (kept as raw input).
- `T&RH&ETo_10min&daily_10Aug_18Sep.xlsx`: combined/exported micro-climate related data (kept as raw input).
- `PH+EC Final.xlsx`: sparse laboratory/measurement data for pH and EC with timestamps.
- `Irrigation + ALL Elemental Fractions schedule for one plant (100N).xlsx`: irrigation/fertigation schedule events.
- `Daily Canopy Cover Values.xlsx`: daily canopy cover values (joined by date).
- `Nitrogen Samples - one group.xlsx`: nitrogen sampling data (kept as raw input).

### Processed outputs (`data/processed/`)
Derived files created by notebooks; safe to overwrite by re-running notebooks.
- `micro_climate_rh_t_et0.xlsx`: internal micro-climate dataset (10-minute) used as a base timeline for modeling/joins.
- `rh_et0.csv`: processed RH/ET0 time series used by `scripts/micro_climate_model.ipynb`.
- `soil_temp_predictions_full_range.csv`: predicted soil temperature time series (10-minute).
- `internal_radiation_predictions_full_weather_range.csv`: predicted internal radiation time series.
- `internal_radiation_predictions_until_aug10.csv`: internal radiation predictions for a limited weather window.
- `internal_radiation_micro_climate.csv`: merged internal radiation + micro-climate dataset.
- `merged_predictions_internal_radiation.csv`: merged internal radiation predictions for evaluation/plots.
- `xgb_predictions_full_weather_range.csv`: predicted micro-climate targets over the full weather range.
- `xgb_predictions_until_aug10.csv`: predicted micro-climate targets for a limited weather window.
- `master.csv`: master 10-minute dataset (current working export).
- `master_data.csv`: master 10-minute dataset combining micro-climate + events + sparse pH/EC + soil temp + canopy.
- `rf_rootzone_model_predictions.csv`: rootzone RF model predictions at anchor intervals.
- `Rootzone_per_interval_errors.csv`: per-interval pH/EC errors from the walk-forward evaluation.
- `MicroClimate_metrics_all_targets_1day.csv`, `MicroClimate_predictions_all_targets_1day.csv`: 1-day walk-forward metrics/predictions.
- `metrics_all_targets_3day_3daystep.csv`, `predictions_all_targets_3day_3daystep.csv`: 3-day walk-forward metrics/predictions.

## Typical run order (recommended)
If you are rebuilding everything from scratch, a practical order is:
1. `scripts/soil_temp_C_pred.ipynb` -> creates `data/processed/soil_temp_predictions_full_range.csv`
2. `scripts/micro_climate_internal_radiation_model.ipynb` -> creates `data/processed/internal_radiation_predictions_full_weather_range.csv`
3. `scripts/micro_climate_model.ipynb` -> creates `data/processed/xgb_predictions_full_weather_range.csv`
4. `scripts/micro_climate_real_time_1day.ipynb` or `scripts/micro_climate_real_time_3day.ipynb` -> creates greenhouse walk-forward metrics/predictions
5. `scripts/greenhouse_time_series_walkforward_3day.ipynb` -> creates 3-day walk-forward metrics/predictions
6. `scripts/RF_Rootzone_Model.ipynb` or `scripts/RF_Rootzone_Realtime.ipynb` -> creates rootzone master/prediction outputs

