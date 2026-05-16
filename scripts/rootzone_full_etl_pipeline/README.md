# Full ETL Pipeline - Bet Dagan to Rootzone Prediction

This folder now includes a full no-RH prediction pipeline:

1. Load Bet Dagan weather and radiation CSV files.
2. Use `micro_climate_3day_unified_model.joblib` to predict greenhouse climate columns.
3. Create a rootzone `master.csv`-format file.
4. Let the user add irrigation, fertilizer, pH, and EC anchor values.
5. Run `v8_unified_model_48h_no_rh_shared_model.joblib` to predict rootzone pH and EC.

## Files

- `rootzone_full_etl.py` - reusable ETL and prediction code
- `full_etl_rootzone_pipeline.ipynb` - notebook wrapper for easy use
- `micro_climate_3day_unified_model.joblib` - Bet Dagan to greenhouse climate model
- `v8_unified_model_48h_no_rh_shared_model.joblib` - final no-RH rootzone model
- `v8_unified_model_48h_no_rh_model_meta.json` - rootzone feature metadata
- `master.csv` - example filled master file

## Python Packages

The full ETL needs:

```bash
pip install numpy pandas joblib scikit-learn xgboost lightgbm
```

`lightgbm` is required because the micro-climate forecast model was trained with LightGBM.

## Basic Use In The Notebook

Open `full_etl_rootzone_pipeline.ipynb`, edit only the first cell, and run all cells.

For the current project files, the default paths are:

```python
WEATHER_FILE = '../../data/raw/bet_dagan_weather.csv'
RADIATION_FILE = '../../data/raw/bet_dagan_radiation.csv'
MANUAL_MASTER_FILE = 'master.csv'
TARGET_TIME = '2025-09-21 21:10'
```

`MANUAL_MASTER_FILE = 'master.csv'` means the ETL keeps the already filled pH, EC, irrigation, fertilizer, canopy, and planting-day values from the current master file while replacing the climate columns from the weather forecast model.

## Use With New Data

1. Put the new Bet Dagan weather and radiation CSV files in this folder, or point `WEATHER_FILE` and `RADIATION_FILE` to their paths.
2. Set `MANUAL_MASTER_FILE = None`.
3. Run the notebook with `RUN_ROOTZONE_PREDICTION = False`.
4. Open the generated `etl_master_template.csv`.
5. Fill the user-editable columns:
   - `ph`
   - `ec_ms`
   - `irrigation_ml_current`
   - `fertilization_flag`
   - `fertilization_type_a_flag`
   - `fertilization_type_b_flag`
   - fertilizer amount columns
   - `canopy_cover` if not supplied by another file
   - `days_after_planting` if `PLANTING_DATE` was not set
   
Use `0` for confirmed no irrigation or fertilization event. Do not leave event amount/flag cells blank inside the 48-hour history and prediction window.
6. Set `MANUAL_MASTER_FILE = 'etl_master_template.csv'`.
7. Set `RUN_ROOTZONE_PREDICTION = True`.
8. Run the notebook again.

The rootzone prediction is saved to `etl_rootzone_prediction.csv`.

## Important Checks

The ETL stops with a clear error if something required is missing.

Forecast-model checks:

- Bet Dagan timestamps must parse correctly.
- Weather and radiation files must overlap in time.
- Required Bet Dagan weather/radiation columns must exist.
- Large timestamp gaps are blocked by `MAX_EXTERNAL_GAP_HOURS`.
- The engineered forecast features must match the joblib model feature list.

Rootzone-model checks:

- The master file must contain all rootzone input columns.
- The anchor row must contain both `ph` and `ec_ms`.
- The target must be after the anchor and no more than 48 hours after it.
- The master must include 48 hours of rows before the anchor.
- `internal_radiation` must be valid in the 6 hours before the target for `hist_dark_recent_6h`.

Irrigation or fertilizer events 36 hours before the anchor are handled correctly as long as the master file contains the full 48-hour window before the anchor. If the file starts only 36 hours before the anchor, the ETL stops because it cannot know whether the missing first 12 hours had no activity or missing data.

## Command-Line Example

From this folder:

```bash
python rootzone_full_etl.py ^
  --weather-file ../../data/raw/bet_dagan_weather.csv ^
  --radiation-file ../../data/raw/bet_dagan_radiation.csv ^
  --manual-master-file master.csv ^
  --target-time "2025-09-21 21:10"
```

To only create the editable master template:

```bash
python rootzone_full_etl.py ^
  --weather-file ../../data/raw/bet_dagan_weather.csv ^
  --radiation-file ../../data/raw/bet_dagan_radiation.csv ^
  --no-rootzone
```
