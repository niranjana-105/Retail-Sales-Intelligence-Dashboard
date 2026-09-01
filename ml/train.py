"""
ml/train.py
===========
CLI Pipeline — Panel XGBoost Demand Forecasting with 5-Metric Evaluation Suite.

Run from the project root:
    python ml/train.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ml.feature_engineering import (
    fetch_weekly_sales,
    engineer_features,
    encode_dummies,
    get_train_test_split,
    DATE_COL,
    GROUP_COLS,
)
from ml.forecaster import XGBoostDemandForecaster


def main():
    print("=" * 60)
    print("  Retail Panel Demand Forecasting - XGBoost Training")
    print("=" * 60)

    # Step 1: Load panel data from star schema
    print("\n[1/4] Querying Retail Star Schema (Panel Mode)...")
    raw_df = fetch_weekly_sales()
    n_streams = raw_df.groupby(GROUP_COLS).ngroups
    n_weeks   = raw_df["week_date"].nunique()
    print(f"      {n_streams} market streams x {n_weeks} weeks = {len(raw_df)} rows")
    print(f"      Date range: {raw_df[DATE_COL].min().date()} to {raw_df[DATE_COL].max().date()}")

    # Step 2: Feature engineering (partitioned by region + platform)
    print("\n[2/4] Engineering partitioned time-series features...")
    feature_df = engineer_features(raw_df)
    df_enc, feature_cols = encode_dummies(feature_df)
    print(f"      {len(feature_df)} usable observations after lag warm-up.")
    print(f"      {len(feature_cols)} features (lags + rolling + calendar + dummies)")

    # Step 3: Chronological panel split
    print("\n[3/4] Chronological panel split (last 8 weeks per stream held out)...")
    X_train, X_test, y_train, y_test, df_train, df_test = get_train_test_split(
        feature_df, df_enc, feature_cols
    )
    print(f"      Training : {len(X_train)} panel obs  "
          f"({df_train[DATE_COL].min().date()} to {df_train[DATE_COL].max().date()})")
    print(f"      Test     : {len(X_test)} panel obs  "
          f"({df_test[DATE_COL].min().date()} to {df_test[DATE_COL].max().date()})")

    # Step 4: Train + Full 5-Metric Evaluation + Save
    print("\n[4/4] Training XGBoost Regressor...")
    forecaster = XGBoostDemandForecaster()
    forecaster.train(X_train, y_train)

    print("\n      Running full 5-metric evaluation suite (including 8-week multi-step horizon)...")
    metrics = forecaster.evaluate(X_test, y_test, df_test, df_train=df_train, feature_cols=feature_cols)

    print("\n      Saving model artifact...")
    forecaster.save()

    # Feature importance
    print("\nTop Feature Importances (by Gain):")
    print(forecaster.get_feature_importance().head(8).to_string(index=False))

    print("\n" + "=" * 60)
    print("  Pipeline complete.")
    print("  Run: streamlit run app.py -> Page 6: Demand Forecasting")
    print("=" * 60)


if __name__ == "__main__":
    main()
