---
title: Rootzone Soft Sensor
emoji: 🌱
colorFrom: green
colorTo: blue
sdk: docker
pinned: false
license: mit
---

# Rootzone Prediction Dashboard

This folder is the portable dashboard package for the rootzone pH/EC prediction workflow.

The dashboard lets a user:

1. Upload Bet Dagan weather and radiation CSV files.
2. Create a downloadable micro-climate/weather prediction CSV.
3. Enter current pH/EC status and timestamp.
4. Add irrigation, gypsum, Kortin, and type A/B fertilizer events using dose presets.
5. Pick a target prediction time.
6. Run the saved rootzone model and download the prediction outputs.

## Required Files

Keep these files together in this folder:

- `rootzone_web_app.py` - guided browser interface
- `dashboard_template.html` - dashboard UI template
- `rootzone_full_etl.py` - ETL and model feature logic used by the app
- `fertilizer_dose_presets.json` - saved type A/B fertilizer dose values
- `requirements.txt` - Python package list
- `micro_climate_3day_unified_model.joblib` - saved micro-climate model
- `v8_unified_model_48h_no_rh_shared_model.joblib` - saved rootzone model
- `v8_unified_model_48h_no_rh_model_meta.json` - rootzone model metadata

Deployment helpers:

- `run_windows.bat` - double-click Windows runner
- `run_mac_linux.sh` - Mac/Linux runner
- `Dockerfile` - container build file
- `docker-compose.yml` - local Docker runner
- `netlify.toml` - Netlify static frontend config
- `netlify_site/` - static frontend for Netlify
- `.dockerignore` - Docker cleanup rules
- `.gitignore` - ignores runtime output
- `DEPLOYMENT.md` - sharing and hosting instructions

## Run On Windows

Double-click:

```text
run_windows.bat
```

The first run creates a local `.venv` folder and installs the required packages. Later runs are faster.

## Run On Mac Or Linux

```bash
chmod +x run_mac_linux.sh
./run_mac_linux.sh
```

## Run With Docker

```bash
docker compose up --build
```

Then open:

```text
http://127.0.0.1:8765
```

## Run Directly With Python (No Web App)

You can run the full pipeline — micro-climate forecast and rootzone prediction — directly from the command line without the web app or Docker.

### 1. Install required packages

```bash
pip install -r requirements.txt
```

### 2. Build the master CSV and micro-climate forecast

Run this first to generate the editable input templates from your Bet Dagan files:

```bash
python rootzone_full_etl.py \
  --weather-file bet_dagan_weather.csv \
  --radiation-file bet_dagan_radiation.csv \
  --no-rootzone
```

This creates four files in the same folder:

- `etl_master_template.csv` — full master data table
- `etl_micro_climate_predictions.csv` — micro-climate forecast (temp, ET0, radiation)
- `etl_events_template.csv` — template to fill in irrigation and fertilizer events
- `etl_anchors_template.csv` — template to fill in pH and EC anchor measurements

### 3. Fill in the event and anchor templates

Open `etl_events_template.csv` and add your irrigation and fertilizer events for the 48 h before the anchor time.

Open `etl_anchors_template.csv` and add your current pH and EC measurement at the anchor timestamp.

### 4. Run the rootzone prediction

Once the templates are filled in, run the full pipeline with your anchor and target times:

```bash
python rootzone_full_etl.py \
  --weather-file bet_dagan_weather.csv \
  --radiation-file bet_dagan_radiation.csv \
  --events-file etl_events_template.csv \
  --anchors-file etl_anchors_template.csv \
  --anchor-time "2025-09-21 06:30" \
  --target-time "2025-09-21 12:00" \
  --planting-date "2025-04-01"
```

Replace the dates with your actual anchor time, target time, and planting date.

Output: `etl_rootzone_prediction.csv`

### All available arguments

| Argument | Required | Description |
|---|---|---|
| `--weather-file` | Yes | Path to Bet Dagan weather CSV |
| `--radiation-file` | Yes | Path to Bet Dagan radiation CSV |
| `--anchor-time` | Recommended | Current measurement time (`"YYYY-MM-DD HH:MM"`) |
| `--target-time` | Recommended | Prediction target time (`"YYYY-MM-DD HH:MM"`) |
| `--planting-date` | Recommended | Crop planting date (`"YYYY-MM-DD"`) |
| `--canopy-cover-default` | No | Default canopy cover fraction, e.g. `0.98` |
| `--events-file` | No | CSV with irrigation and fertilizer events |
| `--anchors-file` | No | CSV with pH and EC anchor readings |
| `--manual-master-file` | No | Provide a pre-built master CSV instead of generating one |
| `--output-prediction-file` | No | Custom path for the prediction output CSV |
| `--no-rootzone` | No | Only build master and forecast; skip the rootzone prediction |

All model files (`micro_climate_3day_unified_model.joblib`, `v8_unified_model_48h_no_rh_shared_model.joblib`, `v8_unified_model_48h_no_rh_model_meta.json`) must be in the same folder as `rootzone_full_etl.py`.

## Deploy On Hugging Face Spaces

Use:

- SDK: Docker
- Template: Blank
- Hardware: Free CPU

Upload the package files to the Space. The included `Dockerfile` already listens on Hugging Face's required port `7860`.

Ignore the example FastAPI instructions shown by Hugging Face; they are only a generic starter guide.

## Deploy With Netlify

Netlify can host the dashboard frontend, but not the Python model backend. For Netlify deployment:

1. Deploy the backend from this folder with Docker on Render, Railway, Fly.io, or another Python/Docker host.
2. Set backend `ALLOWED_ORIGINS` to your Netlify site URL.
3. Edit `netlify_site/config.js` and set `window.ROOTZONE_API_BASE_URL` to the backend URL.
4. Deploy this folder to Netlify. `netlify.toml` publishes `netlify_site`.

See `DEPLOYMENT.md` for the full checklist.

## Fertilizer Presets

Type A/B normal dose values are stored in:

```text
fertilizer_dose_presets.json
```

Edit that file if the operational normal dose changes. In the dashboard, users choose type A or B and set a dose multiplier such as `1`, `2`, or another value.

Gypsum and Kortin are entered directly in the app. The dose multiplier only applies to type A/B fertilizer presets.

## Runtime Output

The app creates an `app_runs/` folder while it is running. That folder contains uploaded files and generated outputs for each run. It is ignored by git and does not need to be copied for deployment.
