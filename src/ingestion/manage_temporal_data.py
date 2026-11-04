
from pathlib import Path

import pandas as pd


INPUT_FILE = Path("datasets/raw/extracted/sensor_selected.csv")

OUTPUT_DIR = Path("datasets/raw/extracted")
OUTPUT_FILE = OUTPUT_DIR / "sensor_temporal.csv"

TIMESTAMP_COLUMN = "timestamp"


def manage_temporal_data():

    print("=" * 60)
    print("TEMPORAL DATA MANAGEMENT")
    print("=" * 60)

    # 1. Load selected dataset
    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"Dataset not found: {INPUT_FILE}"
        )

    df = pd.read_csv(INPUT_FILE)

    print(f"\nInitial dimensions: {df.shape}")

    # 2. Convert timestamp
    print("\n1. TIMESTAMP CONVERSION")

    df[TIMESTAMP_COLUMN] = pd.to_datetime(
        df[TIMESTAMP_COLUMN],
        errors="coerce"
    )

    invalid_timestamps = df[TIMESTAMP_COLUMN].isna().sum()

    print(f"Invalid timestamps: {invalid_timestamps}")

    if invalid_timestamps > 0:
        raise ValueError(
            "Invalid timestamps detected. "
            "Temporal processing stopped."
        )

    # 3. Check chronological order
    print("\n2. CHRONOLOGICAL ORDER")

    is_chronological = df[TIMESTAMP_COLUMN].is_monotonic_increasing

    print(f"Already chronological: {is_chronological}")

    # We do not reorder data silently.
    if not is_chronological:
        raise ValueError(
            "Dataset is not chronologically ordered."
        )

    # 4. Check duplicate timestamps
    print("\n3. DUPLICATE TIMESTAMPS")

    duplicate_timestamps = df[TIMESTAMP_COLUMN].duplicated().sum()

    print(f"Duplicate timestamps: {duplicate_timestamps}")

    # 5. Sampling frequency
    print("\n4. SAMPLING FREQUENCY")

    differences = (
        df[TIMESTAMP_COLUMN]
        .diff()
        .dropna()
    )

    print("\nMost common intervals:")
    print(differences.value_counts().head(10).to_string())

    if not differences.empty:
        print(
            f"\nMost frequent interval: "
            f"{differences.mode().iloc[0]}"
        )

    # 6. Detect temporal gaps
    print("\n5. TEMPORAL GAPS")

    expected_interval = pd.Timedelta(minutes=1)

    gaps = differences[differences > expected_interval]

    print(f"Number of gaps: {len(gaps)}")

    if not gaps.empty:

        gap_details = pd.DataFrame({
            "previous_timestamp": df[TIMESTAMP_COLUMN].shift(1),
            "current_timestamp": df[TIMESTAMP_COLUMN],
            "interval": differences
        })

        gap_details = gap_details[
            gap_details["interval"] > expected_interval
        ]

        print("\nFirst 10 detected gaps:")
        print(gap_details.head(10).to_string(index=False))

    # 7. Temporal coverage
    print("\n6. TEMPORAL COVERAGE")

    print(f"Start: {df[TIMESTAMP_COLUMN].min()}")
    print(f"End:   {df[TIMESTAMP_COLUMN].max()}")

    expected_rows = (
        int(
            (df[TIMESTAMP_COLUMN].max() -
             df[TIMESTAMP_COLUMN].min()).total_seconds() / 60
        ) + 1
    )

    print(f"Expected rows at 1-minute frequency: {expected_rows:,}")
    print(f"Actual rows: {len(df):,}")

    print(
        f"Difference: {expected_rows - len(df):,}"
    )

    # 8. Save temporal dataset
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    df.to_csv(
        OUTPUT_FILE,
        index=False,
        encoding="utf-8",
        date_format="%Y-%m-%d %H:%M:%S"
    )

    print(f"\nTemporal dataset saved: {OUTPUT_FILE}")

    print("\n" + "=" * 60)
    print("TEMPORAL MANAGEMENT COMPLETED")
    print("=" * 60)

    return df


if __name__ == "__main__":
    manage_temporal_data()
