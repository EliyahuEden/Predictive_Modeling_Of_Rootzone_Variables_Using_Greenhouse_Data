import contextlib
import json
import os
import warnings

import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.linear_model import HuberRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.multioutput import MultiOutputRegressor
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler


SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(SCRIPT_DIR)


def load_notebook_context():
    with open("Continuous_Rootzone_V8_MultiOutput_Shared.ipynb", "r", encoding="utf-8") as f:
        nb = json.load(f)
    ctx = globals()
    for cell_idx in [1, 2, 3, 4]:
        src = "".join(nb["cells"][cell_idx]["source"])
        with contextlib.redirect_stdout(open(os.devnull, "w", encoding="utf-8")):
            exec(compile(src, f"notebook_cell_{cell_idx}", "exec"), ctx)


load_notebook_context()

sensor_idx = list(master_df.index[master_df["ph"].notna() & master_df["ec_ms"].notna()])
EC_TARGET_SHIFT = 0.05
SHARED_SKIP_MAX_GAP_H = 26.0
SHARED_SPECIALIST_MIN_ROWS = 8


def unique(seq):
    out = []
    for item in seq:
        if item not in out:
            out.append(item)
    return out


FEATURE_SETS = {
    "current_union": unique(feature_cols_ph + feature_cols_ec),
    "dynamic_core": unique([
        "ph0", "ec0", "gap_hours",
        "ET0_per_hour", "ET0_sum_t0_t1", "transpiration_pull",
        "soil_temp_mean", "soil_delta", "temp_trend", "rad_t1_log",
        "irr_total_t0_t1", "irr_to_et0", "hrs_since_irr", "irr_after_last_salt",
        "h3po4_total", "acid_conc_t0_t1", "weighted_fert_acid",
        "fert_salt_total_t0_t1", "salt_conc_t0_t1",
        "last_event_salt_conc", "recent_salt_conc_2h",
        "hist_acid_decay", "hist_salt_buildup", "hist_hrs_since_fert", "hist_hrs_since_irr",
        "hist48_acid_prevday", "hist48_irr_prevday",
        "hour_sin_b", "hour_cos_b", "t0_morning", "t1_morning",
        "timing_balance", "ec0_x_p48_salt",
    ]),
}


XGB_PARAM_SETS = {
    "current": {
        "n_estimators": 500,
        "learning_rate": 0.03,
        "max_depth": 3,
        "min_child_weight": 3,
        "subsample": 0.72,
        "colsample_bytree": 0.68,
        "reg_alpha": 2.0,
        "reg_lambda": 3.0,
        "random_state": 42,
        "n_jobs": -1,
        "tree_method": "hist",
        "objective": "reg:squarederror",
    },
    "smaller": {
        "n_estimators": 350,
        "learning_rate": 0.04,
        "max_depth": 2,
        "min_child_weight": 3,
        "subsample": 0.78,
        "colsample_bytree": 0.75,
        "reg_alpha": 2.0,
        "reg_lambda": 4.0,
        "random_state": 42,
        "n_jobs": -1,
        "tree_method": "hist",
        "objective": "reg:squarederror",
    },
}


HUBER_PARAMS = {
    "alpha": 0.001,
    "epsilon": 1.35,
    "max_iter": 10000,
    "tol": 1e-5,
}


def selected_shared_skip_pairs(k, max_rows):
    selected = []
    for back in range(2, k + 1):
        j = k - back
        gap_h = (pd.Timestamp(sensor_idx[k]) - pd.Timestamp(sensor_idx[j])).total_seconds() / 3600.0
        if gap_h > SHARED_SKIP_MAX_GAP_H:
            break
        if (j, k) in HOLDOUT_SKIP_PAIRS:
            continue
        selected.append((j, k, back, gap_h))
        if max_rows is not None and len(selected) >= max_rows:
            break
    return selected


def make_shared_row(j, k, timestamp=None):
    t1 = sensor_idx[k]
    row = get_features_v6(master_df, sensor_idx[j], t1)
    row["ph_true"] = float(master_df.loc[t1, "ph"])
    row["ec_true"] = float(master_df.loc[t1, "ec_ms"])
    row["timestamp"] = t1 if timestamp is None else timestamp
    return row


def build_shared_rows(up_to_pos, max_rows):
    rows = []
    for k in range(1, up_to_pos + 1):
        rows.append(make_shared_row(k - 1, k))
        for j, _, back, _ in selected_shared_skip_pairs(k, max_rows):
            rows.append(make_shared_row(j, k, sensor_idx[k] + pd.Timedelta(microseconds=back)))
    return rows


def targets(train_df):
    ph_delta = (train_df["ph_true"] - train_df["ph0"]).to_numpy()
    ec_log_delta = np.log(
        (train_df["ec_true"].to_numpy() + EC_TARGET_SHIFT) /
        (train_df["ec0"].to_numpy() + EC_TARGET_SHIFT)
    )
    return np.column_stack([ph_delta, ec_log_delta])


def event_masks(df):
    acid_event = (df["h3po4_total"] > 0.0) | (df["hist_acid_decay"] > 0.002)
    salt_event = (df["fert_salt_total_t0_t1"] >= 250.0) & (df["irr_after_last_salt"] <= 1.0)
    salt_conc_event = (
        (df["fert_salt_total_t0_t1"] >= 250.0) &
        (df["irr_after_last_salt"] <= 1.0) &
        (df["salt_conc_t0_t1"] >= 2.5)
    )
    shock_event = salt_conc_event & (df["ec0"] <= 0.8)
    salt_shock_strict = shock_event & (df["gap_hours"] <= 10.0)
    salt_shock_no_ec = salt_conc_event & (df["gap_hours"] <= 10.0)
    any_dose_event = (df["fert_salt_total_t0_t1"] > 0.0) | (df["h3po4_total"] > 0.0)
    return {
        "chem_event": salt_event | acid_event,
        "dose_event": any_dose_event | acid_event,
        "concentrated_chem": salt_conc_event | acid_event,
        "shock_or_acid": shock_event | acid_event,
        "salt_shock_strict": salt_shock_strict,
        "salt_shock_no_ec": salt_shock_no_ec,
    }


def mask_for_df(df, mode):
    return event_masks(df)[mode].to_numpy()


def mask_for_feats(feats, mode):
    row = pd.DataFrame([feats])
    return bool(mask_for_df(row, mode)[0])


def shock_mask(df):
    return event_masks(df)["shock_or_acid"].to_numpy() & (
        (df["fert_salt_total_t0_t1"] >= 250.0) &
        (df["irr_after_last_salt"] <= 1.0) &
        (df["salt_conc_t0_t1"] >= 2.5) &
        (df["ec0"] <= 0.8)
    ).to_numpy()


def fit_shared_model(train_df, feature_cols, train_mode, xgb_params, shock_weight):
    X = train_df[feature_cols].replace([np.inf, -np.inf], np.nan).fillna(0.0)
    Y = targets(train_df)

    base = xgb.XGBRegressor(**xgb_params)
    base.fit(X, Y, verbose=False)

    specialist_mask = mask_for_df(train_df, train_mode)
    specialist = None
    if int(specialist_mask.sum()) >= SHARED_SPECIALIST_MIN_ROWS:
        weights = np.ones(int(specialist_mask.sum()))
        if shock_weight > 0:
            weights += shock_weight * shock_mask(train_df)[specialist_mask].astype(float)
        specialist = make_pipeline(
            StandardScaler(),
            MultiOutputRegressor(HuberRegressor(**HUBER_PARAMS)),
        )
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            specialist.fit(
                X.iloc[specialist_mask],
                Y[specialist_mask],
                multioutputregressor__sample_weight=weights,
            )

    return {
        "base": base,
        "specialist": specialist,
        "n_train": len(train_df),
        "n_specialist": int(specialist_mask.sum()),
        "n_shock": int(shock_mask(train_df).sum()),
    }


def predict_raw_and_type(model, feats, feature_cols, pred_mode, blend):
    X = pd.DataFrame([feats])[feature_cols].replace([np.inf, -np.inf], np.nan).fillna(0.0)
    base_raw = np.asarray(model["base"].predict(X))[0]
    specialist = model.get("specialist")
    if specialist is not None and blend > 0 and mask_for_feats(feats, pred_mode):
        spec_raw = np.asarray(specialist.predict(X))[0]
        return (1.0 - blend) * base_raw + blend * spec_raw, "huber"
    return base_raw, "base"


def run_walkforward(config):
    warmup = config["warmup"]
    max_rows = config["max_rows"]
    feature_cols = FEATURE_SETS[config["feature_set"]]
    xgb_params = XGB_PARAM_SETS[config["xgb_set"]]

    train_df = pd.DataFrame(build_shared_rows(warmup, max_rows)).set_index("timestamp").sort_index()
    model = fit_shared_model(train_df, feature_cols, config["train_mode"], xgb_params, config["shock_weight"])

    rows = []
    anchor = sensor_idx[warmup]
    for k in range(warmup, len(sensor_idx)):
        cur = sensor_idx[k]
        feats = get_features_v6(master_df, anchor, cur)
        if feats["gap_hours"] <= 0:
            raw, specialist_type = np.array([0.0, 0.0]), "base"
        else:
            raw, specialist_type = predict_raw_and_type(
                model, feats, feature_cols, config["pred_mode"], config["blend"]
            )

        ph_pred = feats["ph0"] + raw[0]
        ec_pred = max(0.0, (feats["ec0"] + EC_TARGET_SHIFT) * np.exp(raw[1]) - EC_TARGET_SHIFT)
        rows.append({
            "timestamp": cur,
            "gap_hours": feats["gap_hours"],
            "ph_true": float(master_df.loc[cur, "ph"]),
            "ph_pred": ph_pred,
            "ph_naive": feats["ph0"],
            "ec_true": float(master_df.loc[cur, "ec_ms"]),
            "ec_pred": ec_pred,
            "ec_naive": feats["ec0"],
            "specialist_type": specialist_type,
        })

        if k > warmup:
            new_rows = [make_shared_row(k - 1, k)]
            for j, _, back, _ in selected_shared_skip_pairs(k, max_rows):
                new_rows.append(make_shared_row(j, k, sensor_idx[k] + pd.Timedelta(microseconds=back)))
            train_df = pd.concat([train_df, pd.DataFrame(new_rows).set_index("timestamp")]).sort_index()
            model = fit_shared_model(train_df, feature_cols, config["train_mode"], xgb_params, config["shock_weight"])

        anchor = cur

    ev = pd.DataFrame(rows).set_index("timestamp")
    return model, ev


def score_ev(ev, model, config):
    ph_mae = float(mean_absolute_error(ev["ph_true"], ev["ph_pred"]))
    ec_mae = float(mean_absolute_error(ev["ec_true"], ev["ec_pred"]))
    ph_r2 = float(r2_score(ev["ph_true"], ev["ph_pred"]))
    ec_r2 = float(r2_score(ev["ec_true"], ev["ec_pred"]))
    ph_naive = float(mean_absolute_error(ev["ph_true"], ev["ph_naive"]))
    ec_naive = float(mean_absolute_error(ev["ec_true"], ev["ec_naive"]))
    return {
        **config,
        "feature_count": len(FEATURE_SETS[config["feature_set"]]),
        "wf_active": int((ev["specialist_type"] == "huber").sum()),
        "n_spec_final": model["n_specialist"],
        "n_shock_final": model["n_shock"],
        "wf_ph_r2": ph_r2,
        "wf_ec_r2": ec_r2,
        "wf_min_r2": min(ph_r2, ec_r2),
        "wf_ph_mae": ph_mae,
        "wf_ec_mae": ec_mae,
        "wf_ph_gain": ph_naive - ph_mae,
        "wf_ec_gain": ec_naive - ec_mae,
    }


def run_holdout(model, config):
    feature_cols = FEATURE_SETS[config["feature_set"]]
    rows = []
    for j, k, gap_h in HOLDOUT_SKIP_PAIRS_WITH_GAP:
        t0, t1 = sensor_idx[j], sensor_idx[k]
        feats = get_features_v6(master_df, t0, t1)
        raw, specialist_type = predict_raw_and_type(
            model, feats, feature_cols, config["pred_mode"], config["blend"]
        )
        rows.append({
            "t0": t0,
            "t1": t1,
            "gap_h": gap_h,
            "ph_true": float(master_df.loc[t1, "ph"]),
            "ph_pred": feats["ph0"] + raw[0],
            "ph_naive": feats["ph0"],
            "ec_true": float(master_df.loc[t1, "ec_ms"]),
            "ec_pred": max(0.0, (feats["ec0"] + EC_TARGET_SHIFT) * np.exp(raw[1]) - EC_TARGET_SHIFT),
            "ec_naive": feats["ec0"],
            "specialist_type": specialist_type,
        })
    hdf = pd.DataFrame(rows)
    return {
        "ho_active": int((hdf["specialist_type"] == "huber").sum()),
        "ho_ph_r2": float(r2_score(hdf["ph_true"], hdf["ph_pred"])),
        "ho_ec_r2": float(r2_score(hdf["ec_true"], hdf["ec_pred"])),
        "ho_min_r2": float(min(r2_score(hdf["ph_true"], hdf["ph_pred"]), r2_score(hdf["ec_true"], hdf["ec_pred"]))),
        "ho_ph_mae": float(mean_absolute_error(hdf["ph_true"], hdf["ph_pred"])),
        "ho_ec_mae": float(mean_absolute_error(hdf["ec_true"], hdf["ec_pred"])),
    }


def main():
    rows = []
    experiment_blocks = [
        {
            "feature_sets": ["current_union"],
            "xgb_sets": ["current"],
            "warmups": [25, 30, 35, 40, 45, 50, 55],
            "max_rows": [4],
            "modes": ["chem_event", "concentrated_chem", "shock_or_acid", "dose_event"],
            "shock_weights": [0.0, 3.0],
            "blends": [0.0, 0.25, 0.5, 0.75, 1.0, 1.25],
        },
        {
            "feature_sets": ["dynamic_core"],
            "xgb_sets": ["current"],
            "warmups": [30, 35, 40, 45],
            "max_rows": [4],
            "modes": ["chem_event", "concentrated_chem", "shock_or_acid"],
            "shock_weights": [0.0, 3.0],
            "blends": [0.0, 0.5, 1.0],
        },
        {
            "feature_sets": ["current_union"],
            "xgb_sets": ["smaller"],
            "warmups": [30, 35, 40, 45],
            "max_rows": [4],
            "modes": ["chem_event", "concentrated_chem", "shock_or_acid"],
            "shock_weights": [0.0],
            "blends": [0.0, 0.5, 1.0],
        },
        {
            "feature_sets": ["current_union"],
            "xgb_sets": ["current"],
            "warmups": [30, 35, 40],
            "max_rows": [2],
            "modes": ["chem_event", "concentrated_chem", "shock_or_acid"],
            "shock_weights": [0.0, 3.0],
            "blends": [0.0, 0.5, 1.0],
        },
    ]

    for block in experiment_blocks:
        for feature_set in block["feature_sets"]:
            for xgb_set in block["xgb_sets"]:
                for warmup in block["warmups"]:
                    for max_rows in block["max_rows"]:
                        for mode in block["modes"]:
                            train_mode, pred_mode = mode, mode
                            for shock_weight in block["shock_weights"]:
                                for blend in block["blends"]:
                                    config = {
                                        "feature_set": feature_set,
                                        "xgb_set": xgb_set,
                                        "warmup": warmup,
                                        "max_rows": max_rows,
                                        "train_mode": train_mode,
                                        "pred_mode": pred_mode,
                                        "shock_weight": shock_weight,
                                        "blend": blend,
                                    }
                                    model, ev = run_walkforward(config)
                                    result = score_ev(ev, model, config)
                                    result.update(run_holdout(model, config))
                                    rows.append(result)
                                    print(
                                        f"{len(rows):04d} {feature_set} {xgb_set} warmup={warmup} rows={max_rows} "
                                        f"{train_mode} sw={shock_weight} blend={blend} "
                                        f"WF pH={result['wf_ph_r2']:.3f} EC={result['wf_ec_r2']:.3f} "
                                        f"HO pH={result['ho_ph_r2']:.3f} EC={result['ho_ec_r2']:.3f}",
                                        flush=True,
                                    )

    out = pd.DataFrame(rows).sort_values(
        ["wf_min_r2", "wf_ec_r2", "wf_ph_r2", "ho_min_r2"],
        ascending=[False, False, False, False],
    )
    os.makedirs("exports", exist_ok=True)
    out.to_csv("exports/shared_simple_huber_warmup_grid11.csv", index=False)
    print("\nTop 20 by walk-forward min R2:")
    print(out.head(20).to_string(index=False))


if __name__ == "__main__":
    main()
