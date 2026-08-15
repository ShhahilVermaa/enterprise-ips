# preprocessing/replay_simulator.py
"""
Simulates traffic arriving over time by yielding one row at a time
from a dataset, with a configurable delay between records.
Used by run_pipeline.py to make demos feel "live" instead of a
batch script that finishes instantly.
"""

import time
import pandas as pd
from typing import Iterator


def replay(csv_path: str, delay_seconds: float = 0.1, shuffle: bool = True,
           max_records: int = None) -> Iterator[pd.Series]:
    """
    Yields one row at a time from a CSV, pausing `delay_seconds` between
    each -- simulating traffic arriving live rather than being read in
    bulk. Set delay_seconds=0 to replay as fast as possible (still
    row-by-row, useful for testing without waiting).
    """
    df = pd.read_csv(csv_path)

    if shuffle:
        df = df.sample(frac=1, random_state=None).reset_index(drop=True)

    if max_records:
        df = df.head(max_records)

    print(f"Replaying {len(df):,} records "
          f"({'shuffled' if shuffle else 'in original order'}, "
          f"{delay_seconds}s delay between records)...")

    for _, row in df.iterrows():
        yield row
        if delay_seconds > 0:
            time.sleep(delay_seconds)


if __name__ == "__main__":
    # Quick manual test -- replay 10 rows from the sample, fast
    from config import SAMPLE_DIR
    import os

    sample_path = os.path.join(SAMPLE_DIR, "sample.csv")
    count = 0
    for row in replay(sample_path, delay_seconds=0.2, max_records=10):
        count += 1
        print(f"  [{count}] IP={row['Source IP']}, Label={row['Label']}")

    print(f"\nReplayed {count} records successfully.")