from __future__ import annotations

import argparse
import importlib.util
import json
import re
import warnings
from pathlib import Path

import numpy as np
import pandas as pd


PACKAGE_DIR = Path(__file__).resolve().parent

MICRO_MODEL_FILE = "micro_climate_3day_unified_model.joblib"
ROOTZONE_MODEL_FILE = "v8_unified_model_48h_no_rh_shared_model.joblib"
ROOTZONE_META_FILE = "v8_unified_model_48h_no_rh_model_meta.json"

ACID_FERTS = ["Phosphoric acid[mg]-H3PO4"]
SALT_FERTS = [
    "Monopotassium Phosphate[mg] -KH2PO4",
    "Potassium Chloride[mg] - KCL",
    "Kortin [mg]",
    "Ammonium Nitrate [mg] -NH4NO3",
    "Gypsum - CaSO4*2H2O [mg]",
]
CORE_SALT_FERTS = [
    "Monopotassium Phosphate[mg] -KH2PO4",
    "Potassium Chloride[mg] - KCL",
    "Ammonium Nitrate [mg] -NH4NO3",
]

ROOTZONE_REQUIRED_COLUMNS = [
    "timestamp",
    "ph",
    "ec_ms",
    "ET0",
    "internal_air_temp_c",
    "internal_radiation",
    "irrigation_ml_current",
    "fertilization_flag",
    "fertilization_type_a_flag",
    "fertilization_type_b_flag",
    "soil_temp_pred",
    "canopy_cover",
    "days_after_planting",
    *ACID_FERTS,
    *SALT_FERTS,
]

MASTER_COLUMNS = [
    "timestamp",
    "ET0",
    "internal_air_temp_c",
    "internal_rh_%",
    "internal_radiation",
    "irrigation_ml_current",
    "fertilization_flag",
    "fertilization_type_a_flag",
    "fertilization_type_b_flag",
    "ph",
    "ec_ms",
    "soil_temp_pred",
    "canopy_cover",
    "days_after_planting",
    "Ammonium Nitrate [mg] -NH4NO3",
    "Monopotassium Phosphate[mg] -KH2PO4",
    "Potassium Chloride[mg] - KCL",
    "Phosphoric acid[mg]-H3PO4",
    "Kortin [mg]",
    "Gypsum - CaSO4*2H2O [mg]",
]

USER_EDITABLE_COLUMNS = [
    "irrigation_ml_current",
    "fertilization_flag",
    "fertilization_type_a_flag",
    "fertilization_type_b_flag",
    "ph",
    "ec_ms",
    "canopy_cover",
    "days_after_planting",
    *ACID_FERTS,
    *SALT_FERTS,
]

EVENT_COLUMNS = [
    "irrigation_ml_current",
    "fertilization_flag",
    "fertilization_type_a_flag",
    "fertilization_type_b_flag",
    *ACID_FERTS,
    *SALT_FERTS,
]

ANCHOR_COLUMNS = ["ph", "ec_ms"]
CROP_COLUMNS = ["canopy_cover", "days_after_planting"]

WEATHER_COLUMNS = [
    "station",
    "timestamp",
    "station_pressure_hpa",
    "rel_humidity_ext",
    "temp_c_ext",
    "temp_max_c_ext",
    "temp_min_c_ext",
    "temp_ground_c_ext",
    "temp_wet_c_ext",
    "wind_dir_deg",
    "gust_dir_deg",
    "wind_speed_ms",
    "wind_speed_max_1m_ms",
    "wind_speed_max_10m_ms",
    "wind_speed_max_10m_time",
    "gust_speed_ms",
    "wind_dir_std_deg",
]

RADIATION_COLUMNS = [
    "rad_station",
    "timestamp",
    "diffuse_rad_wm2",
    "global_rad_wm2",
    "direct_rad_wm2",
]
RADIATION_VALUE_COLUMNS = ["diffuse_rad_wm2", "global_rad_wm2", "direct_rad_wm2"]

BASE_MICRO_FEATURE_COLS = [
    "station_pressure_hpa",
    "rel_humidity_ext",
    "temp_c_ext",
    "temp_max_c_ext",
    "temp_min_c_ext",
    "temp_ground_c_ext",
    "wind_dir_deg",
    "gust_dir_deg",
    "wind_speed_max_1m_ms",
    "wind_speed_max_10m_ms",
    "gust_speed_ms",
    "wind_dir_std_deg",
    "vpd_ext",
    "abs_humidity_ext",
    "dew_point_ext",
    "diffuse_rad_wm2",
    "global_rad_wm2",
    "direct_rad_wm2",
    "hour_of_day",
    "day_of_year",
    "global_rad_wm2_med6",
    "diffuse_rad_wm2_med6",
    "temp_c_ext_med6",
    "rel_humidity_ext_med6",
    "dewpoint_gradient",
    "vpd_ext_rolling_mean_30min",
    "vpd_ext_min_1h",
    "rad_integral_1h",
    "rad_peak_intensity",
    "rad_slope_30m",
    "rad_slope_1h",
    "minutes_since_sunrise",
    "minutes_since_sunset",
]

SOIL_CYCLIC_MICRO_FEATURE_COLS = ["hour_sin", "hour_cos", "doy_sin", "doy_cos"]
ALL_MICRO_FEATURE_COLS = BASE_MICRO_FEATURE_COLS + SOIL_CYCLIC_MICRO_FEATURE_COLS
SUPPORTED_UPLOAD_EXTENSIONS = {".csv", ".xlsx", ".xls", ".json"}

WEATHER_COLUMN_ALIASES = {
    "station": "station",
    "sname": "station",
    "תחנה": "station",
    "timestamp": "timestamp",
    "date": "timestamp",
    "תאריך ושעה (שעון קיץ)": "timestamp",
    "BP": "station_pressure_hpa",
    "לחץ בגובה התחנה (הקטופסקל)": "station_pressure_hpa",
    "RH": "rel_humidity_ext",
    "לחות יחסית (%)": "rel_humidity_ext",
    "TD": "temp_c_ext",
    "טמפרטורה (C°)": "temp_c_ext",
    "TDmax": "temp_max_c_ext",
    "טמפרטורת מקסימום (C°)": "temp_max_c_ext",
    "TDmin": "temp_min_c_ext",
    "טמפרטורת מינימום (C°)": "temp_min_c_ext",
    "TG": "temp_ground_c_ext",
    "טמפרטורה ליד הקרקע (C°)": "temp_ground_c_ext",
    "TW": "temp_wet_c_ext",
    "טמפרטורה לחה (C°)": "temp_wet_c_ext",
    "WD": "wind_dir_deg",
    "כיוון הרוח (מעלות)": "wind_dir_deg",
    "WDmax": "gust_dir_deg",
    "כיוון המשב העליון (מעלות)": "gust_dir_deg",
    "WS": "wind_speed_ms",
    "מהירות רוח (מטר לשניה)": "wind_speed_ms",
    "WS1mm": "wind_speed_max_1m_ms",
    "מהירות רוח דקתית מקסימלית (מטר לשניה)": "wind_speed_max_1m_ms",
    "Ws10mm": "wind_speed_max_10m_ms",
    "מהירות רוח 10 דקתית מקסימלית (מטר לשניה)": "wind_speed_max_10m_ms",
    "Time": "wind_speed_max_10m_time",
    "זמן סיום מהירות רוח 10 דקתית מקסימלית  (hhmm)": "wind_speed_max_10m_time",
    "WSmax": "gust_speed_ms",
    "מהירות המשב העליון (מטר לשניה)": "gust_speed_ms",
    "STDwd": "wind_dir_std_deg",
    "סטיית התקן של כיוון הרוח (מעלות)": "wind_dir_std_deg",
    "Rain": "rain_mm",
    'כמות גשם (מ"מ)': "rain_mm",
}

RADIATION_COLUMN_ALIASES = {
    "rad_station": "rad_station",
    "station": "rad_station",
    "sname": "rad_station",
    "תחנה": "rad_station",
    "timestamp": "timestamp",
    "date": "timestamp",
    "תאריך ושעה (שעון קיץ)": "timestamp",
    "DiffR": "diffuse_rad_wm2",
    'קרינה מפוזרת (וואט/מ"ר)': "diffuse_rad_wm2",
    "Grad": "global_rad_wm2",
    'קרינה גלובלית (וואט/מ"ר)': "global_rad_wm2",
    "NIP": "direct_rad_wm2",
    'קרינה ישירה (וואט/מ"ר)': "direct_rad_wm2",
}


def check_required_packages(include_micro_model: bool = True) -> None:
    required = [
        ("numpy", "numpy"),
        ("pandas", "pandas"),
        ("joblib", "joblib"),
        ("sklearn", "scikit-learn"),
        ("xgboost", "xgboost"),
    ]
    if include_micro_model:
        required.append(("lightgbm", "lightgbm"))

    missing = [install_name for import_name, install_name in required if importlib.util.find_spec(import_name) is None]
    if missing:
        raise ModuleNotFoundError(
            "Missing Python packages needed for the ETL/rootzone pipeline: "
            + ", ".join(missing)
            + ". Install them before running this pipeline."
        )


def _import_joblib():
    check_required_packages(include_micro_model=False)
    import joblib

    try:
        from sklearn.exceptions import InconsistentVersionWarning

        warnings.filterwarnings("ignore", category=InconsistentVersionWarning)
    except Exception:
        pass
    warnings.filterwarnings("ignore", message=".*If you are loading a serialized model.*", category=UserWarning)
    return joblib


def resolve_path(path_like: str | Path | None, *, base_dir: Path = PACKAGE_DIR, default: Path | None = None) -> Path:
    if path_like is None or str(path_like).strip() == "":
        if default is None:
            raise ValueError("No path was provided")
        return default.resolve()

    raw = Path(path_like)
    if raw.is_absolute():
        return raw.resolve()

    candidates = [
        base_dir / raw,
        Path.cwd() / raw,
        Path.cwd() / "scripts" / raw,
        Path.cwd().parent / raw,
        Path.cwd().parent / "scripts" / raw,
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate.resolve()
    return (base_dir / raw).resolve()


def resolve_output_path(path_like: str | Path, *, base_dir: Path = PACKAGE_DIR) -> Path:
    raw = Path(path_like)
    if raw.is_absolute():
        return raw.resolve()
    if raw.parent == Path("."):
        return (base_dir / raw).resolve()
    return (Path.cwd() / raw).resolve()


def _clean_column_name(name) -> str:
    return re.sub(r"\s+", " ", str(name).replace("\ufeff", "")).strip()


def _read_json_table(path: Path) -> pd.DataFrame:
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    if isinstance(data, list):
        return pd.json_normalize(data)
    if isinstance(data, dict):
        for preferred_key in ("data", "records", "rows", "items", "values"):
            value = data.get(preferred_key)
            if isinstance(value, list):
                return pd.json_normalize(value)
        list_values = [value for value in data.values() if isinstance(value, list)]
        if list_values:
            best = max(list_values, key=len)
            return pd.json_normalize(best)
        return pd.json_normalize([data])
    raise ValueError("JSON input must contain an object or an array of row objects")


def read_table(path: str | Path, *, label: str = "Input file") -> pd.DataFrame:
    path = Path(path)
    ext = path.suffix.lower()
    if ext not in SUPPORTED_UPLOAD_EXTENSIONS:
        allowed = ", ".join(sorted(SUPPORTED_UPLOAD_EXTENSIONS))
        raise ValueError(f"{label} must be a CSV, Excel, or JSON file ({allowed}); got '{ext or 'no extension'}'.")

    try:
        if ext == ".csv":
            df = pd.read_csv(path, encoding="utf-8-sig")
        elif ext in {".xlsx", ".xls"}:
            df = pd.read_excel(path, sheet_name=0)
        else:
            df = _read_json_table(path)
    except Exception as exc:
        raise ValueError(f"Could not read {label} '{path.name}': {exc}") from exc

    if df.empty:
        raise ValueError(f"{label} '{path.name}' is empty.")
    df = df.dropna(axis=0, how="all").dropna(axis=1, how="all")
    df.columns = [_clean_column_name(col) for col in df.columns]
    if df.empty or len(df.columns) == 0:
        raise ValueError(f"{label} '{path.name}' does not contain tabular data.")
    return df


def read_csv(path: str | Path) -> pd.DataFrame:
    return read_table(path, label="Input file")


def _apply_column_aliases(df: pd.DataFrame, aliases: dict[str, str]) -> pd.DataFrame:
    out = df.copy()
    out.columns = [aliases.get(_clean_column_name(col), _clean_column_name(col)) for col in out.columns]
    return out


def _to_numeric_column(series: pd.Series) -> pd.Series:
    if pd.api.types.is_numeric_dtype(series):
        return pd.to_numeric(series, errors="coerce")
    cleaned = series.astype("string").str.strip()
    cleaned = cleaned.replace(
        {
            "": pd.NA,
            "-": pd.NA,
            "--": pd.NA,
            "---": pd.NA,
            "NA": pd.NA,
            "N/A": pd.NA,
            "nan": pd.NA,
            "NaN": pd.NA,
            "null": pd.NA,
        }
    )
    cleaned = cleaned.str.replace(",", "", regex=False)
    return pd.to_numeric(cleaned, errors="coerce")


def _coerce_required_numeric(out: pd.DataFrame, required: list[str], *, label: str) -> None:
    missing = [c for c in required if c not in out.columns]
    if missing:
        raise ValueError(f"{label} is missing columns required by the forecast model: {missing}")
    bad_counts = {
        c: int(pd.to_numeric(out[c], errors="coerce").isna().sum())
        for c in required
    }
    bad_counts = {c: n for c, n in bad_counts.items() if n}
    if bad_counts:
        details = ", ".join(f"{col}: {count}" for col, count in bad_counts.items())
        raise ValueError(
            f"{label} has non-numeric or missing values in required columns. "
            f"Fix these columns and upload again: {details}"
        )


def _parse_timestamp_column(df: pd.DataFrame, *, dayfirst: bool = True) -> pd.DataFrame:
    if "timestamp" not in df.columns:
        raise ValueError("Input file must contain a timestamp column after normalization")
    out = df.copy()
    out["timestamp"] = pd.to_datetime(out["timestamp"], dayfirst=dayfirst, format="mixed", errors="coerce")
    bad = int(out["timestamp"].isna().sum())
    if bad:
        raise ValueError(f"Found {bad} timestamp values that could not be parsed")
    return out.sort_values("timestamp").drop_duplicates("timestamp", keep="last").reset_index(drop=True)


def normalize_bet_dagan_weather(weather: pd.DataFrame) -> pd.DataFrame:
    out = _apply_column_aliases(weather, WEATHER_COLUMN_ALIASES)
    if "timestamp" not in out.columns:
        if len(out.columns) != len(WEATHER_COLUMNS):
            raise ValueError(
                "Weather file does not contain recognized headers and does not match the expected weather column count"
            )
        out.columns = WEATHER_COLUMNS
    if "station" in out.columns:
        out = out.drop(columns=["station"])
    out = _parse_timestamp_column(out, dayfirst=True)

    for col in out.columns:
        if col != "timestamp":
            out[col] = _to_numeric_column(out[col])
    out = out.drop(columns=[c for c in out.columns if c != "timestamp" and out[c].isna().all()])

    required = [
        "station_pressure_hpa",
        "rel_humidity_ext",
        "temp_c_ext",
        "temp_max_c_ext",
        "temp_min_c_ext",
        "temp_ground_c_ext",
        "wind_dir_deg",
        "gust_dir_deg",
        "wind_speed_max_1m_ms",
        "wind_speed_max_10m_ms",
        "gust_speed_ms",
        "wind_dir_std_deg",
    ]
    _coerce_required_numeric(out, required, label="Weather file")
    return out


def normalize_bet_dagan_radiation(radiation: pd.DataFrame) -> pd.DataFrame:
    out = _apply_column_aliases(radiation, RADIATION_COLUMN_ALIASES)
    if "timestamp" not in out.columns:
        if len(out.columns) != len(RADIATION_COLUMNS):
            raise ValueError(
                "Radiation file does not contain recognized headers and does not match the expected radiation column count"
            )
        out.columns = RADIATION_COLUMNS
    if "rad_station" in out.columns:
        out = out.drop(columns=["rad_station"])
    if "station" in out.columns:
        out = out.drop(columns=["station"])
    out = _parse_timestamp_column(out, dayfirst=True)

    for col in out.columns:
        if col != "timestamp":
            out[col] = _to_numeric_column(out[col])
    out = out.drop(columns=[c for c in out.columns if c != "timestamp" and out[c].isna().all()])

    missing = [c for c in RADIATION_VALUE_COLUMNS if c not in out.columns]
    if missing:
        raise ValueError(f"Radiation file is missing columns required by the forecast model: {missing}")

    available_global = out["global_rad_wm2"].notna()
    global_missing = out["global_rad_wm2"].isna()
    direct_or_diffuse_available = out["direct_rad_wm2"].notna() | out["diffuse_rad_wm2"].notna()
    out.loc[global_missing & direct_or_diffuse_available, "global_rad_wm2"] = (
        out.loc[global_missing & direct_or_diffuse_available, ["direct_rad_wm2", "diffuse_rad_wm2"]]
        .fillna(0.0)
        .sum(axis=1)
    )

    for col in ("diffuse_rad_wm2", "direct_rad_wm2"):
        if out[col].notna().sum() == 0 and out["global_rad_wm2"].notna().sum() > 0:
            out[col] = 0.0

    low_global = available_global & (out["global_rad_wm2"] <= 5)
    for col in ("diffuse_rad_wm2", "direct_rad_wm2"):
        out.loc[low_global & out[col].isna(), col] = 0.0

    unusable = [col for col in RADIATION_VALUE_COLUMNS if out[col].notna().sum() == 0]
    if unusable:
        raise ValueError(f"Radiation file has no usable numeric values in required columns: {unusable}")

    for col in RADIATION_VALUE_COLUMNS:
        out[col] = out[col].clip(lower=0)
    return out


def _max_gap_hours(timestamps: pd.Series) -> float:
    ts = pd.Series(pd.to_datetime(timestamps)).dropna().sort_values()
    if len(ts) < 2:
        return 0.0
    return float(ts.diff().dropna().max().total_seconds() / 3600.0)


def calculate_saturation_vapor_pressure(temp_c):
    return 0.61078 * np.exp((17.27 * temp_c) / (temp_c + 237.3))


def calculate_vpd(temp_c, rh_pct):
    es = calculate_saturation_vapor_pressure(temp_c)
    ea = es * (rh_pct / 100.0)
    return es - ea


def calculate_absolute_humidity(temp_c, rh_pct):
    return (6.112 * np.exp((17.67 * temp_c) / (temp_c + 243.5)) * rh_pct * 2.1674) / (273.15 + temp_c)


def engineer_micro_climate_features(
    weather: pd.DataFrame,
    radiation: pd.DataFrame,
    *,
    start_time: str | pd.Timestamp | None = None,
    end_time: str | pd.Timestamp | None = None,
    max_external_gap_hours: float = 3.0,
) -> pd.DataFrame:
    weather = normalize_bet_dagan_weather(weather)
    radiation = normalize_bet_dagan_radiation(radiation)

    weather_gap = _max_gap_hours(weather["timestamp"])
    radiation_gap = _max_gap_hours(radiation["timestamp"])
    if weather_gap > max_external_gap_hours:
        raise ValueError(f"Weather file has a {weather_gap:.1f}h timestamp gap, above the allowed {max_external_gap_hours:.1f}h")
    if radiation_gap > max_external_gap_hours:
        raise ValueError(
            f"Radiation file has a {radiation_gap:.1f}h timestamp gap, above the allowed {max_external_gap_hours:.1f}h"
        )

    overlap_start = max(weather["timestamp"].min(), radiation["timestamp"].min())
    overlap_end = min(weather["timestamp"].max(), radiation["timestamp"].max())
    if overlap_start >= overlap_end:
        raise ValueError(f"Weather and radiation files do not overlap in time: {overlap_start} -> {overlap_end}")

    requested_start = pd.Timestamp(start_time) if start_time is not None else overlap_start
    requested_end = pd.Timestamp(end_time) if end_time is not None else overlap_end
    if requested_start > overlap_end or requested_end < overlap_start:
        raise ValueError(
            "Requested prediction range is outside the uploaded weather/radiation overlap. "
            f"Available overlap is {overlap_start:%Y-%m-%d %H:%M} -> {overlap_end:%Y-%m-%d %H:%M}."
        )

    start = max(requested_start, overlap_start)
    end = min(requested_end, overlap_end)
    start = start.ceil("10min")
    end = end.floor("10min")
    if start >= end:
        raise ValueError(f"Invalid prediction range: {start} -> {end}")

    weather["vpd_ext"] = calculate_vpd(weather["temp_c_ext"], weather["rel_humidity_ext"])
    weather["abs_humidity_ext"] = calculate_absolute_humidity(weather["temp_c_ext"], weather["rel_humidity_ext"])
    weather["dew_point_ext"] = weather["temp_c_ext"] - ((100 - weather["rel_humidity_ext"]) / 5)

    merged = weather.merge(radiation, on="timestamp", how="outer").sort_values("timestamp")
    merged = merged[(merged["timestamp"] >= start) & (merged["timestamp"] <= end)]
    full_range = pd.date_range(start, end, freq="10min")
    model_frame = merged.set_index("timestamp").reindex(full_range)
    model_frame.index.name = "timestamp"

    exogenous_cols = [c for c in model_frame.columns if c != "timestamp"]
    model_frame[exogenous_cols] = model_frame[exogenous_cols].interpolate(method="time").bfill().ffill()
    model_frame = model_frame.reset_index()

    model_frame["hour_of_day"] = model_frame["timestamp"].dt.hour
    model_frame["day_of_year"] = model_frame["timestamp"].dt.dayofyear
    hour_float = model_frame["timestamp"].dt.hour + model_frame["timestamp"].dt.minute / 60.0
    model_frame["hour_sin"] = np.sin(2 * np.pi * hour_float / 24.0)
    model_frame["hour_cos"] = np.cos(2 * np.pi * hour_float / 24.0)
    model_frame["doy_sin"] = np.sin(2 * np.pi * model_frame["day_of_year"] / 365.25)
    model_frame["doy_cos"] = np.cos(2 * np.pi * model_frame["day_of_year"] / 365.25)

    smooth_cols = ["global_rad_wm2", "diffuse_rad_wm2", "direct_rad_wm2", "temp_c_ext", "rel_humidity_ext"]
    for col in smooth_cols:
        if col in model_frame.columns:
            model_frame[f"{col}_med6"] = model_frame[col].rolling(window=6, min_periods=1).median()

    model_frame["vpd_ext_calc"] = calculate_vpd(model_frame["temp_c_ext"], model_frame["rel_humidity_ext"])
    model_frame["dew_point_ext_calc"] = model_frame["temp_c_ext"] - ((100 - model_frame["rel_humidity_ext"]) / 5)
    model_frame["dewpoint_gradient"] = model_frame["dew_point_ext_calc"] - model_frame["temp_c_ext"]
    model_frame["vpd_ext_rolling_mean_30min"] = model_frame["vpd_ext_calc"].rolling(window=3, min_periods=1).mean()
    model_frame["vpd_ext_min_1h"] = model_frame["vpd_ext_calc"].rolling(window=6, min_periods=1).min()

    model_frame["rad_integral_1h"] = model_frame["global_rad_wm2"].rolling(window=6, min_periods=1).sum()
    model_frame["rad_peak_intensity"] = model_frame["global_rad_wm2"].rolling(window=6, min_periods=1).max()
    model_frame["rad_slope_30m"] = model_frame["global_rad_wm2"].diff(periods=3)
    model_frame["rad_slope_1h"] = model_frame["global_rad_wm2"].diff(periods=6)
    model_frame["rad_is_low"] = model_frame["global_rad_wm2"] <= 5
    model_frame["sunrise_flag"] = (~model_frame["rad_is_low"]) & (model_frame["rad_is_low"].shift(1, fill_value=True))
    model_frame["sunset_flag"] = model_frame["rad_is_low"] & (~model_frame["rad_is_low"].shift(1, fill_value=False))
    sunrise_groups = model_frame["sunrise_flag"].cumsum()
    sunset_groups = model_frame["sunset_flag"].cumsum()
    model_frame["minutes_since_sunrise"] = model_frame.groupby(sunrise_groups).cumcount() * 10
    model_frame.loc[model_frame["rad_is_low"], "minutes_since_sunrise"] = np.nan
    model_frame["minutes_since_sunset"] = model_frame.groupby(sunset_groups).cumcount() * 10
    model_frame.loc[~model_frame["rad_is_low"], "minutes_since_sunset"] = np.nan

    missing_features = [c for c in ALL_MICRO_FEATURE_COLS if c not in model_frame.columns]
    if missing_features:
        raise ValueError(f"Missing engineered forecast features: {missing_features}")
    return model_frame


def load_micro_climate_bundle(model_path: str | Path | None = None) -> dict:
    check_required_packages(include_micro_model=True)
    joblib = _import_joblib()
    path = resolve_path(model_path, default=PACKAGE_DIR / MICRO_MODEL_FILE)
    if not path.exists():
        raise FileNotFoundError(f"Micro-climate forecast model not found: {path}")

    bundle = joblib.load(path)
    required_keys = ["models", "target_cols", "feature_cols_by_target"]
    missing = [k for k in required_keys if k not in bundle]
    if missing:
        raise ValueError(f"Micro-climate model bundle is missing required keys: {missing}")

    required_targets = ["internal_air_temp_c", "ET0", "internal_radiation", "soil_temp_C"]
    missing_targets = [t for t in required_targets if t not in bundle["models"]]
    if missing_targets:
        raise ValueError(f"Micro-climate model bundle is missing target models required by rootzone: {missing_targets}")
    return bundle


def forecast_micro_climate(model_frame: pd.DataFrame, bundle: dict) -> pd.DataFrame:
    out = pd.DataFrame({"timestamp": model_frame["timestamp"]})
    for target in bundle["target_cols"]:
        if target not in bundle["models"]:
            continue
        cols = list(bundle["feature_cols_by_target"].get(target, bundle.get("feature_cols", [])))
        missing = [c for c in cols if c not in model_frame.columns]
        if missing:
            raise ValueError(f"Cannot predict {target}; missing forecast features: {missing}")
        preds = np.asarray(bundle["models"][target].predict(model_frame[cols]), dtype=float)
        if target == "internal_rh_pct":
            preds = np.clip(preds, 0, 100)
        if target in ("ET0", "internal_radiation"):
            preds = np.clip(preds, 0, None)
        out[f"pred_{target}"] = preds

    required_pred_cols = [
        "pred_internal_air_temp_c",
        "pred_ET0",
        "pred_internal_radiation",
        "pred_soil_temp_C",
    ]
    missing_preds = [c for c in required_pred_cols if c not in out.columns]
    if missing_preds:
        raise ValueError(f"Forecast output is missing required rootzone climate predictions: {missing_preds}")
    return out


def _has_path(path_like: str | Path | None) -> bool:
    return path_like is not None and str(path_like).strip() != ""


def _read_time_keyed_manual_file(path_like: str | Path, *, label: str) -> tuple[pd.DataFrame, Path]:
    path = resolve_path(path_like)
    if not path.exists():
        raise FileNotFoundError(f"{label} not found: {path}")

    manual = read_table(path, label=label)
    if "timestamp" not in manual.columns:
        raise ValueError(f"{label} must contain a timestamp column")

    manual["timestamp"] = pd.to_datetime(manual["timestamp"], errors="coerce", format="mixed")
    if manual["timestamp"].isna().any():
        raise ValueError(f"{label} contains timestamps that could not be parsed")

    manual = manual.sort_values("timestamp").drop_duplicates("timestamp", keep="last").set_index("timestamp")
    return manual, path


def _merge_manual_time_file(
    master: pd.DataFrame,
    *,
    file_path: str | Path | None,
    columns: list[str],
    label: str,
    blank_numeric_fill: float | None = None,
    update_non_missing_only: bool = False,
    warn_ignored_rows: bool = False,
) -> pd.DataFrame:
    if not _has_path(file_path):
        return master

    manual, path = _read_time_keyed_manual_file(file_path, label=label)
    usable_cols = [col for col in columns if col in manual.columns]
    if not usable_cols:
        raise ValueError(f"{label} has no usable columns. Expected at least one of: {', '.join(columns)}")

    indexed = master.set_index("timestamp")
    common_index = indexed.index.intersection(manual.index)
    if common_index.empty:
        raise ValueError(f"{label} has no timestamps that match the generated master grid: {path}")

    ignored = manual.index.difference(indexed.index)
    if len(ignored) and warn_ignored_rows:
        warnings.warn(
            f"{label} contains {len(ignored)} timestamp rows outside the generated master range/grid; those rows were ignored.",
            RuntimeWarning,
        )

    for col in usable_cols:
        values = pd.to_numeric(manual.loc[common_index, col], errors="coerce")
        if blank_numeric_fill is not None:
            values = values.fillna(blank_numeric_fill)
        if update_non_missing_only:
            values = values[values.notna()]
            if values.empty:
                continue
            indexed.loc[values.index, col] = values
        else:
            indexed.loc[common_index, col] = values

    return indexed.reset_index()


def _manual_template_window(
    master: pd.DataFrame,
    *,
    target_time: str | pd.Timestamp | None = None,
    anchor_time: str | pd.Timestamp | None = None,
    required_history_hours: float = 48.0,
    max_prediction_gap_hours: float = 48.0,
) -> pd.DataFrame:
    if master.empty:
        return master.copy()

    timestamps = pd.to_datetime(master["timestamp"])
    start_ts = timestamps.min()
    end_ts = timestamps.max()

    if target_time is not None:
        target_ts = pd.Timestamp(target_time)
        end_ts = target_ts
        if anchor_time is not None:
            anchor_ts = pd.Timestamp(anchor_time)
            start_ts = anchor_ts - pd.Timedelta(hours=required_history_hours)
        else:
            start_ts = target_ts - pd.Timedelta(hours=required_history_hours + max_prediction_gap_hours)
    elif anchor_time is not None:
        anchor_ts = pd.Timestamp(anchor_time)
        start_ts = anchor_ts - pd.Timedelta(hours=required_history_hours)

    window = master.loc[(timestamps >= start_ts) & (timestamps <= end_ts)].copy()
    if window.empty:
        return master.copy()
    return window


def write_manual_input_templates(
    master: pd.DataFrame,
    *,
    output_events_template_file: str | Path | None = None,
    output_anchors_template_file: str | Path | None = None,
    output_crop_template_file: str | Path | None = None,
    target_time: str | pd.Timestamp | None = None,
    anchor_time: str | pd.Timestamp | None = None,
    required_history_hours: float = 48.0,
) -> dict[str, str]:
    window = _manual_template_window(
        master,
        target_time=target_time,
        anchor_time=anchor_time,
        required_history_hours=required_history_hours,
    )
    paths: dict[str, str] = {}

    if _has_path(output_events_template_file):
        events_path = resolve_output_path(output_events_template_file)
        events_path.parent.mkdir(parents=True, exist_ok=True)
        window[["timestamp", *EVENT_COLUMNS]].to_csv(events_path, index=False)
        paths["events"] = str(events_path)

    if _has_path(output_anchors_template_file):
        anchors_path = resolve_output_path(output_anchors_template_file)
        anchors_path.parent.mkdir(parents=True, exist_ok=True)
        if anchor_time is not None:
            anchor_ts = pd.Timestamp(anchor_time)
            anchors = master.loc[pd.to_datetime(master["timestamp"]) == anchor_ts, ["timestamp", *ANCHOR_COLUMNS]]
            if anchors.empty:
                anchors = window[["timestamp", *ANCHOR_COLUMNS]]
        else:
            anchors = window[["timestamp", *ANCHOR_COLUMNS]]
        anchors.to_csv(anchors_path, index=False)
        paths["anchors"] = str(anchors_path)

    if _has_path(output_crop_template_file):
        crop_path = resolve_output_path(output_crop_template_file)
        crop_path.parent.mkdir(parents=True, exist_ok=True)
        window[["timestamp", *CROP_COLUMNS]].to_csv(crop_path, index=False)
        paths["crop"] = str(crop_path)

    return paths


def create_master_template(
    climate_predictions: pd.DataFrame,
    *,
    manual_master_file: str | Path | None = None,
    events_file: str | Path | None = None,
    anchors_file: str | Path | None = None,
    crop_file: str | Path | None = None,
    planting_date: str | pd.Timestamp | None = None,
    canopy_cover_default: float = 0.0,
) -> pd.DataFrame:
    master = pd.DataFrame(
        {
            "timestamp": pd.to_datetime(climate_predictions["timestamp"]),
            "ET0": climate_predictions["pred_ET0"],
            "internal_air_temp_c": climate_predictions["pred_internal_air_temp_c"],
            "internal_rh_%": climate_predictions.get("pred_internal_rh_pct", np.nan),
            "internal_radiation": climate_predictions["pred_internal_radiation"],
            "soil_temp_pred": climate_predictions["pred_soil_temp_C"],
        }
    )

    for col in USER_EDITABLE_COLUMNS:
        if col not in master.columns:
            master[col] = np.nan if col in ("ph", "ec_ms") else 0.0

    master["canopy_cover"] = canopy_cover_default
    if planting_date is not None:
        planted = pd.Timestamp(planting_date)
        master["days_after_planting"] = (
            master["timestamp"].dt.normalize() - planted.normalize()
        ).dt.days.clip(lower=0)
    else:
        master["days_after_planting"] = 0

    master = _merge_manual_time_file(
        master,
        file_path=manual_master_file,
        columns=USER_EDITABLE_COLUMNS,
        label="Manual master file",
    )
    master = _merge_manual_time_file(
        master,
        file_path=events_file,
        columns=EVENT_COLUMNS,
        label="Events file",
        blank_numeric_fill=0.0,
        warn_ignored_rows=True,
    )
    master = _merge_manual_time_file(
        master,
        file_path=anchors_file,
        columns=ANCHOR_COLUMNS,
        label="Anchors file",
        update_non_missing_only=True,
        warn_ignored_rows=True,
    )
    master = _merge_manual_time_file(
        master,
        file_path=crop_file,
        columns=CROP_COLUMNS,
        label="Crop file",
        update_non_missing_only=True,
        warn_ignored_rows=True,
    )

    for col in MASTER_COLUMNS:
        if col not in master.columns:
            master[col] = np.nan if col in ("ph", "ec_ms") else 0.0
    master = master[MASTER_COLUMNS].sort_values("timestamp").reset_index(drop=True)
    return master


def _to_num(s, default=0.0):
    return pd.to_numeric(s, errors="coerce").fillna(default)


def _sum_avail(frame, cols):
    available = [c for c in cols if c in frame.columns]
    if not available:
        return 0.0
    return float(frame[available].apply(pd.to_numeric, errors="coerce").fillna(0.0).sum().sum())


def _sum_avail_series(frame, cols):
    available = [c for c in cols if c in frame.columns]
    if not available:
        return pd.Series(0.0, index=frame.index)
    return frame[available].apply(pd.to_numeric, errors="coerce").fillna(0.0).sum(axis=1)


def _get_fert_any(frame):
    if "fertilization_flag" in frame.columns:
        return _to_num(frame["fertilization_flag"])
    has_a = "fertilization_type_a_flag" in frame.columns
    has_b = "fertilization_type_b_flag" in frame.columns
    if has_a or has_b:
        flag_a = _to_num(frame["fertilization_type_a_flag"]) if has_a else pd.Series(0.0, index=frame.index)
        flag_b = _to_num(frame["fertilization_type_b_flag"]) if has_b else pd.Series(0.0, index=frame.index)
        return ((flag_a > 0) | (flag_b > 0)).astype(float)
    return pd.Series(0.0, index=frame.index)


def _segment(master_df, start, stop):
    if pd.Timestamp(start) >= pd.Timestamp(stop):
        return master_df.iloc[0:0]
    return master_df.loc[(master_df.index >= pd.Timestamp(start)) & (master_df.index < pd.Timestamp(stop))]


def get_window_features(master_df, anchor_idx, current_idx):
    t0 = pd.Timestamp(anchor_idx)
    t1 = pd.Timestamp(current_idx)
    ph0 = float(master_df.loc[t0, "ph"])
    ec0 = float(master_df.loc[t0, "ec_ms"])
    gap_h = float((t1 - t0).total_seconds() / 3600.0)
    safe_gap_h = max(gap_h, 0.16)
    seg = _segment(master_df, t0, t1)

    irr_s = _to_num(seg["irrigation_ml_current"]) if "irrigation_ml_current" in seg.columns else pd.Series(0.0, index=seg.index)
    irr_total = float(irr_s.sum()) if len(seg) else 0.0
    fert_salt_total = _sum_avail(seg, SALT_FERTS)
    h3po4_total = _sum_avail(seg, ACID_FERTS)

    ET0_sum = float(_to_num(seg["ET0"]).sum()) if "ET0" in seg.columns else 0.0
    ET0_per_hour = float(ET0_sum / safe_gap_h)
    salt_conc_t0_t1 = float(fert_salt_total / (irr_total + 1.0))
    irr_to_et0 = float(irr_total / (ET0_sum + 0.1))

    if "internal_air_temp_c" in seg.columns and len(seg) > 0:
        temp_s = _to_num(seg["internal_air_temp_c"])
        es_s = 0.6108 * np.exp((17.27 * temp_s) / (temp_s + 237.3))
        rad_s_tmp = _to_num(seg["internal_radiation"]) if "internal_radiation" in seg.columns else pd.Series(0.0, index=seg.index)
        rad_per_hour_tmp = float(rad_s_tmp.sum() / safe_gap_h) if len(rad_s_tmp) > 0 else 0.0
        climate_demand_proxy = float(
            es_s.mean() * (0.35 + np.log1p(max(rad_per_hour_tmp, 0.0)) / 8.0) + 0.10 * ET0_per_hour
        )
    else:
        temp_s = pd.Series(dtype=float)
        climate_demand_proxy = 0.0

    soil_temp_mean = float(_to_num(seg["soil_temp_pred"]).mean()) if "soil_temp_pred" in seg.columns and len(seg) > 0 else 0.0
    canopy = float(_to_num(seg["canopy_cover"]).mean()) if "canopy_cover" in seg.columns and len(seg) > 0 else 0.0
    climate_demand_pull = float(climate_demand_proxy * canopy)
    climate_demand_soil = float(climate_demand_proxy * soil_temp_mean)
    temp_x_canopy = float(soil_temp_mean * canopy)
    temp_trend = float(temp_s.iloc[-1] - temp_s.iloc[0]) if len(temp_s) > 1 else 0.0

    rad_morning = (
        float(_to_num(seg.loc[(seg.index.hour >= 6) & (seg.index.hour < 12), "internal_radiation"]).sum())
        if len(seg) > 0 and "internal_radiation" in seg.columns
        else 0.0
    )

    fert_any = _get_fert_any(seg) if len(seg) > 0 else pd.Series(dtype=float)
    fert_times = fert_any[fert_any > 0].index
    hrs_since_fert = float((t1 - fert_times.max()).total_seconds() / 3600.0) if len(fert_times) > 0 else gap_h

    core_salt_s = _sum_avail_series(seg, CORE_SALT_FERTS) if len(seg) > 0 else pd.Series(0.0, index=seg.index)
    salt_event_idx = core_salt_s[core_salt_s > 0].index.max() if len(core_salt_s[core_salt_s > 0]) else None
    last_salt_dose = float(core_salt_s.loc[salt_event_idx]) if salt_event_idx is not None else 0.0
    last_irr_amount = float(irr_s.loc[salt_event_idx]) if salt_event_idx is not None and salt_event_idx in irr_s.index else 0.0
    hrs_since_last_salt_event = float((t1 - salt_event_idx).total_seconds() / 3600.0) if salt_event_idx is not None else gap_h
    last_event_salt_conc = float(last_salt_dose / (last_irr_amount + 1.0))
    irr_after_last_salt = (
        float(_to_num(seg.loc[seg.index > salt_event_idx, "irrigation_ml_current"]).sum())
        if salt_event_idx is not None and "irrigation_ml_current" in seg.columns
        else 0.0
    )

    hour_b = t1.hour + t1.minute / 60.0
    days_after_planting_t1 = float(master_df.loc[t1, "days_after_planting"]) if "days_after_planting" in master_df.columns else 0.0

    t1_soil = (
        _to_num(master_df.loc[t1:t1, "soil_temp_pred"]).iloc[0]
        if t1 in master_df.index and master_df.loc[t1, "soil_temp_pred"] != 0
        else float(_to_num(seg["soil_temp_pred"]).iloc[-1]) if len(seg) > 0 and "soil_temp_pred" in seg.columns else 0.0
    )
    t0_soil = float(_to_num(master_df.loc[t0:t0, "soil_temp_pred"]).iloc[0]) if "soil_temp_pred" in master_df.columns else 0.0
    rad_t1 = (
        float(_to_num(master_df.loc[t1:t1, "internal_radiation"]).iloc[0])
        if t1 in master_df.index and "internal_radiation" in master_df.columns
        else 0.0
    )

    return {
        "ph0": ph0,
        "ec0": ec0,
        "gap_hours": gap_h,
        "irr_total_t0_t1": irr_total,
        "fert_salt_total_t0_t1": fert_salt_total,
        "ET0_sum_t0_t1": ET0_sum,
        "ET0_per_hour": ET0_per_hour,
        "h3po4_total": h3po4_total,
        "log_ec_drive": float(np.log((fert_salt_total + h3po4_total) / (irr_total + 1.0) + 0.01) - np.log(ec0 + 0.01)),
        "soil_temp_mean": soil_temp_mean,
        "climate_demand_pull": climate_demand_pull,
        "climate_demand_soil": climate_demand_soil,
        "temp_x_canopy": temp_x_canopy,
        "salt_conc_t0_t1": salt_conc_t0_t1,
        "irr_to_et0": irr_to_et0,
        "stage_x_salt_conc": float((days_after_planting_t1 / 100.0) * salt_conc_t0_t1),
        "ec_log_anchor": float(np.log(ec0 + 0.05)),
        "hrs_since_fert": hrs_since_fert,
        "hrs_since_last_salt_event": hrs_since_last_salt_event,
        "last_event_salt_conc": last_event_salt_conc,
        "irr_after_last_salt": irr_after_last_salt,
        "temp_trend": temp_trend,
        "hour_sin_b": float(np.sin(2 * np.pi * hour_b / 24.0)),
        "hour_cos_b": float(np.cos(2 * np.pi * hour_b / 24.0)),
        "t1_morning_short": int((5 <= t1.hour <= 10) and (gap_h <= 1.5)),
        "t1_early_day": int(5 <= hour_b < 13.0),
        "soil_delta": float(t1_soil - t0_soil),
        "rad_t1_log": float(np.log1p(rad_t1)),
        "rad_morning": rad_morning,
    }


def get_history_features(master_df, t0, t1):
    t1 = pd.Timestamp(t1)
    recent_6h = _segment(master_df, t1 - pd.Timedelta(hours=6), t1)
    prior_12_24h = _segment(master_df, t1 - pd.Timedelta(hours=24), t1 - pd.Timedelta(hours=12))
    hist24 = _segment(master_df, t1 - pd.Timedelta(hours=24), t1)

    def _irr(seg):
        return float(_to_num(seg["irrigation_ml_current"]).sum()) if "irrigation_ml_current" in seg.columns and len(seg) > 0 else 0.0

    hist_irr_recent = _irr(recent_6h)
    hist_irr_prior = _irr(prior_12_24h)
    hist_dark_recent_6h = (
        float((_to_num(recent_6h["internal_radiation"]) <= 10).sum()) / 6.0
        if "internal_radiation" in recent_6h.columns and len(recent_6h) > 0
        else 0.0
    )

    hist_acid_decay = 0.0
    if len(hist24) > 0:
        acid_doses = _sum_avail_series(hist24, ACID_FERTS)
        acid_mask = acid_doses > 0
        if acid_mask.any():
            hrs_before_t1 = np.array((t1 - hist24.index[acid_mask]).total_seconds()) / 3600.0
            hist_acid_decay = float((acid_doses[acid_mask].values * np.exp(-0.34 * hrs_before_t1)).sum())

    if len(hist24) > 1:
        hist_irr_s = _to_num(hist24["irrigation_ml_current"]) if "irrigation_ml_current" in hist24.columns else pd.Series(0.0, index=hist24.index)
        salt_s = _sum_avail_series(hist24, SALT_FERTS)
        salt_mask = salt_s > 0
        if salt_mask.any():
            hrs_before_t1 = np.array((t1 - hist24.index[salt_mask]).total_seconds()) / 3600.0
            decayed_salt = float((salt_s[salt_mask].values * np.exp(-0.15 * hrs_before_t1)).sum())
        else:
            decayed_salt = 0.0
        hist_salt_buildup = float(decayed_salt - float(hist_irr_s.sum()) * 0.1)
        fert_any = _get_fert_any(hist24)
        fert_times = hist24.index[fert_any > 0]
        hist_hrs_since_fert = float((t1 - fert_times[-1]).total_seconds() / 3600.0) if len(fert_times) > 0 else 24.0
    else:
        hist_salt_buildup = 0.0
        hist_hrs_since_fert = 24.0

    return {
        "hist_irr_recent": hist_irr_recent,
        "hist_irr_prior": hist_irr_prior,
        "hist_dark_recent_6h": hist_dark_recent_6h,
        "hist_acid_decay": hist_acid_decay,
        "hist_salt_buildup": hist_salt_buildup,
        "hist_hrs_since_fert": hist_hrs_since_fert,
    }


def get_target_prevday_features(master_df, t1):
    t1 = pd.Timestamp(t1)
    prevday = _segment(master_df, t1 - pd.Timedelta(hours=48), t1 - pd.Timedelta(hours=24))
    return {
        "hist48_irr_prevday": (
            float(_to_num(prevday["irrigation_ml_current"]).sum())
            if "irrigation_ml_current" in prevday.columns and len(prevday) > 0
            else 0.0
        )
    }


def get_features_shared(master_df, anchor_idx, current_idx):
    feats = {
        **get_window_features(master_df, anchor_idx, current_idx),
        **get_history_features(master_df, t0=anchor_idx, t1=current_idx),
        **get_target_prevday_features(master_df, t1=current_idx),
    }

    t0 = pd.Timestamp(anchor_idx)

    def _pre_irr(seg):
        return float(_to_num(seg["irrigation_ml_current"]).sum()) if "irrigation_ml_current" in seg.columns and len(seg) > 0 else 0.0

    def _pre_salt_dw(seg, t_ref):
        if len(seg) == 0:
            return 0.0
        salt_cols = [c for c in SALT_FERTS if c in seg.columns]
        if not salt_cols:
            return 0.0
        s = seg[salt_cols].apply(pd.to_numeric, errors="coerce").fillna(0).sum(axis=1)
        sm = s > 0
        if not sm.any():
            return 0.0
        hrs_ago = np.array((pd.Timestamp(t_ref) - seg.index[sm]).total_seconds()) / 3600.0
        return float((s[sm].values * np.exp(-0.15 * hrs_ago)).sum())

    pre6h_seg = _segment(master_df, t0 - pd.Timedelta(hours=6), t0)
    pre24h_seg = _segment(master_df, t0 - pd.Timedelta(hours=24), t0)
    irr_6h = _pre_irr(pre6h_seg)
    irr_24h = _pre_irr(pre24h_seg)
    salt_6h = _pre_salt_dw(pre6h_seg, t0)
    salt_24h = _pre_salt_dw(pre24h_seg, t0)

    pre_salt_irr_ratio_6h = float(salt_6h / (irr_6h + 1.0))
    pre_salt_irr_ratio_24h = float(salt_24h / (irr_24h + 1.0))

    hist24_t0 = _segment(master_df, t0 - pd.Timedelta(hours=24), t0)
    if len(hist24_t0) > 1:
        hi_s = _to_num(hist24_t0["irrigation_ml_current"]) if "irrigation_ml_current" in hist24_t0.columns else pd.Series(0.0, index=hist24_t0.index)
        pre_anchor_salt_buildup = float(_pre_salt_dw(hist24_t0, t0) - float(hi_s.sum()) * 0.1)
    else:
        pre_anchor_salt_buildup = 0.0

    gap_h_safe = max(float(feats["gap_hours"]), 0.25)
    hist48_pre_t0 = _segment(master_df, t0 - pd.Timedelta(hours=48), t0)
    salt48_pre_t0 = float(_sum_avail(hist48_pre_t0, SALT_FERTS)) if len(hist48_pre_t0) > 0 else 0.0

    positive_pre_anchor_salt_buildup = max(pre_anchor_salt_buildup, 0.0)
    salt_carryover_pressure = float(positive_pre_anchor_salt_buildup * np.exp(-gap_h_safe / 8.0))
    ec_salt_carryover_pressure = float(feats["ec0"] * np.log1p(positive_pre_anchor_salt_buildup) * np.exp(-gap_h_safe / 8.0))

    feats.update(
        {
            "pre_salt_irr_ratio_6h": pre_salt_irr_ratio_6h,
            "pre_salt_irr_ratio_24h": pre_salt_irr_ratio_24h,
            "pre_anchor_salt_buildup": pre_anchor_salt_buildup,
            "salt_carryover_pressure": salt_carryover_pressure,
            "ec_salt_carryover_pressure": ec_salt_carryover_pressure,
            "high_ec_salt_carryover": int(feats["ec0"] >= 2.0 and positive_pre_anchor_salt_buildup >= 250.0 and feats["gap_hours"] <= 3.0),
            "salt_recency_pressure": float(feats["last_event_salt_conc"] * np.exp(-feats["hrs_since_last_salt_event"] / 6.0)),
            "salt_event_pos": float(np.clip(1.0 - (feats["hrs_since_last_salt_event"] / gap_h_safe), 0.0, 1.0)),
            "ec0_x_p48_salt": float(feats["ec0"] * salt48_pre_t0),
        }
    )
    return feats


def robust_linear_gate(feats, meta):
    gap_hours = feats.get("gap_hours", np.inf)
    min_gap_h = meta.get("ROBUST_LINEAR_GATE_MIN_GAP_H", 0.0)
    min_salt_total = meta.get("ROBUST_LINEAR_GATE_MIN_SALT_TOTAL", 250.0)
    return bool(
        feats.get("fert_salt_total_t0_t1", 0.0) >= min_salt_total
        and feats.get("irr_after_last_salt", 0.0) <= 1.0
        and feats.get("salt_conc_t0_t1", 0.0) >= 3.0
        and feats.get("ec0", np.inf) <= 0.8
        and min_gap_h <= gap_hours <= meta["ROBUST_LINEAR_GATE_MAX_GAP_H"]
    )


FEATURE_LABELS = {
    "ph0": "Current pH",
    "ec0": "Current EC",
    "gap_hours": "Prediction horizon",
    "ET0_per_hour": "ET0 per hour",
    "ET0_sum_t0_t1": "ET0 total",
    "climate_demand_pull": "Climate demand x canopy",
    "climate_demand_soil": "Climate demand x soil temperature",
    "temp_x_canopy": "Soil temperature x canopy",
    "soil_temp_mean": "Mean soil temperature",
    "soil_delta": "Soil temperature change",
    "temp_trend": "Air temperature trend",
    "rad_t1_log": "Radiation at target",
    "rad_morning": "Morning radiation",
    "hist_dark_recent_6h": "Recent dark period",
    "hist_irr_recent": "Recent irrigation",
    "hist_irr_prior": "Prior irrigation",
    "hist48_irr_prevday": "Previous-day irrigation",
    "irr_total_t0_t1": "Irrigation in prediction window",
    "irr_to_et0": "Irrigation to ET0 ratio",
    "irr_after_last_salt": "Irrigation after salt event",
    "fert_salt_total_t0_t1": "Fertilizer salt total",
    "h3po4_total": "Acid total",
    "salt_conc_t0_t1": "Salt concentration",
    "stage_x_salt_conc": "Crop stage x salt concentration",
    "log_ec_drive": "EC drive",
    "hist_salt_buildup": "Recent salt buildup",
    "hist_hrs_since_fert": "Hours since recent fertilizer",
    "hrs_since_fert": "Hours since fertilizer",
    "hrs_since_last_salt_event": "Hours since last salt event",
    "last_event_salt_conc": "Last salt event concentration",
    "salt_recency_pressure": "Salt recency pressure",
    "salt_event_pos": "Salt event timing",
    "pre_salt_irr_ratio_6h": "Pre-anchor salt/irrigation ratio, 6h",
    "pre_salt_irr_ratio_24h": "Pre-anchor salt/irrigation ratio, 24h",
    "pre_anchor_salt_buildup": "Pre-anchor salt buildup",
    "salt_carryover_pressure": "Salt carryover pressure",
    "ec_salt_carryover_pressure": "EC salt carryover pressure",
    "high_ec_salt_carryover": "High EC carryover flag",
    "ec0_x_p48_salt": "Current EC x 48h salt",
    "ec_log_anchor": "Current EC, log scale",
    "t1_early_day": "Target in early day",
    "t1_morning_short": "Short morning horizon",
    "hour_sin_b": "Target hour sine",
    "hour_cos_b": "Target hour cosine",
}


FEATURE_DESCRIPTIONS = {
    "ET0_per_hour": "Atmospheric water demand over the prediction window.",
    "fert_salt_total_t0_t1": "Total salt-bearing fertilizer applied between the anchor and target.",
    "h3po4_total": "Phosphoric acid applied between the anchor and target.",
    "salt_conc_t0_t1": "Fertilizer salt load divided by irrigation volume.",
    "irr_total_t0_t1": "Total irrigation entered for the prediction window.",
    "irr_to_et0": "How irrigation volume compares with evaporative demand.",
    "hist_salt_buildup": "Decayed fertilizer salts remaining from recent history.",
    "pre_anchor_salt_buildup": "Salt carryover entering the prediction window.",
    "salt_recency_pressure": "Recent concentrated salt event pressure.",
    "ec_salt_carryover_pressure": "Interaction between current EC and salt carryover.",
    "ph0": "The measured pH used as the prediction anchor.",
    "ec0": "The measured EC used as the prediction anchor.",
    "gap_hours": "Elapsed time from measurement to target prediction.",
}


FEATURE_CATEGORY_RULES = [
    ("fertilizer", ("fert", "salt", "h3po4", "acid", "kortin", "gypsum")),
    ("irrigation", ("irr",)),
    ("climate", ("ET0", "climate", "temp", "soil", "rad", "dark")),
    ("history", ("hist", "pre_", "carryover", "recency")),
    ("time", ("gap", "hour", "t1_", "morning", "early")),
    ("baseline", ("ph0", "ec0", "ec_log_anchor")),
    ("crop", ("canopy", "stage")),
]


def feature_label(feature: str) -> str:
    if feature in FEATURE_LABELS:
        return FEATURE_LABELS[feature]
    return feature.replace("_", " ").replace(" t0 t1", "").strip().title()


def feature_category(feature: str) -> str:
    for category, tokens in FEATURE_CATEGORY_RULES:
        if any(token in feature for token in tokens):
            return category
    return "model"


def safe_feature_float(value) -> float:
    try:
        number = float(value)
    except Exception:
        return 0.0
    if not np.isfinite(number):
        return 0.0
    return number


def contribution_direction(value: float) -> str:
    if value > 1e-9:
        return "increase"
    if value < -1e-9:
        return "decrease"
    return "neutral"


def prediction_direction(delta: float) -> str:
    if delta > 1e-9:
        return "increase"
    if delta < -1e-9:
        return "decrease"
    return "stable"


def driver_rows(
    feats: dict,
    feature_cols: list[str],
    contributions: np.ndarray,
    *,
    global_importances: np.ndarray | None = None,
    limit: int = 8,
) -> list[dict]:
    contributions = np.asarray(contributions, dtype=float)
    ranked = sorted(range(len(feature_cols)), key=lambda i: abs(contributions[i]), reverse=True)
    rows = []
    for idx in ranked:
        feature = feature_cols[idx]
        contribution = safe_feature_float(contributions[idx])
        if abs(contribution) < 1e-10:
            continue
        importance = None
        if global_importances is not None and idx < len(global_importances):
            importance = safe_feature_float(global_importances[idx])
        rows.append(
            {
                "feature": feature,
                "label": feature_label(feature),
                "category": feature_category(feature),
                "value": safe_feature_float(feats.get(feature, 0.0)),
                "contribution": contribution,
                "abs_contribution": abs(contribution),
                "direction": contribution_direction(contribution),
                "importance": importance,
                "description": FEATURE_DESCRIPTIONS.get(feature, ""),
            }
        )
        if len(rows) >= limit:
            break
    return rows


def group_driver_pressure(rows: list[dict]) -> list[dict]:
    grouped: dict[str, float] = {}
    signed: dict[str, float] = {}
    for row in rows:
        category = row["category"]
        grouped[category] = grouped.get(category, 0.0) + abs(float(row["contribution"]))
        signed[category] = signed.get(category, 0.0) + float(row["contribution"])
    total = sum(grouped.values()) or 1.0
    return [
        {
            "category": category,
            "share": value / total,
            "signed_pressure": signed.get(category, 0.0),
            "direction": contribution_direction(signed.get(category, 0.0)),
        }
        for category, value in sorted(grouped.items(), key=lambda item: item[1], reverse=True)
    ]


def xgb_target_contributions(model: dict, meta: dict, X: pd.DataFrame) -> tuple[list[str], np.ndarray, np.ndarray | None, str]:
    try:
        import xgboost as xgb

        feature_cols = list(meta["feature_cols"])
        booster = model["base"].get_booster()
        raw = booster.predict(xgb.DMatrix(X, feature_names=feature_cols), pred_contribs=True)
        contrib = np.asarray(raw)
        n_features = len(feature_cols)
        if contrib.ndim == 3:
            contrib = contrib[0]
            if contrib.shape[0] != 2 and contrib.shape[1] == 2:
                contrib = contrib.T
        elif contrib.ndim == 2:
            contrib = contrib[0].reshape(1, -1)
        else:
            raise ValueError("Unexpected XGBoost contribution shape")
        contrib = contrib[:, :n_features]
        target_std = np.asarray(model["target_std"], dtype=float)
        contrib = contrib * target_std.reshape(-1, 1)
        global_importances = getattr(model["base"], "feature_importances_", None)
        if global_importances is not None:
            global_importances = np.asarray(global_importances, dtype=float)
        return feature_cols, contrib, global_importances, "xgboost_tree_contributions"
    except Exception:
        feature_cols = list(meta["feature_cols"])
        global_importances = getattr(model["base"], "feature_importances_", None)
        if global_importances is None:
            global_importances = np.ones(len(feature_cols), dtype=float)
        global_importances = np.asarray(global_importances, dtype=float)
        fallback = np.tile(global_importances, (2, 1))
        return feature_cols, fallback, global_importances, "xgboost_global_importance"


def robust_target_contributions(model: dict, meta: dict, feats: dict) -> tuple[list[str], np.ndarray, None, str] | None:
    robust_linear = model.get("robust_linear")
    if robust_linear is None:
        return None
    feature_cols = list(meta.get("robust_feature_cols", meta["feature_cols"]))
    X = pd.DataFrame([feats])[feature_cols].replace([np.inf, -np.inf], np.nan).fillna(0.0)
    try:
        scaler = robust_linear.named_steps["standardscaler"]
        multi = robust_linear.named_steps["multioutputregressor"]
        scaled = np.asarray(scaler.transform(X), dtype=float)[0]
        target_std = np.asarray(model["target_std"], dtype=float)
        rows = []
        for target_idx, estimator in enumerate(multi.estimators_[:2]):
            rows.append(np.asarray(estimator.coef_, dtype=float) * scaled * target_std[target_idx])
        return feature_cols, np.asarray(rows), None, "robust_linear_coefficients"
    except Exception:
        return None


def build_prediction_explanation(
    *,
    model: dict,
    meta: dict,
    feats: dict,
    X: pd.DataFrame,
    model_component: str,
    ph_pred: float,
    ec_pred: float,
    final_raw: np.ndarray,
) -> dict:
    xgb_cols, xgb_contrib, xgb_importance, xgb_method = xgb_target_contributions(model, meta, X)
    selected_cols = xgb_cols
    selected_contrib = xgb_contrib
    selected_importance = xgb_importance
    method = xgb_method

    robust_contrib = robust_target_contributions(model, meta, feats)
    if model_component == "robust_linear" and robust_contrib is not None:
        selected_cols, selected_contrib, selected_importance, method = robust_contrib

    ph_delta = float(ph_pred - feats["ph0"])
    ec_delta = float(ec_pred - feats["ec0"])
    ph_drivers = driver_rows(feats, selected_cols, selected_contrib[0], global_importances=selected_importance)
    ec_drivers = driver_rows(feats, selected_cols, selected_contrib[1], global_importances=selected_importance)

    return {
        "method": method,
        "model_component": model_component,
        "prediction_delta": {
            "ph": ph_delta,
            "ph_direction": prediction_direction(ph_delta),
            "ec_ms": ec_delta,
            "ec_direction": prediction_direction(ec_delta),
            "ec_log_change": safe_feature_float(final_raw[1]),
        },
        "drivers": {
            "ph": ph_drivers,
            "ec": ec_drivers,
        },
        "groups": {
            "ph": group_driver_pressure(ph_drivers),
            "ec": group_driver_pressure(ec_drivers),
        },
    }


def load_rootzone_artifacts(model_dir: str | Path | None = None) -> tuple[dict, dict, Path]:
    joblib = _import_joblib()
    model_dir_path = resolve_path(model_dir, default=PACKAGE_DIR)
    model_path = model_dir_path / ROOTZONE_MODEL_FILE
    meta_path = model_dir_path / ROOTZONE_META_FILE
    if not model_path.exists():
        raise FileNotFoundError(f"Rootzone model not found: {model_path}")
    if not meta_path.exists():
        raise FileNotFoundError(f"Rootzone metadata not found: {meta_path}")

    model = joblib.load(model_path)
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    required_model_keys = ["base", "target_mean", "target_std"]
    missing_model_keys = [k for k in required_model_keys if k not in model]
    if missing_model_keys:
        raise ValueError(f"Rootzone model artifact is missing required fields: {missing_model_keys}")
    if not meta.get("NO_INTERNAL_RH", False):
        raise ValueError("Loaded rootzone metadata is not marked as a no-RH model")
    if "prev_ec_slope" in meta.get("feature_cols", []):
        raise ValueError("Loaded metadata belongs to an older model version with prev_ec_slope")
    return model, meta, model_path


def prepare_rootzone_master(master_df: pd.DataFrame) -> pd.DataFrame:
    if "timestamp" not in master_df.columns:
        raise ValueError("Rootzone master must contain a timestamp column")
    raw = master_df.copy()
    raw["timestamp"] = pd.to_datetime(raw["timestamp"], errors="coerce")
    if raw["timestamp"].isna().any():
        raise ValueError("Rootzone master contains timestamps that could not be parsed")

    missing_columns = [c for c in ROOTZONE_REQUIRED_COLUMNS if c not in raw.columns]
    if missing_columns:
        raise ValueError("Rootzone master is missing columns needed by the trained model: " + ", ".join(missing_columns))

    raw = raw.sort_values("timestamp").drop_duplicates("timestamp", keep="last")
    df = raw.set_index("timestamp")
    for col in df.columns:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


def validate_rootzone_ready(
    df: pd.DataFrame,
    meta: dict,
    *,
    target_time: str | pd.Timestamp | None = None,
    anchor_time: str | pd.Timestamp | None = None,
    required_history_hours: float = 48.0,
    dark_window_hours: float = 6.0,
) -> tuple[pd.Timestamp, pd.Timestamp]:
    if target_time is None:
        target_ts = df.index.max()
    else:
        target_ts = pd.Timestamp(target_time)
        if target_ts not in df.index:
            raise ValueError(f"Target time is not present in the master file: {target_ts}")

    if anchor_time is None:
        labeled_before_target = df.loc[df.index < target_ts]
        labeled_before_target = labeled_before_target[labeled_before_target["ph"].notna() & labeled_before_target["ec_ms"].notna()]
        if labeled_before_target.empty:
            raise ValueError(
                "No pH/EC anchor row found before the target. Fill ph and ec_ms at the latest measured rootzone time before prediction."
            )
        anchor_ts = labeled_before_target.index[-1]
    else:
        anchor_ts = pd.Timestamp(anchor_time)
        if anchor_ts not in df.index:
            raise ValueError(f"Anchor time is not present in the master file: {anchor_ts}")
        if pd.isna(df.loc[anchor_ts, "ph"]) or pd.isna(df.loc[anchor_ts, "ec_ms"]):
            raise ValueError("Anchor row must contain both ph and ec_ms")

    gap_hours = (target_ts - anchor_ts).total_seconds() / 3600.0
    if gap_hours <= 0:
        raise ValueError("Target time must be after the anchor time")

    max_gap_h = float(meta.get("SHARED_SKIP_MAX_GAP_H", 48.0))
    if gap_hours > max_gap_h:
        raise ValueError(
            f"Target is {gap_hours:.1f}h after the anchor, but the model is intended for <= {max_gap_h:.0f}h predictions."
        )

    required_history_start = anchor_ts - pd.Timedelta(hours=required_history_hours)
    if df.index.min() > required_history_start:
        available_history_h = (anchor_ts - df.index.min()).total_seconds() / 3600.0
        raise ValueError(
            f"The model needs {required_history_hours:.0f}h before the anchor. "
            f"This master only has {available_history_h:.1f}h before {anchor_ts:%Y-%m-%d %H:%M}."
        )
    history_window = df.loc[(df.index >= required_history_start) & (df.index < anchor_ts)]
    if history_window.empty:
        raise ValueError("No rows found in the required 48h history window before the anchor")

    model_context = df.loc[(df.index >= required_history_start) & (df.index <= target_ts)]
    must_be_known_cols = [
        "ET0",
        "internal_air_temp_c",
        "internal_radiation",
        "irrigation_ml_current",
        "fertilization_flag",
        "fertilization_type_a_flag",
        "fertilization_type_b_flag",
        "soil_temp_pred",
        "canopy_cover",
        "days_after_planting",
        *ACID_FERTS,
        *SALT_FERTS,
    ]
    missing_context = {}
    for col in must_be_known_cols:
        values = pd.to_numeric(model_context[col], errors="coerce")
        missing_n = int(values.isna().sum())
        if missing_n:
            missing_context[col] = missing_n
    if missing_context:
        details = ", ".join(f"{col}: {count}" for col, count in missing_context.items())
        raise ValueError(
            "The rootzone model context has missing values in required climate/crop/event columns. "
            "Use 0 for confirmed no irrigation/fertilization event; leave only ph/ec_ms blank except for measured anchor rows. "
            f"Missing counts: {details}"
        )

    dark_start = target_ts - pd.Timedelta(hours=dark_window_hours)
    dark_window = df.loc[(df.index >= dark_start) & (df.index < target_ts)]
    if dark_window.empty:
        raise ValueError(f"No rows found in the {dark_window_hours:.0f}h radiation window before the target")
    dark_radiation = pd.to_numeric(dark_window["internal_radiation"], errors="coerce")
    if dark_radiation.notna().sum() == 0:
        raise ValueError(f"internal_radiation has no valid values in the {dark_window_hours:.0f}h window before target")
    if dark_radiation.isna().any():
        raise ValueError(
            f"internal_radiation has {int(dark_radiation.isna().sum())} missing values in the {dark_window_hours:.0f}h window before target"
        )
    return anchor_ts, target_ts


def predict_rootzone_from_master(
    master_df: pd.DataFrame,
    *,
    model_dir: str | Path | None = None,
    target_time: str | pd.Timestamp | None = None,
    anchor_time: str | pd.Timestamp | None = None,
    required_history_hours: float = 48.0,
    dark_window_hours: float = 6.0,
) -> dict:
    model, meta, model_path = load_rootzone_artifacts(model_dir)
    df = prepare_rootzone_master(master_df)
    anchor_ts, target_ts = validate_rootzone_ready(
        df,
        meta,
        target_time=target_time,
        anchor_time=anchor_time,
        required_history_hours=required_history_hours,
        dark_window_hours=dark_window_hours,
    )

    feats = get_features_shared(df, anchor_ts, target_ts)
    feature_cols = list(meta["feature_cols"])
    robust_feature_cols = list(meta.get("robust_feature_cols", feature_cols))
    required_features = list(dict.fromkeys(feature_cols + robust_feature_cols))
    missing_features = [f for f in required_features if f not in feats]
    if missing_features:
        raise ValueError(f"Missing model features: {missing_features}")

    X = pd.DataFrame([feats])[feature_cols].replace([np.inf, -np.inf], np.nan).fillna(0.0)
    base_raw = np.asarray(model["base"].predict(X))[0]
    base_raw = base_raw * model["target_std"] + model["target_mean"]

    final_raw = base_raw
    model_component = "xgboost"
    robust_linear = model.get("robust_linear")
    if robust_linear is not None and robust_linear_gate(feats, meta):
        X_robust = pd.DataFrame([feats])[robust_feature_cols].replace([np.inf, -np.inf], np.nan).fillna(0.0)
        robust_raw = np.asarray(robust_linear.predict(X_robust))[0]
        robust_raw = robust_raw * model["target_std"] + model["target_mean"]
        blend = np.array([meta["ROBUST_LINEAR_BLEND_PH"], meta["ROBUST_LINEAR_BLEND_EC"]], dtype=float)
        final_raw = (1.0 - blend) * base_raw + blend * robust_raw
        model_component = "robust_linear"

    ph_pred = feats["ph0"] + final_raw[0]
    ec_pred = max(0.0, (feats["ec0"] + meta["EC_TARGET_SHIFT"]) * np.exp(final_raw[1]) - meta["EC_TARGET_SHIFT"])
    xai = build_prediction_explanation(
        model=model,
        meta=meta,
        feats=feats,
        X=X,
        model_component=model_component,
        ph_pred=ph_pred,
        ec_pred=ec_pred,
        final_raw=final_raw,
    )

    return {
        "anchor_time": anchor_ts,
        "target_time": target_ts,
        "gap_hours": float(feats["gap_hours"]),
        "anchor_ph": float(feats["ph0"]),
        "anchor_ec_ms": float(feats["ec0"]),
        "predicted_ph": float(ph_pred),
        "predicted_ec_ms": float(ec_pred),
        "model_component": model_component,
        "model_file": str(model_path),
        "xai": xai,
    }


def run_pipeline(
    *,
    weather_file: str | Path,
    radiation_file: str | Path,
    micro_model_file: str | Path | None = None,
    manual_master_file: str | Path | None = None,
    events_file: str | Path | None = None,
    anchors_file: str | Path | None = None,
    crop_file: str | Path | None = None,
    output_master_file: str | Path = PACKAGE_DIR / "etl_master_template.csv",
    output_events_template_file: str | Path | None = PACKAGE_DIR / "etl_events_template.csv",
    output_anchors_template_file: str | Path | None = PACKAGE_DIR / "etl_anchors_template.csv",
    output_crop_template_file: str | Path | None = PACKAGE_DIR / "etl_crop_template.csv",
    output_forecast_file: str | Path | None = PACKAGE_DIR / "etl_micro_climate_predictions.csv",
    output_prediction_file: str | Path | None = PACKAGE_DIR / "etl_rootzone_prediction.csv",
    start_time: str | pd.Timestamp | None = None,
    end_time: str | pd.Timestamp | None = None,
    planting_date: str | pd.Timestamp | None = None,
    canopy_cover_default: float = 0.0,
    run_rootzone: bool = True,
    target_time: str | pd.Timestamp | None = None,
    anchor_time: str | pd.Timestamp | None = None,
    required_history_hours: float = 48.0,
    dark_window_hours: float = 6.0,
    max_external_gap_hours: float = 3.0,
) -> dict:
    weather_path = resolve_path(weather_file)
    radiation_path = resolve_path(radiation_file)
    if not weather_path.exists():
        raise FileNotFoundError(f"Weather file not found: {weather_path}")
    if not radiation_path.exists():
        raise FileNotFoundError(f"Radiation file not found: {radiation_path}")

    weather = read_table(weather_path, label="Weather file")
    radiation = read_table(radiation_path, label="Radiation file")
    model_frame = engineer_micro_climate_features(
        weather,
        radiation,
        start_time=start_time,
        end_time=end_time,
        max_external_gap_hours=max_external_gap_hours,
    )
    micro_bundle = load_micro_climate_bundle(micro_model_file)
    climate_predictions = forecast_micro_climate(model_frame, micro_bundle)

    master = create_master_template(
        climate_predictions,
        manual_master_file=manual_master_file,
        events_file=events_file,
        anchors_file=anchors_file,
        crop_file=crop_file,
        planting_date=planting_date,
        canopy_cover_default=canopy_cover_default,
    )

    output_master_path = resolve_output_path(output_master_file)
    output_master_path.parent.mkdir(parents=True, exist_ok=True)
    master.to_csv(output_master_path, index=False)

    forecast_path = None
    if output_forecast_file is not None and str(output_forecast_file).strip():
        forecast_path = resolve_output_path(output_forecast_file)
        forecast_path.parent.mkdir(parents=True, exist_ok=True)
        climate_predictions.to_csv(forecast_path, index=False)

    manual_template_paths = write_manual_input_templates(
        master,
        output_events_template_file=output_events_template_file,
        output_anchors_template_file=output_anchors_template_file,
        output_crop_template_file=output_crop_template_file,
        target_time=target_time,
        anchor_time=anchor_time,
        required_history_hours=required_history_hours,
    )

    input_notes = []
    if not _has_path(manual_master_file) and not _has_path(events_file):
        input_notes.append("No events file/manual master was provided; irrigation and fertilizer inputs are assumed 0.")
    if not _has_path(manual_master_file) and not _has_path(anchors_file):
        input_notes.append("No anchors file/manual master was provided; rootzone prediction needs a measured ph/ec_ms anchor.")

    result = {
        "weather_file": str(weather_path),
        "radiation_file": str(radiation_path),
        "forecast_rows": len(climate_predictions),
        "master_file": str(output_master_path),
        "manual_input_templates": manual_template_paths,
        "input_notes": input_notes,
        "forecast_file": str(forecast_path) if forecast_path else None,
        "rootzone_prediction": None,
        "prediction_file": None,
    }

    if run_rootzone:
        prediction = predict_rootzone_from_master(
            master,
            target_time=target_time,
            anchor_time=anchor_time,
            required_history_hours=required_history_hours,
            dark_window_hours=dark_window_hours,
        )
        result["rootzone_prediction"] = prediction
        if output_prediction_file is not None and str(output_prediction_file).strip():
            prediction_path = resolve_output_path(output_prediction_file)
            prediction_path.parent.mkdir(parents=True, exist_ok=True)
            pd.DataFrame([prediction]).to_csv(prediction_path, index=False)
            result["prediction_file"] = str(prediction_path)
    return result


def print_pipeline_result(result: dict) -> None:
    print("ETL finished")
    print(f"Forecast rows : {result['forecast_rows']:,}")
    print(f"Master CSV    : {result['master_file']}")
    if result.get("forecast_file"):
        print(f"Forecast CSV  : {result['forecast_file']}")
    templates = result.get("manual_input_templates") or {}
    for label in ("events", "anchors", "crop"):
        if templates.get(label):
            print(f"{label.title()} input : {templates[label]}")
    for note in result.get("input_notes") or []:
        print(f"Note         : {note}")
    prediction = result.get("rootzone_prediction")
    if prediction is None:
        print("Rootzone prediction was not run. Fill the anchors/events input files, then rerun with rootzone enabled.")
        return

    print(f"Prediction CSV: {result.get('prediction_file')}")
    print()
    print("ROOTZONE PREDICTION")
    print(f"Anchor time : {prediction['anchor_time']:%Y-%m-%d %H:%M}")
    print(f"Anchor pH   : {prediction['anchor_ph']:.3f}")
    print(f"Anchor EC   : {prediction['anchor_ec_ms']:.4f} mS/cm")
    print(f"Target time : {prediction['target_time']:%Y-%m-%d %H:%M}")
    print(f"Gap         : {prediction['gap_hours']:.1f} hours")
    print(f"Component   : {prediction['model_component']}")
    print(f"Predicted pH: {prediction['predicted_ph']:.3f}")
    print(f"Predicted EC: {prediction['predicted_ec_ms']:.4f} mS/cm")


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build master-format rootzone inputs from weather/radiation files and run the no-RH rootzone model.")
    parser.add_argument("--weather-file", required=True)
    parser.add_argument("--radiation-file", required=True)
    parser.add_argument("--micro-model-file", default=None)
    parser.add_argument("--manual-master-file", default=None)
    parser.add_argument("--events-file", default=None, help="Optional small CSV with timestamp plus irrigation/fertilizer event columns.")
    parser.add_argument("--anchors-file", default=None, help="Optional small CSV with timestamp, ph, and ec_ms anchor measurements.")
    parser.add_argument("--crop-file", default=None, help="Optional small CSV with timestamp plus canopy_cover and/or days_after_planting.")
    parser.add_argument("--output-master-file", default=str(PACKAGE_DIR / "etl_master_template.csv"))
    parser.add_argument("--output-events-template-file", default=str(PACKAGE_DIR / "etl_events_template.csv"))
    parser.add_argument("--output-anchors-template-file", default=str(PACKAGE_DIR / "etl_anchors_template.csv"))
    parser.add_argument("--output-crop-template-file", default=str(PACKAGE_DIR / "etl_crop_template.csv"))
    parser.add_argument("--output-forecast-file", default=str(PACKAGE_DIR / "etl_micro_climate_predictions.csv"))
    parser.add_argument("--output-prediction-file", default=str(PACKAGE_DIR / "etl_rootzone_prediction.csv"))
    parser.add_argument("--start-time", default=None)
    parser.add_argument("--end-time", default=None)
    parser.add_argument("--planting-date", default=None)
    parser.add_argument("--canopy-cover-default", type=float, default=0.0)
    parser.add_argument("--target-time", default=None)
    parser.add_argument("--anchor-time", default=None)
    parser.add_argument("--required-history-hours", type=float, default=48.0)
    parser.add_argument("--dark-window-hours", type=float, default=6.0)
    parser.add_argument("--max-external-gap-hours", type=float, default=3.0)
    parser.add_argument("--no-rootzone", action="store_true", help="Only create the editable master CSV; do not run rootzone prediction.")
    return parser


def main(argv: list[str] | None = None) -> dict:
    args = build_arg_parser().parse_args(argv)
    result = run_pipeline(
        weather_file=args.weather_file,
        radiation_file=args.radiation_file,
        micro_model_file=args.micro_model_file,
        manual_master_file=args.manual_master_file,
        events_file=args.events_file,
        anchors_file=args.anchors_file,
        crop_file=args.crop_file,
        output_master_file=args.output_master_file,
        output_events_template_file=args.output_events_template_file,
        output_anchors_template_file=args.output_anchors_template_file,
        output_crop_template_file=args.output_crop_template_file,
        output_forecast_file=args.output_forecast_file,
        output_prediction_file=args.output_prediction_file,
        start_time=args.start_time,
        end_time=args.end_time,
        planting_date=args.planting_date,
        canopy_cover_default=args.canopy_cover_default,
        run_rootzone=not args.no_rootzone,
        target_time=args.target_time,
        anchor_time=args.anchor_time,
        required_history_hours=args.required_history_hours,
        dark_window_hours=args.dark_window_hours,
        max_external_gap_hours=args.max_external_gap_hours,
    )
    print_pipeline_result(result)
    return result


if __name__ == "__main__":
    main()
