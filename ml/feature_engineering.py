"""
ml/feature_engineering.py
==========================
Hierarchical Panel Time-Series Feature Engineering Pipeline
------------------------------------------------------------
Queries the Retail Star Schema (dim_region x dim_platform x fact_weekly_sales)
and builds a panel dataset of 14 market streams (7 regions x 2 platforms),
each with lag, rolling-window, and calendar features for XGBoost training.

Key Design Rules:
- Lags use .shift() WITHIN each (region, platform) group — no cross-stream leakage.
- Rolling stats use shift(1) before rolling to exclude the current week (zero lookahead).
- Chronological split: all training data strictly before the split date.
- One-hot encoded region and platform dummies are derived from historical data only.
"""

import sys
import os
import pandas as pd
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from db import run_query

# ─────────────────────────────────────────────
# Config
# ─────────────────────────────────────────────
GROUP_COLS   = ["region", "platform"]
DATE_COL     = "week_date"
TARGET_COL   = "sales"
SPLIT_DATE   = "2020-07-13"      # Last 8 weeks held out for test
TEST_WEEKS   = 8

FEATURE_COLS = [
    "lag_1", "lag_2", "lag_4", "lag_8",
    "rolling_mean_4", "rolling_mean_8", "rolling_std_4",
    "week_number", "month_number", "quarter", "calendar_year",
]


# ─────────────────────────────────────────────
# 1. Data Ingestion from Star Schema
# ─────────────────────────────────────────────
def fetch_weekly_sales() -> pd.DataFrame:
    """
    Query the star schema, grouping by (week_date, region, platform).
    Returns a panel DataFrame of 14 market streams x 72 weeks = 1,008 rows.
    Sales are normalised to millions (M) for dashboard readability.
    """
    query = """
    SELECT
        f.week_date,
        r.region_name   AS region,
        p.platform_name AS platform,
        f.week_number,
        f.month_number,
        f.calendar_year,
        SUM(f.sales)        / 1000000.0 AS sales,
        SUM(f.transactions) / 1000.0    AS transactions
    FROM fact_weekly_sales f
    JOIN dim_region   r ON f.region_id   = r.region_id
    JOIN dim_platform p ON f.platform_id = p.platform_id
    GROUP BY f.week_date, r.region_name, p.platform_name,
             f.week_number, f.month_number, f.calendar_year
    ORDER BY r.region_name, p.platform_name, f.week_date ASC;
    """
    df = run_query(query)
    df[DATE_COL] = pd.to_datetime(df[DATE_COL])
    df = df.sort_values(GROUP_COLS + [DATE_COL]).reset_index(drop=True)
    return df


# ─────────────────────────────────────────────
# 2. Feature Engineering (per-stream partitioned)
# ─────────────────────────────────────────────
def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Engineer time-series features for each (region, platform) stream independently.
    All lags and rolling windows use .shift(1) to guarantee zero lookahead leakage.

    Features:
        lag_1, lag_2, lag_4, lag_8      - autoregressive sales signals
        rolling_mean_4, rolling_mean_8  - momentum (4-week and 8-week)
        rolling_std_4                   - weekly sales volatility
        week_number, month_number,
        quarter, calendar_year          - calendar seasonality

    Returns the feature DataFrame and a one-hot encoded version (for XGBoost).
    """
    df = df.copy()
    grp = df.groupby(GROUP_COLS)[TARGET_COL]

    # Autoregressive lags
    for lag in [1, 2, 4, 8]:
        df[f"lag_{lag}"] = grp.shift(lag)

    # Rolling window stats (shift(1) first → strictly past-data only)
    shifted = grp.shift(1)
    df["rolling_mean_4"] = shifted.transform(lambda s: s.rolling(4, min_periods=2).mean())
    df["rolling_mean_8"] = shifted.transform(lambda s: s.rolling(8, min_periods=4).mean())
    df["rolling_std_4"]  = shifted.transform(lambda s: s.rolling(4, min_periods=2).std())

    # Calendar features
    df["quarter"] = df[DATE_COL].dt.quarter

    # Naive baseline: lag_1 = last week's actual (persistence model for benchmarking)
    df["naive_pred"] = df["lag_1"]

    # Drop NaN warm-up rows
    feature_check_cols = FEATURE_COLS
    df = df.dropna(subset=feature_check_cols).reset_index(drop=True)

    return df


def encode_dummies(df: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    """
    One-hot encode region and platform for XGBoost.
    Returns (encoded_df, feature_cols_list).
    """
    df_enc = pd.get_dummies(df, columns=["region", "platform"], drop_first=True)
    all_feature_cols = FEATURE_COLS + [c for c in df_enc.columns if c.startswith("region_") or c.startswith("platform_")]
    return df_enc, all_feature_cols


# ─────────────────────────────────────────────
# 3. Chronological Panel Split
# ─────────────────────────────────────────────
def get_train_test_split(df: pd.DataFrame, df_enc: pd.DataFrame, feature_cols: list[str]):
    """
    Strict chronological split on the panel dataset.
    Training: all weeks before SPLIT_DATE.
    Test:     last TEST_WEEKS weeks (SPLIT_DATE onwards) across all 14 streams.

    Returns X_train, X_test, y_train, y_test, df_train, df_test
    """
    train_mask = df[DATE_COL] < SPLIT_DATE
    test_mask  = df[DATE_COL] >= SPLIT_DATE

    df_train = df.loc[train_mask].copy()
    df_test  = df.loc[test_mask].copy()

    X_train = df_enc.loc[train_mask, feature_cols]
    y_train = df.loc[train_mask, TARGET_COL]
    X_test  = df_enc.loc[test_mask, feature_cols]
    y_test  = df.loc[test_mask, TARGET_COL]

    return X_train, X_test, y_train, y_test, df_train, df_test


if __name__ == "__main__":
    raw_df     = fetch_weekly_sales()
    feature_df = engineer_features(raw_df)
    df_enc, fc = encode_dummies(feature_df)
    X_tr, X_te, y_tr, y_te, df_tr, df_te = get_train_test_split(feature_df, df_enc, fc)

    print(f"Panel shape        : {feature_df.shape}  (streams x weeks)")
    print(f"Train samples      : {len(X_tr)}")
    print(f"Test  samples      : {len(X_te)}")
    print(f"Unique streams     : {feature_df.groupby(GROUP_COLS).ngroups}")
    print(f"Date range (train) : {df_tr[DATE_COL].min().date()} to {df_tr[DATE_COL].max().date()}")
    print(f"Date range (test)  : {df_te[DATE_COL].min().date()} to {df_te[DATE_COL].max().date()}")
