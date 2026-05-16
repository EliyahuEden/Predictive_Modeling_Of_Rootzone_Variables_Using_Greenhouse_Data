# Rootzone pH and EC Prediction Package

This folder contains everything needed to run the final unified 48H rootzone model.

## Folder contents

- `predict_rootzone.ipynb` - notebook used for prediction
- `master.csv` - input data file used by default
- `v8_unified_model_48h_shared_model.joblib` - trained hybrid model
- `v8_unified_model_48h_model_meta.json` - model metadata and feature list

Keep the notebook, CSV, model file, and metadata file together in the same folder.

## Python packages needed

The notebook checks these packages before running:

- `numpy`
- `pandas`
- `joblib`
- `scikit-learn`
- `xgboost`

If any package is missing, install it in the notebook environment before running the model.

Example:

```bash
pip install numpy pandas joblib scikit-learn xgboost
```

Use the same Python environment as the training notebook when possible.

## How to run

1. Open `predict_rootzone.ipynb`.
2. Edit only the first code cell if needed.
3. Run all cells.
4. Read the printed pH and EC prediction at the bottom.

The default setup is:

```python
CSV_FILE = None
MODEL_DIR = None
TARGET_TIME = None
ANCHOR_TIME = None
ALLOW_MISSING_INPUT_COLUMNS = False
REQUIRED_HISTORY_HOURS = 48.0
```

With these defaults:

- `MODEL_DIR = None` means the notebook automatically finds this folder because it contains the model and metadata files.
- `CSV_FILE = None` means the notebook uses `master.csv` from this same folder.
- `TARGET_TIME = None` means it predicts the last timestamp in the CSV.
- `ANCHOR_TIME = None` means it uses the most recent earlier row that has both `ph` and `ec_ms`.

## Predicting a specific time

To predict a specific target time, change:

```python
TARGET_TIME = '2025-09-21 21:10'
```

To force a specific anchor measurement, change:

```python
ANCHOR_TIME = '2025-09-21 15:30'
```

The anchor row must contain both measured `ph` and measured `ec_ms`.

## Data requirements

The CSV must contain:

- `timestamp`
- `ph`
- `ec_ms`
- `ET0`
- `internal_air_temp_c`
- `internal_rh_%`
- `internal_radiation`
- `irrigation_ml_current`
- `fertilization_flag`
- `fertilization_type_a_flag`
- `fertilization_type_b_flag`
- `soil_temp_pred`
- `canopy_cover`
- `days_after_planting`
- `Phosphoric acid[mg]-H3PO4`
- `Monopotassium Phosphate[mg] -KH2PO4`
- `Potassium Chloride[mg] - KCL`
- `Kortin [mg]`
- `Ammonium Nitrate [mg] -NH4NO3`
- `Gypsum - CaSO4*2H2O [mg]`

Leave `ALLOW_MISSING_INPUT_COLUMNS = False` for normal use. This makes the notebook stop if a required column is missing.

The notebook also checks that `internal_radiation` has valid values in the 6 hours before the target time. This is needed for the `hist_dark_recent_6h` feature, and prevents missing radiation values from being treated as darkness.

## Timing requirements

The model was trained for predictions up to 48 hours after a known pH/EC measurement.

For a valid prediction:

- The target time must be after the anchor time.
- The target time must be no more than 48 hours after the anchor time.
- The CSV must include at least 48 hours of data before the anchor time.

This is important because the model uses irrigation, fertilizer, climate, and crop history before the anchor and before the target. For example, irrigation or fertilizer 36 hours before the anchor is used correctly if the CSV contains the full 48-hour history window.

If the CSV only starts 36 hours before the anchor, the notebook stops, because it cannot know whether the missing first 12 hours had no activity or missing data.

## Replacing the input data

To use new greenhouse data:

1. Replace `master.csv` with a new CSV that has the same column names.
2. Keep the file name as `master.csv`, or set `CSV_FILE` to the new file name.
3. Make sure the CSV includes at least 48 hours before the selected anchor row.
4. Run all cells in `predict_rootzone.ipynb`.

## Output

The notebook prints:

- anchor time
- anchor pH
- anchor EC
- target time
- prediction gap in hours
- model component used
- predicted pH
- predicted EC

Example output:

```text
ROOTZONE PREDICTION
Anchor time : 2025-09-21 15:30
Anchor pH   : 5.400
Anchor EC   : 3.8700 mS/cm
Target time : 2025-09-21 21:10
Gap         : 5.7 hours
Component   : xgboost
Predicted pH : 5.294
Predicted EC : 3.3145 mS/cm
```
