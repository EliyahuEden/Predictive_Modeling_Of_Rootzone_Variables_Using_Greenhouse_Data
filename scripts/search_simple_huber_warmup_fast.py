import os

import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, r2_score

import search_simple_huber_warmup as s


def raw_parts(model, feats, feature_cols, pred_mode):
    x = pd.DataFrame([feats])[feature_cols].replace([np.inf, -np.inf], np.nan).fillna(0.0)
    base_raw = np.asarray(model["base"].predict(x))[0]
    specialist = model.get("specialist")
    gate = specialist is not None and s.mask_for_feats(feats, pred_mode)
    if gate:
        spec_raw = np.asarray(specialist.predict(x))[0]
    else:
        spec_raw = base_raw.copy()
    return base_raw, spec_raw, gate


def run_structural(config):
    warmup = config["warmup"]
    max_rows = config["max_rows"]
    feature_cols = s.FEATURE_SETS[config["feature_set"]]
    xgb_params = s.XGB_PARAM_SETS[config["xgb_set"]]

    train_df = pd.DataFrame(s.build_shared_rows(warmup, max_rows)).set_index("timestamp").sort_index()
    model = s.fit_shared_model(
        train_df,
        feature_cols,
        config["train_mode"],
        xgb_params,
        config["shock_weight"],
    )

    rows = []
    anchor = s.sensor_idx[warmup]
    for k in range(warmup, len(s.sensor_idx)):
        cur = s.sensor_idx[k]
        feats = s.get_features_v6(s.master_df, anchor, cur)
        if feats["gap_hours"] <= 0:
            base_raw, spec_raw, gate = np.array([0.0, 0.0]), np.array([0.0, 0.0]), False
        else:
            base_raw, spec_raw, gate = raw_parts(model, feats, feature_cols, config["pred_mode"])

        rows.append({
            "timestamp": cur,
            "gap_hours": feats["gap_hours"],
            "ph0": feats["ph0"],
            "ec0": feats["ec0"],
            "ph_true": float(s.master_df.loc[cur, "ph"]),
            "ec_true": float(s.master_df.loc[cur, "ec_ms"]),
            "base_ph_raw": base_raw[0],
            "base_ec_raw": base_raw[1],
            "spec_ph_raw": spec_raw[0],
            "spec_ec_raw": spec_raw[1],
            "huber_gate": gate,
        })

        if k > warmup:
            new_rows = [s.make_shared_row(k - 1, k)]
            for j, _, back, _ in s.selected_shared_skip_pairs(k, max_rows):
                new_rows.append(s.make_shared_row(j, k, s.sensor_idx[k] + pd.Timedelta(microseconds=back)))
            train_df = pd.concat([train_df, pd.DataFrame(new_rows).set_index("timestamp")]).sort_index()
            model = s.fit_shared_model(
                train_df,
                feature_cols,
                config["train_mode"],
                xgb_params,
                config["shock_weight"],
            )

        anchor = cur

    return model, pd.DataFrame(rows).set_index("timestamp")


def score_blend(raw_df, blend):
    ph_raw = np.where(
        raw_df["huber_gate"],
        (1.0 - blend) * raw_df["base_ph_raw"] + blend * raw_df["spec_ph_raw"],
        raw_df["base_ph_raw"],
    )
    ec_raw = np.where(
        raw_df["huber_gate"],
        (1.0 - blend) * raw_df["base_ec_raw"] + blend * raw_df["spec_ec_raw"],
        raw_df["base_ec_raw"],
    )
    ph_pred = raw_df["ph0"].to_numpy() + ph_raw
    ec_pred = np.maximum(0.0, (raw_df["ec0"].to_numpy() + s.EC_TARGET_SHIFT) * np.exp(ec_raw) - s.EC_TARGET_SHIFT)
    return {
        "wf_active": int(raw_df["huber_gate"].sum()),
        "wf_ph_r2": float(r2_score(raw_df["ph_true"], ph_pred)),
        "wf_ec_r2": float(r2_score(raw_df["ec_true"], ec_pred)),
        "wf_min_r2": float(min(r2_score(raw_df["ph_true"], ph_pred), r2_score(raw_df["ec_true"], ec_pred))),
        "wf_ph_mae": float(mean_absolute_error(raw_df["ph_true"], ph_pred)),
        "wf_ec_mae": float(mean_absolute_error(raw_df["ec_true"], ec_pred)),
    }


def score_holdout(model, config, blend):
    feature_cols = s.FEATURE_SETS[config["feature_set"]]
    rows = []
    for j, k, gap_h in s.HOLDOUT_SKIP_PAIRS_WITH_GAP:
        t0, t1 = s.sensor_idx[j], s.sensor_idx[k]
        feats = s.get_features_v6(s.master_df, t0, t1)
        base_raw, spec_raw, gate = raw_parts(model, feats, feature_cols, config["pred_mode"])
        raw = (1.0 - blend) * base_raw + blend * spec_raw if gate else base_raw
        rows.append({
            "ph_true": float(s.master_df.loc[t1, "ph"]),
            "ec_true": float(s.master_df.loc[t1, "ec_ms"]),
            "ph_pred": feats["ph0"] + raw[0],
            "ec_pred": max(0.0, (feats["ec0"] + s.EC_TARGET_SHIFT) * np.exp(raw[1]) - s.EC_TARGET_SHIFT),
            "huber_gate": gate,
        })
    df = pd.DataFrame(rows)
    return {
        "ho_active": int(df["huber_gate"].sum()),
        "ho_ph_r2": float(r2_score(df["ph_true"], df["ph_pred"])),
        "ho_ec_r2": float(r2_score(df["ec_true"], df["ec_pred"])),
        "ho_ph_mae": float(mean_absolute_error(df["ph_true"], df["ph_pred"])),
        "ho_ec_mae": float(mean_absolute_error(df["ec_true"], df["ec_pred"])),
    }


def main():
    structural_configs = []
    for warmup in [25, 30, 35, 40, 45, 50, 55]:
        for mode in ["chem_event", "concentrated_chem", "shock_or_acid", "dose_event"]:
            for shock_weight in [0.0, 3.0]:
                structural_configs.append({
                    "feature_set": "current_union",
                    "xgb_set": "current",
                    "warmup": warmup,
                    "max_rows": 4,
                    "train_mode": mode,
                    "pred_mode": mode,
                    "shock_weight": shock_weight,
                })

    for warmup in [30, 35, 40, 45]:
        for mode in ["chem_event", "concentrated_chem", "shock_or_acid"]:
            structural_configs.append({
                "feature_set": "dynamic_core",
                "xgb_set": "current",
                "warmup": warmup,
                "max_rows": 4,
                "train_mode": mode,
                "pred_mode": mode,
                "shock_weight": 0.0,
            })

    rows = []
    blends = [0.0, 0.25, 0.5, 0.75, 1.0, 1.25]
    for idx, config in enumerate(structural_configs, start=1):
        model, raw_df = run_structural(config)
        for blend in blends:
            result = dict(config)
            result["blend"] = blend
            result["feature_count"] = len(s.FEATURE_SETS[config["feature_set"]])
            result["n_spec_final"] = model["n_specialist"]
            result["n_shock_final"] = model["n_shock"]
            result.update(score_blend(raw_df, blend))
            result.update(score_holdout(model, config, blend))
            rows.append(result)
        best_now = max(rows[-len(blends):], key=lambda r: r["wf_min_r2"])
        print(
            f"{idx:03d}/{len(structural_configs)} {config['feature_set']} warmup={config['warmup']} "
            f"{config['train_mode']} sw={config['shock_weight']} "
            f"best_blend={best_now['blend']} WF pH={best_now['wf_ph_r2']:.3f} EC={best_now['wf_ec_r2']:.3f}",
            flush=True,
        )

    out = pd.DataFrame(rows).sort_values(
        ["wf_min_r2", "wf_ec_r2", "wf_ph_r2", "ho_ec_r2"],
        ascending=[False, False, False, False],
    )
    os.makedirs("exports", exist_ok=True)
    out.to_csv("exports/shared_simple_huber_warmup_fast_grid12.csv", index=False)
    print("\nTop 25 by walk-forward min R2:")
    print(out.head(25).to_string(index=False))


if __name__ == "__main__":
    main()
