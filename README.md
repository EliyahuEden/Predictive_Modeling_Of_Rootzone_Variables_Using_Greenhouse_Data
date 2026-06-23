# Predictive Modeling of Rootzone Variables Using Greenhouse Data

## Business problem

This project supports greenhouse irrigation and fertigation decisions by estimating root-zone chemistry between sparse manual measurements.

The practical decision is: given recent greenhouse climate, irrigation, fertilizer, canopy, and previous root-zone readings, estimate the current or near-future:

- pH
- EC, measured as `ec_ms`

These predictions can help decide whether fertigation, acid dosing, irrigation volume, or monitoring frequency should be adjusted before root-zone conditions drift too far.

## Dataset

The project combines raw greenhouse operation logs, weather data, microclimate data, canopy measurements, fertilizer schedules, and sparse pH/EC measurements.

Main modeling dataset:

- File: `data/processed/master.csv`
- Notebook working copy: `scripts/master.csv`
- Grain: 10-minute timestamped greenhouse timeline
- Rows: 16,682
- Columns: 20
- Date range: `2025-05-29 01:00:00` to `2025-09-21 21:10:00`
- Labeled pH samples: 109
- Labeled EC samples: 109
- Rows with both pH and EC labels: 109

Important caveats:

- The telemetry is dense, but the true pH/EC labels are sparse.
- The model is trained as a soft sensor: it predicts changes from a known root-zone anchor measurement at time `t0` to a later time `t1`.
- Holdout intervals are created from skipped labeled intervals, not from a large independent production dataset.
- Some processed files are committed because the project is notebook-first and not yet a fully automated data pipeline.

Raw inputs include:

- External weather and radiation data
- Greenhouse logger data
- ET0, temperature, and relative humidity files
- pH and EC measurement workbook
- Irrigation and fertilizer schedule
- Canopy cover values
- Nitrogen samples

## Technical stack

Core stack:

- Python
- Jupyter notebooks
- pandas
- NumPy
- scikit-learn
- XGBoost
- matplotlib
- seaborn
- openpyxl
- joblib

Supporting packages used in parts of the project:

- LightGBM
- SHAP
- Open-Meteo client packages

## Project structure

```text
data/
  raw/                         Original greenhouse, weather, fertigation, and lab files
  processed/                   Cleaned and modeled datasets used by later notebooks

scripts/
  master.csv                   Notebook-local copy of the final merged dataset
  *.ipynb                      Data validation, microclimate, and root-zone modeling notebooks
  exports/                     Final root-zone model evaluation CSVs and predictions
  saved_model/                 Serialized final model and metadata

plots/
  micro climate results/       Microclimate model figures
  model architecture and workflow/
                               Architecture, data sparsity, and workflow diagrams
  PH& EC_Results_24H_Version/  Final 24h root-zone plots and exports
  PH& EC_Results_48H_Version/  Final 48h root-zone plots and exports

rootzone presentation/
  rootzone_presentation.html   Standalone project presentation

README.md
```

## Method

The project is built as a staged modeling workflow.

1. **Ingest raw data**
   Raw weather, logger, fertigation, canopy, and pH/EC files are loaded from `data/raw/`.

2. **Build support signals**
   Upstream notebooks estimate or validate greenhouse context variables such as soil temperature, internal radiation, internal air temperature, relative humidity, and ET0.

3. **Create the master timeline**
   Climate signals, irrigation volume, fertilizer additions, canopy cover, plant age, and sparse pH/EC labels are merged into `master.csv`.

4. **Engineer interval features**
   Root-zone models are trained on intervals from anchor time `t0` to target time `t1`. Features include:

   - anchor pH and EC
   - elapsed hours
   - irrigation and fertilizer totals between `t0` and `t1`
   - ET0 and radiation summaries
   - soil temperature behavior
   - canopy and plant-age features
   - salt buildup and fertilizer recency features
   - pre-anchor history features

5. **Train unified pH and EC model**
   The final root-zone model is a unified multi-output model that predicts both pH change and EC log-change from the same rows and the same feature set.

6. **Validate with walk-forward testing**
   The model is evaluated using walk-forward validation. Training grows through time, and predictions are made only using information available up to the prediction point.

7. **Validate with skipped-interval holdout**
   Separate holdout intervals are removed from training and predicted later. The project includes both 24h and 48h holdout versions.

## Key metrics

Business metrics:

- pH prediction error, measured by MAE
- EC prediction error, measured by MAE
- Improvement over naive carry-forward from the last measured pH/EC value
- Holdout performance on skipped intervals
- Stability in early walk-forward sections, especially the EC warmup-30 stress check

Model metrics:

- MAE
- RMSE
- R2
- Naive MAE
- Gain over naive MAE
- Holdout MAE
- Holdout R2

Current final exports:

- `scripts/exports/v8_final_unified_model_summary_with_ec_warmup30.csv`
- `scripts/exports/v8_final_unified_model_48h_summary_with_ec_warmup30.csv`

### Final 24h unified model

| Target | Warmup | MAE | RMSE | R2 | Holdout MAE | Holdout R2 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| pH | 52 | 0.2976 | 0.3936 | 0.9388 | 0.3165 | 0.9364 |
| EC | 52 | 0.1251 | 0.1739 | 0.9811 | 0.2052 | 0.9237 |
| EC stress | 30 | 0.1625 | 0.2616 | 0.9510 | - | - |

### Final 48h unified model

| Target | Warmup | MAE | RMSE | R2 | Holdout MAE | Holdout R2 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| pH | 52 | 0.3086 | 0.4066 | 0.9347 | 0.2971 | 0.9328 |
| EC | 52 | 0.1200 | 0.1620 | 0.9836 | 0.1275 | 0.9605 |
| EC warmup30 | 30 | 0.1616 | 0.2710 | 0.9474 | - | - |

## Results

Main findings:

- pH can be predicted accurately from interval features, previous pH, climate, irrigation, and acid/fertilizer signals.
- EC benefits strongly from the 48h holdout setup because longer skipped intervals expose the model to more realistic salinity movement.
- The final 48h model improves EC holdout MAE from `0.2052` in the 24h version to `0.1275`.
- The 24h model keeps the best pH walk-forward score, but the 48h model has better pH holdout MAE.
- The EC warmup-30 stress check remains important because early August intervals are sensitive to which skipped rows are removed from training.

## How to run

The repository does not yet include a pinned `requirements.txt` or `environment.yml`.

Recommended local setup:

```bash
python -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip
python -m pip install jupyterlab pandas numpy matplotlib seaborn scikit-learn xgboost lightgbm shap openpyxl openmeteo-requests requests-cache retry-requests joblib
```

Run notebooks from the `scripts/` directory because several notebooks read `master.csv` by relative path:

```bash
cd scripts
jupyter lab
```

Suggested reproduction order:

1. `soil_temp_C_pred.ipynb`
2. `micro_climate_internal_radiation_model.ipynb`
3. `micro_climate_model.ipynb`
4. `micro_climate_real_time_1day.ipynb`
5. `micro_climate_real_time_3day.ipynb`
6. Verify or rebuild `master.csv`
7. Run `Continuous_Rootzone_V8_Unified_Model.ipynb` for the 24h final model
8. Run `Continuous_Rootzone_V8_Unified_Model_48H.ipynb` for the 48h final model

Saved 48h model artifacts:

```text
scripts/saved_model/v8_unified_model_48h_shared_model.joblib
scripts/saved_model/v8_unified_model_48h_model_meta.json
```

## plots

Model architecture:

![Model architecture](plots/model%20architecture%20and%20workflow/model%20architecture.png)

Walk-forward workflow:

![Walk-forward workflow](plots/model%20architecture%20and%20workflow/walk%20forward.png)

48h pH prediction results:

![48h pH true vs predicted](plots/PH%26%20EC_Results_48H_Version/PH/48h_ph_true_vs_predicted.png)

48h pH walk-forward index series:

![48h pH actual vs predicted by index](plots/PH%26%20EC_Results_48H_Version/PH/48h_ph_actual_vs_predicted_index.png)

48h EC prediction results:

![48h EC true vs predicted](plots/PH%26%20EC_Results_48H_Version/EC/48h_ec_true_vs_predicted.png)

48h EC walk-forward index series:

![48h EC actual vs predicted by index](plots/PH%26%20EC_Results_48H_Version/EC/48h_ec_actual_vs_predicted_index.png)

48h holdout pH results:

![48h holdout pH actual vs predicted](plots/PH%26%20EC_Results_48H_Version/HOLDOUT_PH/48h_holdout_ph_actual_vs_predicted.png)

48h holdout pH true vs predicted:

![48h holdout pH true vs predicted](plots/PH%26%20EC_Results_48H_Version/HOLDOUT_PH/48h_holdout_ph_true_vs_predicted.png)

48h holdout EC results:

![48h holdout EC](plots/PH%26%20EC_Results_48H_Version/HOLDOUT_EC/48h_holdout_ec_true_vs_predicted.png)

48h holdout EC interval series:

![48h holdout EC actual vs predicted](plots/PH%26%20EC_Results_48H_Version/HOLDOUT_EC/48h_holdout_ec_actual_vs_predicted.png)

