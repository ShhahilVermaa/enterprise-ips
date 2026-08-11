# preprocessing/verify_dataset.py

import pandas as pd
import glob
import os

DATA_DIR = "data/raw/MachineLearningCVE"

def load_all_csvs(data_dir: str) -> pd.DataFrame:
    """Load and concatenate all CICIDS2017 CSV files."""
    csv_files = glob.glob(os.path.join(data_dir, "*.csv"))
    if not csv_files:
        raise FileNotFoundError(
            f"No CSV files found in {data_dir}. Did you unzip the dataset there?"
        )

    print(f"Found {len(csv_files)} CSV files:")
    for f in csv_files:
        print(f"  - {os.path.basename(f)}")

    dfs = []
    for f in csv_files:
        df = pd.read_csv(f, low_memory=False)
        # CICIDS2017 CSVs have inconsistent column name spacing — clean it
        df.columns = df.columns.str.strip()
        dfs.append(df)

    combined = pd.concat(dfs, ignore_index=True)
    return combined


def report_class_distribution(df: pd.DataFrame):
    """Print how many rows exist per label."""
    if "Label" not in df.columns:
        raise KeyError("Expected a 'Label' column — check the CSV headers.")

    counts = df["Label"].value_counts()
    total = len(df)

    print(f"\nTotal records: {total:,}")
    print("\nClass distribution:")
    for label, count in counts.items():
        pct = (count / total) * 100
        print(f"  {label:<30} {count:>10,}  ({pct:.2f}%)")

    return counts


if __name__ == "__main__":
    df = load_all_csvs(DATA_DIR)
    counts = report_class_distribution(df)