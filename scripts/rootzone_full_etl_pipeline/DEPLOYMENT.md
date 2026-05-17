# Rootzone Dashboard Deployment

This folder is the portable dashboard package. It contains the app code, saved models, fertilizer presets, requirements, and Docker files.

## Share With Another Windows Computer

1. Copy this whole folder:

```text
scripts/rootzone_full_etl_pipeline
```

2. On the other computer, install Python 3.11 or newer.
3. Double-click:

```text
run_windows.bat
```

The first run creates a local `.venv` folder and installs the required packages. Later runs are faster.

## Run On Mac Or Linux

From this folder:

```bash
chmod +x run_mac_linux.sh
./run_mac_linux.sh
```

## Run With Docker

From this folder:

```bash
docker compose up --build
```

Then open:

```text
http://127.0.0.1:8765
```

Without compose:

```bash
docker build -t rootzone-dashboard .
docker run --rm -p 8765:8765 rootzone-dashboard
```

## Deploy On Hugging Face Spaces

Create the Space with:

- SDK: Docker
- Docker template: Blank
- Hardware: Free CPU

Then upload the files from this folder, or upload the contents of `rootzone_dashboard_app.zip`.

Hugging Face Docker Spaces expect the app to listen on port `7860`. The included `Dockerfile` sets:

```text
HOST=0.0.0.0
PORT=7860
```

You do not need to create the example FastAPI files shown by Hugging Face. That is only their default starter example.

## Put It On The Internet

Use the Docker setup for the Python backend. The app listens on `0.0.0.0` inside the container and uses the `PORT` environment variable when provided.

Recommended minimum setup:

- Build from this folder's `Dockerfile`.
- Expose the container port from the `PORT` environment variable, or use port `8765`.
- Put the app behind authentication if it is public.
- Persist `/app/app_runs` if you want uploaded files and predictions to remain after restart.

The app is designed as an operational internal tool. Do not expose it publicly without access control.

## Use Netlify

Netlify should host only the static browser interface. The Python model backend must run somewhere that supports a long-running Python/Docker service, such as Render, Railway, Fly.io, a VM, or another container host.

Recommended Netlify setup:

1. Deploy the backend first using `Dockerfile`.
2. Set these backend environment variables:

```text
HOST=0.0.0.0
PORT=<platform port if required>
ALLOWED_ORIGINS=https://your-netlify-site.netlify.app
```

Use `ALLOWED_ORIGINS=*` only for quick testing. For real use, set the exact Netlify URL.

3. Edit:

```text
netlify_site/config.js
```

Set:

```javascript
window.ROOTZONE_API_BASE_URL = "https://your-backend-url";
```

4. Deploy this folder to Netlify. The included `netlify.toml` publishes:

```text
netlify_site
```

Netlify will serve the frontend, and the frontend will call the Python backend for uploads, model prediction, and downloads.

## Files Needed For Deployment

Required:

- `rootzone_web_app.py`
- `dashboard_template.html`
- `rootzone_full_etl.py`
- `fertilizer_dose_presets.json`
- `requirements.txt`
- `micro_climate_3day_unified_model.joblib`
- `v8_unified_model_48h_no_rh_shared_model.joblib`
- `v8_unified_model_48h_no_rh_model_meta.json`

Helpful:

- `run_windows.bat`
- `run_mac_linux.sh`
- `Dockerfile`
- `docker-compose.yml`
- `.dockerignore`
- `netlify.toml`
- `netlify_site/index.html`
- `netlify_site/config.js`
