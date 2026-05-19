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

1. Upload weather and radiation files in CSV, Excel, or JSON format.
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

Use Python 3.12 on Windows. The final model was built with Python 3.12.13 and `scikit-learn==1.7.1`; Python 3.14 is not compatible with these pinned model packages on Windows.

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

## Deploy On Hugging Face Spaces

Use:

- SDK: Docker
- Template: Blank
- Hardware: Free CPU

Upload the package files to the Space. The included `Dockerfile` already listens on Hugging Face's required port `7860`.
The Docker image uses Python 3.12 to match the model-building environment.

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
