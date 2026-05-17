from __future__ import annotations

import argparse
import cgi
import json
import mimetypes
import os
import re
import shutil
import traceback
import uuid
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlparse

import numpy as np
import pandas as pd

from rootzone_full_etl import (
    EVENT_COLUMNS,
    predict_rootzone_from_master,
    run_pipeline,
)


APP_DIR = Path(__file__).resolve().parent
RUNS_DIR = APP_DIR / "app_runs"
PRESETS_FILE = APP_DIR / "fertilizer_dose_presets.json"
RUN_ID_RE = re.compile(r"^[A-Za-z0-9_-]+$")

DOWNLOAD_FILES = {
    "forecast": "etl_micro_climate_predictions.csv",
    "master": "etl_master_template.csv",
    "applied_master": "rootzone_applied_master.csv",
    "prediction": "etl_rootzone_prediction.csv",
    "events": "rootzone_events_input.csv",
    "anchors": "rootzone_anchor_input.csv",
}

DEFAULT_PRESETS = {
    "version": 1,
    "presets": {
        "A": {
            "label": "Type A normal dose",
            "fertilization_type_a_flag": 1.0,
            "fertilization_type_b_flag": 0.0,
            "amounts": {
                "Phosphoric acid[mg]-H3PO4": 0.0,
                "Monopotassium Phosphate[mg] -KH2PO4": 109.75,
                "Potassium Chloride[mg] - KCL": 82.9,
                "Kortin [mg]": 0.0,
                "Ammonium Nitrate [mg] -NH4NO3": 142.85,
                "Gypsum - CaSO4*2H2O [mg]": 0.0,
            },
        },
        "B": {
            "label": "Type B normal dose",
            "fertilization_type_a_flag": 0.0,
            "fertilization_type_b_flag": 1.0,
            "amounts": {
                "Phosphoric acid[mg]-H3PO4": 0.016437,
                "Monopotassium Phosphate[mg] -KH2PO4": 87.8,
                "Potassium Chloride[mg] - KCL": 94.9,
                "Kortin [mg]": 0.0,
                "Ammonium Nitrate [mg] -NH4NO3": 142.85,
                "Gypsum - CaSO4*2H2O [mg]": 0.0,
            },
        },
    },
}


def load_presets() -> dict:
    if not PRESETS_FILE.exists():
        PRESETS_FILE.write_text(json.dumps(DEFAULT_PRESETS, indent=2), encoding="utf-8")
    data = json.loads(PRESETS_FILE.read_text(encoding="utf-8"))
    presets = data.get("presets", data)
    for key, preset in DEFAULT_PRESETS["presets"].items():
        presets.setdefault(key, preset)
    return {"version": data.get("version", 1), "presets": presets}


def safe_filename(name: str) -> str:
    name = Path(name or "upload.csv").name
    name = re.sub(r"[^A-Za-z0-9_. -]+", "_", name).strip(" .")
    return name or "upload.csv"


def json_default(value):
    if isinstance(value, (pd.Timestamp, datetime)):
        return value.strftime("%Y-%m-%dT%H:%M")
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating,)):
        return float(value)
    raise TypeError(f"Object of type {type(value).__name__} is not JSON serializable")


def json_response(handler: BaseHTTPRequestHandler, payload: dict, status: int = 200) -> None:
    body = json.dumps(payload, default=json_default).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    add_cors_headers(handler)
    handler.send_header("Content-Length", str(len(body)))
    handler.end_headers()
    handler.wfile.write(body)


def text_response(handler: BaseHTTPRequestHandler, body: str, *, content_type: str = "text/html; charset=utf-8") -> None:
    raw = body.encode("utf-8")
    handler.send_response(200)
    handler.send_header("Content-Type", content_type)
    add_cors_headers(handler)
    handler.send_header("Content-Length", str(len(raw)))
    handler.end_headers()
    handler.wfile.write(raw)


def error_response(handler: BaseHTTPRequestHandler, exc: Exception, status: int = 400) -> None:
    json_response(handler, {"ok": False, "error": str(exc)}, status=status)


def allowed_origins() -> list[str]:
    raw = os.environ.get("ALLOWED_ORIGINS", "")
    return [item.strip().rstrip("/") for item in raw.split(",") if item.strip()]


def add_cors_headers(handler: BaseHTTPRequestHandler) -> None:
    origin = (handler.headers.get("Origin") or "").rstrip("/")
    allowed = allowed_origins()
    if "*" in allowed:
        handler.send_header("Access-Control-Allow-Origin", "*")
    elif origin and origin in allowed:
        handler.send_header("Access-Control-Allow-Origin", origin)
        handler.send_header("Vary", "Origin")
    handler.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
    handler.send_header("Access-Control-Allow-Headers", "Content-Type")


def form_value(form: cgi.FieldStorage, name: str, default: str | None = None) -> str | None:
    if name not in form:
        return default
    value = form[name].value
    if value is None:
        return default
    value = str(value).strip()
    return value if value else default


def parse_optional_float(value, default: float | None = None) -> float | None:
    if value is None or str(value).strip() == "":
        return default
    return float(value)


def save_upload(form: cgi.FieldStorage, field: str, run_dir: Path) -> Path:
    if field not in form:
        raise ValueError(f"Missing upload field: {field}")
    item = form[field]
    if isinstance(item, list):
        item = item[0]
    if not getattr(item, "filename", ""):
        raise ValueError(f"No file was uploaded for {field}")

    path = run_dir / safe_filename(item.filename)
    with path.open("wb") as out:
        shutil.copyfileobj(item.file, out)
    return path


def make_run_dir() -> tuple[str, Path]:
    RUNS_DIR.mkdir(parents=True, exist_ok=True)
    run_id = f"{datetime.now():%Y%m%d_%H%M%S}_{uuid.uuid4().hex[:8]}"
    run_dir = RUNS_DIR / run_id
    run_dir.mkdir(parents=True, exist_ok=False)
    return run_id, run_dir


def get_run_dir(run_id: str) -> Path:
    if not RUN_ID_RE.match(run_id or ""):
        raise ValueError("Invalid run id")
    run_dir = (RUNS_DIR / run_id).resolve()
    if not str(run_dir).startswith(str(RUNS_DIR.resolve())) or not run_dir.exists():
        raise FileNotFoundError("Run was not found")
    return run_dir


def timestamp_bounds(master_path: Path) -> tuple[str, str]:
    master = pd.read_csv(master_path, usecols=["timestamp"])
    timestamps = pd.to_datetime(master["timestamp"], errors="coerce")
    return timestamps.min().strftime("%Y-%m-%dT%H:%M"), timestamps.max().strftime("%Y-%m-%dT%H:%M")


def snap_timestamp(master: pd.DataFrame, value: str, label: str) -> tuple[pd.Timestamp, int]:
    if value is None or str(value).strip() == "":
        raise ValueError(f"{label} is required")
    ts = pd.Timestamp(value)
    timestamps = pd.to_datetime(master["timestamp"], errors="coerce")
    diffs = (timestamps - ts).abs()
    idx = int(diffs.idxmin())
    gap = diffs.loc[idx]
    if gap > pd.Timedelta(minutes=6):
        raise ValueError(f"{label} is not close to a 10-minute model timestamp: {ts}")
    return pd.Timestamp(timestamps.loc[idx]), idx


def apply_events(master: pd.DataFrame, events: list[dict], presets: dict) -> pd.DataFrame:
    for col in EVENT_COLUMNS:
        master[col] = pd.to_numeric(master[col], errors="coerce").fillna(0.0)

    applied_rows = []
    for event in events:
        event_time = event.get("time")
        snapped_ts, idx = snap_timestamp(master, event_time, "Event time")
        irrigation_ml = max(0.0, parse_optional_float(event.get("irrigation_ml"), 0.0) or 0.0)
        fert_type = str(event.get("fert_type") or "none").upper()
        multiplier = max(0.0, parse_optional_float(event.get("multiplier"), 1.0) or 1.0)

        if irrigation_ml:
            master.loc[idx, "irrigation_ml_current"] += irrigation_ml

        used_fert = False
        if fert_type in presets:
            preset = presets[fert_type]
            master.loc[idx, "fertilization_flag"] = 1.0
            master.loc[idx, "fertilization_type_a_flag"] = max(
                float(master.loc[idx, "fertilization_type_a_flag"]),
                float(preset.get("fertilization_type_a_flag", 0.0)),
            )
            master.loc[idx, "fertilization_type_b_flag"] = max(
                float(master.loc[idx, "fertilization_type_b_flag"]),
                float(preset.get("fertilization_type_b_flag", 0.0)),
            )
            for col, base_amount in preset.get("amounts", {}).items():
                if col in master.columns:
                    master.loc[idx, col] += float(base_amount) * multiplier
            used_fert = True

        gypsum = max(0.0, parse_optional_float(event.get("gypsum_mg"), 0.0) or 0.0)
        kortin = max(0.0, parse_optional_float(event.get("kortin_mg"), 0.0) or 0.0)
        if gypsum and "Gypsum - CaSO4*2H2O [mg]" in master.columns:
            master.loc[idx, "Gypsum - CaSO4*2H2O [mg]"] += gypsum
            master.loc[idx, "fertilization_flag"] = 1.0
            used_fert = True
        if kortin and "Kortin [mg]" in master.columns:
            master.loc[idx, "Kortin [mg]"] += kortin
            master.loc[idx, "fertilization_flag"] = 1.0
            used_fert = True

        applied_rows.append(
            {
                "requested_time": event_time,
                "applied_time": snapped_ts,
                "irrigation_ml_current": irrigation_ml,
                "fert_type": fert_type if used_fert else "none",
                "dose_multiplier": multiplier if fert_type in presets else 0.0,
                "gypsum_mg": gypsum,
                "kortin_mg": kortin,
            }
        )

    master.attrs["applied_events"] = applied_rows
    return master


def handle_forecast(form: cgi.FieldStorage) -> dict:
    run_id, run_dir = make_run_dir()
    weather_path = save_upload(form, "weather_file", run_dir)
    radiation_path = save_upload(form, "radiation_file", run_dir)

    start_time = form_value(form, "start_time")
    end_time = form_value(form, "end_time")
    planting_date = form_value(form, "planting_date")
    canopy_cover_default = parse_optional_float(form_value(form, "canopy_cover_default"), 0.0)

    result = run_pipeline(
        weather_file=weather_path,
        radiation_file=radiation_path,
        manual_master_file=None,
        output_master_file=run_dir / DOWNLOAD_FILES["master"],
        output_events_template_file=run_dir / "etl_events_template.csv",
        output_anchors_template_file=run_dir / "etl_anchors_template.csv",
        output_crop_template_file=run_dir / "etl_crop_template.csv",
        output_forecast_file=run_dir / DOWNLOAD_FILES["forecast"],
        output_prediction_file=run_dir / DOWNLOAD_FILES["prediction"],
        start_time=start_time,
        end_time=end_time,
        planting_date=planting_date,
        canopy_cover_default=canopy_cover_default or 0.0,
        run_rootzone=False,
    )

    state = {
        "run_id": run_id,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "weather_file": str(weather_path),
        "radiation_file": str(radiation_path),
        "config": {
            "start_time": start_time,
            "end_time": end_time,
            "planting_date": planting_date,
            "canopy_cover_default": canopy_cover_default or 0.0,
        },
    }
    (run_dir / "run_state.json").write_text(json.dumps(state, indent=2), encoding="utf-8")

    ts_min, ts_max = timestamp_bounds(run_dir / DOWNLOAD_FILES["master"])
    return {
        "ok": True,
        "run_id": run_id,
        "forecast_rows": result["forecast_rows"],
        "timestamp_min": ts_min,
        "timestamp_max": ts_max,
        "downloads": {
            "forecast": f"/download/{run_id}/forecast",
            "master": f"/download/{run_id}/master",
        },
    }


def handle_prediction(payload: dict) -> dict:
    run_id = payload.get("run_id")
    run_dir = get_run_dir(run_id)
    master_path = run_dir / DOWNLOAD_FILES["master"]
    if not master_path.exists():
        raise FileNotFoundError("Forecast master file is missing for this run")

    presets = load_presets()["presets"]
    master = pd.read_csv(master_path)
    master["timestamp"] = pd.to_datetime(master["timestamp"], errors="coerce")

    canopy_cover = parse_optional_float(payload.get("canopy_cover"))
    if canopy_cover is not None:
        master["canopy_cover"] = canopy_cover

    days_after_planting = parse_optional_float(payload.get("days_after_planting"))
    if days_after_planting is not None:
        master["days_after_planting"] = days_after_planting

    master = apply_events(master, payload.get("events") or [], presets)

    anchor_ts, anchor_idx = snap_timestamp(master, payload.get("anchor_time"), "Anchor time")
    target_ts, _ = snap_timestamp(master, payload.get("target_time"), "Target time")
    if payload.get("anchor_ph") in (None, "") or payload.get("anchor_ec") in (None, ""):
        raise ValueError("Current pH and EC are required")
    master.loc[anchor_idx, "ph"] = float(payload.get("anchor_ph"))
    master.loc[anchor_idx, "ec_ms"] = float(payload.get("anchor_ec"))

    applied_master_path = run_dir / DOWNLOAD_FILES["applied_master"]
    master.to_csv(applied_master_path, index=False)

    anchor_path = run_dir / DOWNLOAD_FILES["anchors"]
    pd.DataFrame(
        [{"timestamp": anchor_ts, "ph": payload.get("anchor_ph"), "ec_ms": payload.get("anchor_ec")}]
    ).to_csv(anchor_path, index=False)

    events_path = run_dir / DOWNLOAD_FILES["events"]
    pd.DataFrame(master.attrs.get("applied_events", [])).to_csv(events_path, index=False)

    prediction = predict_rootzone_from_master(
        master,
        target_time=target_ts,
        anchor_time=anchor_ts,
    )
    prediction_path = run_dir / DOWNLOAD_FILES["prediction"]
    pd.DataFrame([prediction]).to_csv(prediction_path, index=False)

    return {
        "ok": True,
        "prediction": prediction,
        "snapped_anchor_time": anchor_ts,
        "snapped_target_time": target_ts,
        "downloads": {
            "prediction": f"/download/{run_id}/prediction",
            "applied_master": f"/download/{run_id}/applied_master",
            "events": f"/download/{run_id}/events",
            "anchors": f"/download/{run_id}/anchors",
        },
    }


def send_download(handler: BaseHTTPRequestHandler, run_id: str, kind: str) -> None:
    run_dir = get_run_dir(run_id)
    if kind not in DOWNLOAD_FILES:
        raise ValueError("Unknown download file")
    path = run_dir / DOWNLOAD_FILES[kind]
    if not path.exists():
        raise FileNotFoundError(f"Download is not ready yet: {kind}")

    raw = path.read_bytes()
    content_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    handler.send_response(200)
    handler.send_header("Content-Type", content_type)
    add_cors_headers(handler)
    handler.send_header("Content-Disposition", f'attachment; filename="{path.name}"')
    handler.send_header("Content-Length", str(len(raw)))
    handler.end_headers()
    handler.wfile.write(raw)


def load_dashboard_html() -> str:
    return (APP_DIR / "dashboard_template.html").read_text(encoding="utf-8")


HTML = load_dashboard_html()


class RootzoneHandler(BaseHTTPRequestHandler):
    server_version = "RootzoneDashboard/1.0"

    def log_message(self, format: str, *args) -> None:
        print(f"{self.address_string()} - {format % args}")

    def do_OPTIONS(self) -> None:
        self.send_response(204)
        add_cors_headers(self)
        self.end_headers()

    def do_GET(self) -> None:
        try:
            path = urlparse(self.path).path
            if path == "/":
                text_response(self, HTML)
                return
            if path == "/config.js":
                text_response(self, 'window.ROOTZONE_API_BASE_URL = "";', content_type="application/javascript; charset=utf-8")
                return
            if path == "/api/presets":
                json_response(self, {"ok": True, **load_presets()})
                return
            if path.startswith("/download/"):
                _, _, run_id, kind = path.split("/", 3)
                send_download(self, unquote(run_id), unquote(kind))
                return
            error_response(self, ValueError("Route not found"), status=404)
        except Exception as exc:
            error_response(self, exc, status=400)

    def do_POST(self) -> None:
        try:
            path = urlparse(self.path).path
            if path == "/api/forecast":
                form = cgi.FieldStorage(
                    fp=self.rfile,
                    headers=self.headers,
                    environ={"REQUEST_METHOD": "POST", "CONTENT_TYPE": self.headers.get("Content-Type", "")},
                )
                json_response(self, handle_forecast(form))
                return
            if path == "/api/predict":
                content_length = int(self.headers.get("Content-Length", "0"))
                payload = json.loads(self.rfile.read(content_length).decode("utf-8"))
                json_response(self, handle_prediction(payload))
                return
            error_response(self, ValueError("Route not found"), status=404)
        except Exception as exc:
            print(traceback.format_exc())
            error_response(self, exc, status=400)


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the local rootzone prediction dashboard.")
    parser.add_argument("--host", default=os.environ.get("HOST", "127.0.0.1"))
    parser.add_argument("--port", type=int, default=int(os.environ.get("PORT", "8765")))
    return parser


def main(argv: list[str] | None = None) -> None:
    args = build_arg_parser().parse_args(argv)
    load_presets()
    server = ThreadingHTTPServer((args.host, args.port), RootzoneHandler)
    print(f"Rootzone dashboard running at http://{args.host}:{args.port}")
    server.serve_forever()


if __name__ == "__main__":
    main()
