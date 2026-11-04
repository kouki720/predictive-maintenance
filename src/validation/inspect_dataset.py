
from pathlib import Path

import pandas as pd


DATASET_PATH = Path("datasets/raw/extracted/sensor.csv")


def inspect_dataset():

    print("=" * 60)
    print("       DATASET STRUCTURE INSPECTION")
    print("=" * 60)

    if not DATASET_PATH.exists():
        raise FileNotFoundError(
            f"Dataset introuvable : {DATASET_PATH}"
        )

    df = pd.read_csv(DATASET_PATH)

    # 1. Dimensions
    print("\n1. DATASET DIMENSIONS")
    print("-" * 40)
    print(f"Rows       : {df.shape[0]:,}")
    print(f"Columns    : {df.shape[1]}")
    print(f"Memory     : {df.memory_usage(deep=True).sum() / (1024**2):.2f} MB")

    # 2. Colonnes et types
    print("\n2. COLUMN TYPES")
    print("-" * 40)
    print(df.dtypes.to_string())

    # 3. Valeurs manquantes
    print("\n3. MISSING VALUES")
    print("-" * 40)

    missing = pd.DataFrame({
        "missing_count": df.isnull().sum(),
        "missing_percent": df.isnull().mean() * 100
    })

    print(missing[missing["missing_count"] > 0].to_string())

    if not df.isnull().any().any():
        print("No missing values detected.")

    # 4. Doublons
    print("\n4. DUPLICATE RECORDS")
    print("-" * 40)
    print(f"Duplicate rows: {df.duplicated().sum():,}")

    # 5. Analyse temporelle
    print("\n5. TEMPORAL ANALYSIS")
    print("-" * 40)

    if "timestamp" in df.columns:

        timestamps = pd.to_datetime(
            df["timestamp"],
            errors="coerce"
        )

        print(f"Invalid timestamps: {timestamps.isna().sum():,}")
        print(f"Start date: {timestamps.min()}")
        print(f"End date  : {timestamps.max()}")

        valid_timestamps = timestamps.dropna().sort_values()

        differences = valid_timestamps.diff().dropna()

        print("\nMost common time intervals:")
        print(differences.value_counts().head(10).to_string())

        print(
            "\nDuplicate timestamps:",
            timestamps.duplicated().sum()
        )

    # 6. Machine status
    print("\n6. MACHINE STATUS DISTRIBUTION")
    print("-" * 40)

    if "machine_status" in df.columns:

        print(df["machine_status"].value_counts(dropna=False).to_string())

        print("\nStatus percentages:")
        print(
            (df["machine_status"].value_counts(normalize=True, dropna=False) * 100)
            .round(2)
            .to_string()
        )

    # 7. Sensor columns
    print("\n7. SENSOR COLUMNS")
    print("-" * 40)

    sensor_columns = [
        col for col in df.columns
        if col.startswith("sensor_")
    ]

    print(f"Number of sensors: {len(sensor_columns)}")
    print(sensor_columns)

    # 8. Sensor statistics
    print("\n8. SENSOR STATISTICS")
    print("-" * 40)

    print(
        df[sensor_columns]
        .describe()
        .round(3)
        .to_string()
    )

    print("\n" + "=" * 60)
    print("INSPECTION COMPLETED")
    print("=" * 60)


if __name__ == "__main__":
    inspect_dataset()
