# Rootzone Prediction Project - ML Pipeline Summary

This document maps the project to the standard workflow a data scientist is expected to follow when building a prediction model. It can be used as the backbone for the project summary, article, or presentation.

## 1. Problem Framing

Goal: predict future rootzone pH and EC from the current measured status, external climate, greenhouse micro-climate, irrigation, fertilizer, and crop-state context.

Why this is needed: last-known-value and simple rolling-average baselines assume the rootzone stays mostly unchanged. In practice, pH and EC respond to irrigation, fertilizer, acid, gypsum/Kortin, evapotranspiration, radiation, temperature, and time since previous events. The final model is necessary because it learns these combined effects.

Project evidence:
- Rootzone dashboard: `dist/rootzone_dashboard_app/`
- Final deployed ETL and inference path: `dist/rootzone_dashboard_app/rootzone_full_etl.py`
- Baseline comparison script: `scripts/baseline_model_comparison.py`

## 2. Data Collection

The project combines multiple data sources:
- External weather and radiation files.
- Internal greenhouse micro-climate measurements and derived predictions.
- Irrigation and fertilizer operational events.
- Rootzone pH and EC measurements.
- Crop-state variables such as canopy cover and days after planting.

Project evidence:
- Master dataset: `scripts/master.csv`
- External-file app ingestion: `dist/rootzone_dashboard_app/rootzone_full_etl.py`
- Uploadable app formats: CSV, Excel, and JSON.

## 3. Data Audit And EDA

The project explicitly deals with the main real-world data problem: pH and EC labels are sparse compared with dense climate data. This affects validation, baseline design, and the way forecast horizons are selected.

What was checked:
- Target distributions for pH and EC.
- Time gaps between labeled pH/EC samples.
- Missing or invalid input values.
- Coverage of weather data before anchor time and through target time.

Generated evidence:
- `plots/project_summary_visualizations/target_distribution_and_label_sparsity.png`
- App pre-flight checks and upload validation in `dist/rootzone_dashboard_app/rootzone_web_app.py`

## 4. ETL And Data Alignment

All sources are transformed into one timestamp-aligned master table. The app now accepts CSV, XLS/XLSX, and JSON weather/radiation inputs and normalizes English and Hebrew column names into the model schema.

Key decisions:
- Use one model-ready timestamp grid.
- Normalize external weather/radiation columns before feature engineering.
- Reject unsupported file formats and alert users about missing columns, bad timestamps, or nonnumeric required values.

Project evidence:
- `read_table`, `normalize_bet_dagan_weather`, and `normalize_bet_dagan_radiation` in `dist/rootzone_dashboard_app/rootzone_full_etl.py`
- Generated master template: `etl_master_template.csv` in app run folders.

## 5. Feature Engineering

The model uses more than raw pH/EC status. It builds operational, climate, horizon, and historical context features.

Feature families:
- Current anchor values: pH and EC at t0.
- Forecast horizon: gap hours from t0 to target.
- Climate summaries: ET0, temperature, radiation, soil temperature, trends.
- Event summaries: irrigation totals, fertilizer totals, acid, salt concentration, recency.
- Historical behavior: recent irrigation/fertilizer accumulation and previous rootzone dynamics.
- Crop state: canopy cover and days after planting.

Project evidence:
- Shared feature builder: `get_features_shared` in `dist/rootzone_dashboard_app/rootzone_full_etl.py`
- Feature importance exports in `scripts/exports/` and `plots/PH& EC_Results_48H_Version/`

## 6. Baseline Strategy

The project compares the final model against baselines that answer different scientific questions:
- Last measured value: is a model needed at all?
- Last 3 and last 5 sample mean: can a simple recent average solve it?
- Historical median: does the target mostly regress to a fixed central value?
- Average delta and gap-bin delta: does only typical drift matter?
- Linear drift: does time horizon alone explain changes?
- Anchor-gap ridge: do current values and target timing explain enough?
- Event ridge: do simple operational variables explain enough?
- Analog kNN: can similar past intervals replace the model?
- Compact ridge: can a smaller interpretable model match performance?

Generated evidence:
- `scripts/exports/baseline_model_comparison_summary.csv`
- `scripts/exports/baseline_model_comparison_predictions.csv`
- `plots/PH& EC_Results_48H_Version/BASELINE_COMPARISON/baseline_mae_comparison.png`
- `plots/project_summary_visualizations/mae_reduction_vs_baselines.png`
- `plots/project_summary_visualizations/absolute_error_distribution_by_baseline.png`

## 7. Validation Design

The project uses validation setups that match the operational prediction problem:
- Walk-forward evaluation: train on the past, predict future samples.
- Skipped-target holdout: test longer gaps and avoid only evaluating easy next-sample predictions.
- Horizon-aware analysis: inspect performance by prediction gap.

Why MAE and R2 are fair together:
- MAE is directly interpretable in pH units and EC mS/cm.
- R2 shows whether the model explains variation better than a mean baseline.
- Because pH and EC have different scales, metrics are interpreted per target rather than averaged blindly.
- Baseline comparisons are essential because high or low R2 can be misleading when target variance is small.

Generated evidence:
- `scripts/exports/v8_final_unified_model_48h_no_rh_eval_ph.csv`
- `scripts/exports/v8_final_unified_model_48h_no_rh_eval_ec.csv`
- `scripts/exports/v8_final_unified_model_48h_no_rh_holdout_detail.csv`
- `plots/project_summary_visualizations/mae_by_prediction_horizon.png`

## 8. Model Building And Selection

The project went through multiple model versions and selected the final unified 48h NoRH rootzone model for deployment. The model is paired with a micro-climate forecast layer so the rootzone model can use predicted greenhouse conditions when future internal measurements are unavailable.

Project evidence:
- Model-development notebooks under `scripts/Continuous_Rootzone_*.ipynb`
- Final exports under `scripts/exports/`
- Saved model files under `dist/rootzone_dashboard_app/`

## 9. Error Analysis

The analysis does not stop at one metric table. It checks:
- pH and EC separately.
- Walk-forward and skip-holdout separately.
- Short and long horizon errors.
- Absolute error distributions rather than only averages.
- Time-series behavior against selected baselines.

Generated evidence:
- `plots/project_summary_visualizations/walk_forward_prediction_trace.png`
- `plots/project_summary_visualizations/skip_holdout_prediction_trace.png`
- Existing per-target plots under `plots/PH& EC_Results_48H_Version/PH/` and `plots/PH& EC_Results_48H_Version/EC/`

## 10. Deployment And Operational Safeguards

The dashboard turns the model into an operational workflow:
- Upload weather and radiation data.
- Generate micro-climate forecast.
- Enter current rootzone pH and EC.
- Enter before-t0 irrigation/fertilizer events.
- Run rootzone prediction and download artifacts.

Safeguards added:
- File format validation for CSV, Excel, and JSON.
- Pop-up alerts for unsupported files, failed forecasts, failed predictions, malformed events, and missing required inputs.
- Live checks for weather coverage, target range, and before-t0 event context.

Project evidence:
- `dist/rootzone_dashboard_app/dashboard_template.html`
- `dist/rootzone_dashboard_app/rootzone_web_app.py`

## Article Narrative

A concise story for the article:

We built a rootzone soft sensor for pH and EC prediction in greenhouse conditions. The main challenge was combining dense climate data with sparse rootzone measurements and irregular operational events. We created a full data pipeline that aligns weather, radiation, micro-climate, irrigation, fertilizer, crop state, and pH/EC targets into model-ready intervals. We validated the model with walk-forward and skipped-target holdout tests and compared it against simple and stronger baselines, including last measured value, rolling means, drift models, event-based ridge regression, analog nearest neighbors, and compact ridge models. The final model consistently reduces error, which demonstrates that the learned operational and climate context is necessary rather than just convenient.
