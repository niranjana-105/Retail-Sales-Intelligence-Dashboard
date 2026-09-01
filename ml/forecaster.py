"""
ml/forecaster.py
================
XGBoost Demand Forecaster — Panel Time-Series Edition
------------------------------------------------------
Trains a single XGBRegressor across all 14 market streams
(7 regions x 2 platforms) and evaluates with the full 5-metric suite:

  1. Overall Pooled R²         — cross-sectional scale discrimination
  2. Per-Series R²             — individual stream fit quality
  3. Median / Mean Per-Series R² — robust central tendency of stream-level fit
  4. Model WAPE                — weighted dollar forecast accuracy
  5. Naive Baseline WAPE       — persistence benchmark (predict last week's sales)
"""

import os
import numpy as np
import pandas as pd
import joblib
from xgboost import XGBRegressor
from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error

MODELS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "models")
MODEL_PATH  = os.path.join(MODELS_DIR, "xgboost_demand_model.joblib")

GROUP_COLS  = ["region", "platform"]
TARGET_COL  = "sales"
DATE_COL    = "week_date"
FEATURE_COLS_BASE = [
    "lag_1", "lag_2", "lag_4", "lag_8",
    "rolling_mean_4", "rolling_mean_8", "rolling_std_4",
    "week_number", "month_number", "quarter", "calendar_year",
]


class XGBoostDemandForecaster:
    """
    Panel XGBoost Demand Forecaster with full 5-metric evaluation suite.
    """

    def __init__(self):
        self.model = XGBRegressor(
            n_estimators     = 100,
            max_depth        = 3,
            learning_rate    = 0.05,
            subsample        = 0.8,
            colsample_bytree = 0.8,
            min_child_weight = 2,
            reg_alpha        = 0.1,
            reg_lambda       = 1.0,
            random_state     = 42,
            verbosity        = 0,
        )
        self.is_trained    = False
        self._feature_cols = None

    # ─────────────────────────────────────────────────
    # Training
    # ─────────────────────────────────────────────────
    def train(self, X_train: pd.DataFrame, y_train: pd.Series) -> None:
        self._feature_cols = list(X_train.columns)
        self.model.fit(X_train, y_train)
        self.is_trained = True
        print(f"Model trained on {len(X_train)} panel observations "
              f"({X_train.shape[1]} features).")

    # ─────────────────────────────────────────────────
    # 5-Metric Evaluation Suite
    # ─────────────────────────────────────────────────
    def evaluate(self, X_test: pd.DataFrame, y_test: pd.Series,
                 df_test: pd.DataFrame, df_train: pd.DataFrame = None,
                 feature_cols: list = None) -> dict:
        """
        Full 5-metric evaluation suite:

        1. Overall Pooled R²          — single R² across all 112 hold-out obs.
        2. Model WAPE                 — weighted absolute % error (all streams).
        3. Naive Baseline WAPE        — persistence model benchmark.
        4. Per-Series R², WAPE, MAE   — per (region, platform) stream breakdown.
        5. Median / Mean Per-Series R² — robust aggregates of stream-level R².
        """
        if not self.is_trained:
            raise RuntimeError("Train the model before evaluating.")

        y_pred  = np.maximum(self.model.predict(X_test), 0)
        y_naive = df_test["naive_pred"].values

        # ── 1. Overall Pooled R² ──────────────────────────────────
        pooled_r2 = r2_score(y_test, y_pred)

        # ── 2 & 3. Model WAPE vs Naive WAPE ──────────────────────
        def wape(actual, pred):
            return float(np.sum(np.abs(actual - pred)) / np.sum(np.abs(actual)) * 100)

        model_wape = wape(y_test.values, y_pred)
        naive_wape = wape(y_test.values, y_naive)

        # ── 4. Per-Series breakdown ───────────────────────────────
        df_eval = df_test.copy()
        df_eval["y_pred"]  = y_pred
        df_eval["y_naive"] = y_naive

        per_series = []
        for (region, platform), grp in df_eval.groupby(GROUP_COLS):
            sr2    = r2_score(grp[TARGET_COL], grp["y_pred"])
            swape  = wape(grp[TARGET_COL].values, grp["y_pred"].values)
            nwape  = wape(grp[TARGET_COL].values, grp["y_naive"].values)
            smae   = float(mean_absolute_error(grp[TARGET_COL], grp["y_pred"]))
            smean  = float(grp[TARGET_COL].mean())
            per_series.append({
                "region":       region,
                "platform":     platform,
                "stream":       f"{region} ({platform})",
                "r2":           round(sr2,   4),
                "model_wape":   round(swape,  2),
                "naive_wape":   round(nwape,  2),
                "beat_naive":   swape < nwape,
                "mae_M":        round(smae,   3),
                "mean_sales_M": round(smean,  2),
            })

        per_series_df = pd.DataFrame(per_series)

        # ── 5. Median / Mean Per-Series R² ───────────────────────
        valid_r2 = per_series_df["r2"]
        median_r2 = float(valid_r2.median())
        mean_r2   = float(valid_r2.mean())
        streams_beat_naive = int(per_series_df["beat_naive"].sum())

        # ── 6. Multi-Step Planning Horizon Evaluation (Recursive) ──
        multi_xgb_wape = None
        multi_nc_wape  = None
        multi_imp      = None
        multi_step_df  = None

        if df_train is not None and feature_cols is not None:
            recursive_preds = []
            for (region, platform), grp_train in df_train.groupby(GROUP_COLS):
                grp_test = df_test[(df_test["region"] == region) & (df_test["platform"] == platform)].sort_values(DATE_COL)
                history = grp_train[TARGET_COL].tolist()
                last_known_val = history[-1]

                stream_dummies = {}
                for c in feature_cols:
                    if c.startswith("region_"):
                        rname = c.replace("region_", "")
                        stream_dummies[c] = 1.0 if region == rname else 0.0
                    elif c.startswith("platform_"):
                        pname = c.replace("platform_", "")
                        stream_dummies[c] = 1.0 if platform == pname else 0.0

                for step_idx, row_test in grp_test.reset_index().iterrows():
                    dt = row_test[DATE_COL]
                    lag_1 = history[-1]
                    lag_2 = history[-2] if len(history) >= 2 else lag_1
                    lag_4 = history[-4] if len(history) >= 4 else lag_1
                    lag_8 = history[-8] if len(history) >= 8 else lag_1
                    rm4   = float(np.mean(history[-4:])) if len(history) >= 4 else float(np.mean(history))
                    rm8   = float(np.mean(history[-8:])) if len(history) >= 8 else float(np.mean(history))
                    std4  = float(np.std(history[-4:]))  if len(history) >= 4 else 0.0
                    wk_num = int(dt.strftime("%W")) + 1
                    mo_num = dt.month
                    qtr    = (mo_num - 1) // 3 + 1
                    yr     = dt.year

                    feat = {
                        "lag_1": lag_1, "lag_2": lag_2, "lag_4": lag_4, "lag_8": lag_8,
                        "rolling_mean_4": rm4, "rolling_mean_8": rm8, "rolling_std_4": std4,
                        "week_number": wk_num, "month_number": mo_num, "quarter": qtr, "calendar_year": yr,
                        **stream_dummies
                    }
                    feat_df = pd.DataFrame([feat])[feature_cols]
                    pred = float(max(self.model.predict(feat_df)[0], 0))
                    history.append(pred)

                    recursive_preds.append({
                        DATE_COL: dt, "region": region, "platform": platform,
                        "sales": row_test[TARGET_COL],
                        "xgb_recursive": pred,
                        "naive_constant": last_known_val,
                        "step": step_idx + 1
                    })

            multi_df = pd.DataFrame(recursive_preds)
            multi_xgb_wape = round(wape(multi_df["sales"].values, multi_df["xgb_recursive"].values), 2)
            multi_nc_wape  = round(wape(multi_df["sales"].values, multi_df["naive_constant"].values), 2)
            multi_imp      = round(multi_nc_wape - multi_xgb_wape, 2)

            step_summary = []
            for s, sgrp in multi_df.groupby("step"):
                xw = wape(sgrp["sales"].values, sgrp["xgb_recursive"].values)
                nw = wape(sgrp["sales"].values, sgrp["naive_constant"].values)
                step_summary.append({
                    "Horizon (Weeks Ahead)": f"t+{s} week",
                    "XGBoost Recursive WAPE": f"{xw:.2f}%",
                    "Naive Constant WAPE": f"{nw:.2f}%",
                    "Winner": "XGBoost" if xw < nw else "Naive",
                    "XGBoost Edge": f"{nw - xw:+.2f}% pts"
                })
            multi_step_df = pd.DataFrame(step_summary)

        metrics = {
            # Pooled metrics (1-step walk forward)
            "pooled_r2":           round(pooled_r2,   4),
            "model_wape":          round(model_wape,  2),
            "naive_wape":          round(naive_wape,  2),
            "wape_improvement":    round(naive_wape - model_wape, 2),
            # Per-series aggregates
            "median_series_r2":    round(median_r2, 4),
            "mean_series_r2":      round(mean_r2,   4),
            "streams_beat_naive":  streams_beat_naive,
            "total_streams":       len(per_series_df),
            # Full per-stream table
            "per_series_df":       per_series_df,
            # Multi-step planning horizon metrics
            "multi_xgb_wape":      multi_xgb_wape,
            "multi_nc_wape":       multi_nc_wape,
            "multi_imp":           multi_imp,
            "multi_step_df":       multi_step_df,
            # Raw predictions array
            "y_pred":              y_pred.tolist(),
        }

        # Console summary
        print("\n=== 5-METRIC EVALUATION SUITE ===")
        print(f"[1] Overall Pooled R2        : {metrics['pooled_r2']:+.4f}")
        print(f"[2] 1-Step Model WAPE        : {metrics['model_wape']:.2f}%")
        print(f"[3] 1-Step Naive WAPE        : {metrics['naive_wape']:.2f}%")
        if multi_xgb_wape is not None:
            print(f"[*] 8-Week Multi-Step WAPE   : XGBoost {multi_xgb_wape:.2f}% vs Naive {multi_nc_wape:.2f}% (XGBoost edge: {multi_imp:+.2f}% pts)")
        print(f"[4] Median Per-Series R2      : {metrics['median_series_r2']:+.4f}")
        print(f"[5] Streams beating naive     : {streams_beat_naive}/{len(per_series_df)}")

        return metrics

    # ─────────────────────────────────────────────────
    # Feature Importance
    # ─────────────────────────────────────────────────
    def get_feature_importance(self) -> pd.DataFrame:
        if not self.is_trained:
            raise RuntimeError("Model must be trained first.")
        importance = self.model.get_booster().get_score(importance_type="gain")
        df_imp = pd.DataFrame(
            list(importance.items()), columns=["Feature", "Gain"]
        ).sort_values("Gain", ascending=False).reset_index(drop=True)
        df_imp["Gain"] = df_imp["Gain"].round(2)
        return df_imp

    # ─────────────────────────────────────────────────
    # Persistence
    # ─────────────────────────────────────────────────
    def save(self, path: str = MODEL_PATH) -> None:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        joblib.dump(self.model, path)
        print(f"Model saved to {path}")

    def load(self, path: str = MODEL_PATH) -> None:
        if not os.path.exists(path):
            raise FileNotFoundError(
                f"No model at '{path}'. Run `python ml/train.py` first."
            )
        self.model      = joblib.load(path)
        self.is_trained = True
        print(f"Model loaded from {path}")

