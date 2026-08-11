# preprocessing/preprocess.py

import os
import glob
import hashlib
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split

from config import RAW_DATA_DIR, PROCESSED_DIR, SAMPLE_DIR, LABEL_MERGE_MAP

# Columns that identify a connection but aren't useful as ML features
DROP_COLUMNS = [
    "Flow ID", "Source Port", "Destination Port",
    "Timestamp", "Fwd Header Length.1",
]

LABEL_COLUMN = "Label"
SIMULATED_IP_COLUMN = "Source IP"


def load_raw_data(data_dir: str) -> pd.DataFrame:
    csv_files = glob.glob(os.path.join(data_dir, "*.csv"))
    if not csv_files:
        raise FileNotFoundError(f"No CSV files found in {data_dir}")

    dfs = []
    for f in csv_files:
        df = pd.read_csv(f, low_memory=False)
        df.columns = df.columns.str.strip()
        dfs.append(df)

    return pd.concat(dfs, ignore_index=True)


def merge_and_filter_labels(df: pd.DataFrame) -> pd.DataFrame:
    df = df[df[LABEL_COLUMN].isin(LABEL_MERGE_MAP.keys())].copy()
    df[LABEL_COLUMN] = df[LABEL_COLUMN].map(LABEL_MERGE_MAP)
    return df


def clean_features(df: pd.DataFrame) -> pd.DataFrame:
    existing_drop_cols = [c for c in DROP_COLUMNS if c in df.columns]
    df = df.drop(columns=existing_drop_cols)

    df = df.replace([np.inf, -np.inf], np.nan)

    before = len(df)
    df = df.dropna()
    after = len(df)
    print(f"Dropped {before - after:,} rows containing NaN/inf values")

    return df


def simulate_source_ips(df: pd.DataFrame, n_unique_ips: int = 500) -> pd.Series:
    """
    This dataset (MachineLearningCVE) does not include real IP addresses --
    they're stripped for privacy in the pre-extracted flow-feature CSVs.
    We simulate a source IP per row by hashing a stable combination of
    feature values into one of n_unique_ips buckets, so the prevention
    module (Member 3) has something realistic to block against.
    """
    def row_to_ip(row):
        # Hash a few stable-ish columns to pick a consistent IP bucket
        key = f"{row.get('Flow Duration', 0)}_{row.get('Total Fwd Packets', 0)}_{row.name}"
        bucket = int(hashlib.md5(key.encode()).hexdigest(), 16) % n_unique_ips
        return f"10.0.{bucket // 256}.{bucket % 256}"

    return df.apply(row_to_ip, axis=1)


def run_preprocessing():
    print("Loading raw data...")
    df = load_raw_data(RAW_DATA_DIR)
    print(f"Loaded {len(df):,} raw records")

    print("\nMerging and filtering labels...")
    df = merge_and_filter_labels(df)
    print(f"{len(df):,} records remain after filtering to target classes")
    print(df[LABEL_COLUMN].value_counts())

    print("\nCleaning features...")
    df = clean_features(df)

    print("\nSimulating source IPs (dataset has none)...")
    df[SIMULATED_IP_COLUMN] = simulate_source_ips(df)

    source_ips = df[SIMULATED_IP_COLUMN]
    feature_df = df.drop(columns=[SIMULATED_IP_COLUMN, LABEL_COLUMN])
    labels = df[LABEL_COLUMN]

    print("\nSplitting train/test (80/20, stratified)...")
    X_train, X_test, y_train, y_test, ip_train, ip_test = train_test_split(
        feature_df, labels, source_ips,
        test_size=0.2, stratify=labels, random_state=42
    )

    os.makedirs(PROCESSED_DIR, exist_ok=True)
    os.makedirs(SAMPLE_DIR, exist_ok=True)

    train_df = X_train.copy()
    train_df[LABEL_COLUMN] = y_train
    train_df[SIMULATED_IP_COLUMN] = ip_train
    train_df.to_csv(os.path.join(PROCESSED_DIR, "train.csv"), index=False)

    test_df = X_test.copy()
    test_df[LABEL_COLUMN] = y_test
    test_df[SIMULATED_IP_COLUMN] = ip_test
    test_df.to_csv(os.path.join(PROCESSED_DIR, "test.csv"), index=False)

    sample_parts = []
    for label in test_df[LABEL_COLUMN].unique():
        subset = test_df[test_df[LABEL_COLUMN] == label]
        sample_parts.append(subset.sample(min(len(subset), 200), random_state=42))
    sample_df = pd.concat(sample_parts, ignore_index=True)
    sample_df.to_csv(os.path.join(SAMPLE_DIR, "sample.csv"), index=False)

    print(f"\nSaved train.csv ({len(train_df):,} rows), test.csv ({len(test_df):,} rows)")
    print(f"Saved sample.csv ({len(sample_df):,} rows) — this one goes to Git")


if __name__ == "__main__":
    run_preprocessing()