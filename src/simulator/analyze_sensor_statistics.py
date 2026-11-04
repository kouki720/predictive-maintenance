
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd


# ============================================================
# PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

INPUT_FILE = (
    PROJECT_ROOT
    / "datasets"
    / "raw"
    / "extracted"
    / "sensor_temporal.csv"
)

OUTPUT_FILE = (
    PROJECT_ROOT
    / "datasets"
    / "metadata"
    / "sensor_statistics.json"
)


# ============================================================
# CONFIGURATION
# ============================================================

TIMESTAMP_COLUMN = "timestamp"
STATUS_COLUMN = "machine_status"

EXPECTED_SENSOR_COUNT = 20
EXPECTED_INTERVAL_MINUTES = 1

AUTOCORRELATION_LAGS = [1, 5, 10]


# ============================================================
# JSON HELPERS
# ============================================================

def safe_float(value: Any) -> float | None:
    """Convertit une valeur numérique en float JSON valide."""

    if value is None or pd.isna(value):
        return None

    return float(value)


# ============================================================
# DATASET VALIDATION
# ============================================================

def load_and_validate_dataset() -> tuple[pd.DataFrame, list[str]]:

    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"Dataset not found: {INPUT_FILE}"
        )

    df = pd.read_csv(INPUT_FILE)

    required_columns = [
        TIMESTAMP_COLUMN,
        STATUS_COLUMN,
    ]

    missing_columns = [
        column
        for column in required_columns
        if column not in df.columns
    ]

    if missing_columns:
        raise ValueError(
            f"Missing required columns: {missing_columns}"
        )

    sensor_columns = [
        column
        for column in df.columns
        if column not in required_columns
    ]

    if len(sensor_columns) != EXPECTED_SENSOR_COUNT:
        raise ValueError(
            f"Expected {EXPECTED_SENSOR_COUNT} sensors, "
            f"but found {len(sensor_columns)}."
        )

    df[TIMESTAMP_COLUMN] = pd.to_datetime(
        df[TIMESTAMP_COLUMN],
        errors="coerce",
    )

    if df[TIMESTAMP_COLUMN].isna().any():
        raise ValueError("Invalid timestamps detected.")

    if df[TIMESTAMP_COLUMN].duplicated().any():
        raise ValueError("Duplicate timestamps detected.")

    if not df[TIMESTAMP_COLUMN].is_monotonic_increasing:
        raise ValueError("Timestamps are not chronological.")

    intervals = df[TIMESTAMP_COLUMN].diff().dropna()

    expected_interval = pd.Timedelta(
        minutes=EXPECTED_INTERVAL_MINUTES
    )

    if not intervals.eq(expected_interval).all():
        raise ValueError(
            "Unexpected temporal gaps detected. "
            "Temporal analysis requires a regular one-minute series."
        )

    for sensor in sensor_columns:
        df[sensor] = pd.to_numeric(
            df[sensor],
            errors="coerce",
        )

    return df, sensor_columns


# ============================================================
# DISTRIBUTION STATISTICS
# ============================================================

def calculate_distribution(
    values: pd.Series,
) -> dict:

    valid_values = values.dropna()

    count = int(valid_values.count())
    missing_count = int(values.isna().sum())

    if count == 0:
        return {
            "min": None,
            "max": None,
            "mean": None,
            "std": None,
            "median": None,
            "q25": None,
            "q75": None,
            "q95": None,
            "count": 0,
            "missing_count": missing_count,
            "missing_percentage": 100.0,
        }

    return {
        "min": safe_float(valid_values.min()),
        "max": safe_float(valid_values.max()),
        "mean": safe_float(valid_values.mean()),
        "std": safe_float(valid_values.std(ddof=1)),
        "median": safe_float(valid_values.median()),
        "q25": safe_float(valid_values.quantile(0.25)),
        "q75": safe_float(valid_values.quantile(0.75)),
        "q95": safe_float(valid_values.quantile(0.95)),
        "count": count,
        "missing_count": missing_count,
        "missing_percentage": round(
            missing_count / len(values) * 100,
            4,
        ),
    }


# ============================================================
# TEMPORAL VARIATION
# ============================================================

def calculate_temporal_variation(
    values: pd.Series,
) -> dict:

    # Diff conserve les positions temporelles.
    # Une valeur manquante ne sera pas ignorée pour
    # créer artificiellement une variation entre deux instants.
    differences = values.diff().dropna()

    absolute_differences = differences.abs()

    if differences.empty:
        return {
            "valid_transitions": 0,
            "mean_change": None,
            "std_change": None,
            "mean_absolute_change": None,
            "max_absolute_change": None,
        }

    return {
        "valid_transitions": int(len(differences)),
        "mean_change": safe_float(differences.mean()),
        "std_change": safe_float(differences.std()),
        "mean_absolute_change": safe_float(
            absolute_differences.mean()
        ),
        "max_absolute_change": safe_float(
            absolute_differences.max()
        ),
    }


# ============================================================
# AUTOCORRELATION
# ============================================================

def calculate_autocorrelation(
    values: pd.Series,
) -> dict:

    results = {}

    for lag in AUTOCORRELATION_LAGS:

        correlation = (
            values.autocorr(lag=lag)
            if len(values) > lag
            else None
        )

        results[f"lag_{lag}"] = safe_float(correlation)

    return results


# ============================================================
# SENSOR ANALYSIS
# ============================================================

def analyze_sensors(
    df: pd.DataFrame,
    sensor_columns: list[str],
) -> dict:

    sensor_results = {}

    for sensor in sensor_columns:

        values = df[sensor]

        sensor_results[sensor] = {
            "distribution": calculate_distribution(values),
            "temporal_variation": calculate_temporal_variation(values),
            "autocorrelation": calculate_autocorrelation(values),
        }

    return sensor_results


# ============================================================
# SENSOR CORRELATION
# ============================================================

def calculate_sensor_correlations(
    df: pd.DataFrame,
    sensor_columns: list[str],
) -> dict:

    correlation_matrix = df[sensor_columns].corr(
        method="pearson"
    )

    correlations = {}

    for sensor, row in correlation_matrix.iterrows():

        correlations[sensor] = {
            other_sensor: safe_float(value)
            for other_sensor, value in row.items()
        }

    return correlations


# ============================================================
# MACHINE STATUS
# ============================================================

def calculate_status_distribution(
    df: pd.DataFrame,
) -> dict:

    counts = df[STATUS_COLUMN].value_counts(
        dropna=False
    )

    return {
        str(status): {
            "count": int(count),
            "percentage": round(
                count / len(df) * 100,
                4,
            ),
        }
        for status, count in counts.items()
    }


# ============================================================
# MAIN ANALYSIS
# ============================================================

def calculate_sensor_statistics() -> None:

    print("=" * 60)
    print("SENSOR STATISTICS AND TEMPORAL ANALYSIS")
    print("=" * 60)

    # 1. Load and validate
    print("\nLoading and validating dataset...")

    df, sensor_columns = load_and_validate_dataset()

    print(f"Dataset dimensions: {df.shape}")
    print(f"Number of sensors: {len(sensor_columns)}")

    # 2. Sensor analysis
    print("\nCalculating sensor statistics...")

    sensor_results = analyze_sensors(
        df,
        sensor_columns,
    )

    # 3. Correlations
    print("Calculating sensor correlations...")

    correlations = calculate_sensor_correlations(
        df,
        sensor_columns,
    )

    # 4. Machine status
    print("Calculating machine status distribution...")

    status_distribution = calculate_status_distribution(df)

    # 5. Temporal information
    temporal_information = {
        "first_timestamp": str(df[TIMESTAMP_COLUMN].iloc[0]),
        "last_timestamp": str(df[TIMESTAMP_COLUMN].iloc[-1]),
        "sampling_interval_minutes": EXPECTED_INTERVAL_MINUTES,
        "chronological": True,
        "duplicate_timestamps": 0,
        "temporal_gaps": 0,
    }

    # 6. Report
    report = {
        "dataset": INPUT_FILE.name,

        "generated_at": datetime.now(
            timezone.utc
        ).isoformat(),

        "number_of_rows": int(len(df)),
        "number_of_sensors": len(sensor_columns),

        "temporal_information": temporal_information,

        "statistics_method": {
            "std": "Sample standard deviation (ddof=1)",
            "missing_values": "Excluded from distribution calculations",
            "temporal_variation": (
                "Differences between adjacent one-minute observations. "
                "Missing observations are not bridged."
            ),
            "autocorrelation": (
                "Pearson autocorrelation at the specified row lags."
            ),
            "correlation": "Pearson correlation",
        },

        "sensors": sensor_results,

        "sensor_correlations": correlations,

        "machine_status_distribution": status_distribution,
    }

    # 7. Save JSON
    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with open(
        OUTPUT_FILE,
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            report,
            file,
            indent=4,
            ensure_ascii=False,
            allow_nan=False,
        )

    # 8. Summary
    print("\n" + "=" * 60)
    print("SENSOR ANALYSIS COMPLETED")
    print("=" * 60)

    print(f"Rows analyzed: {len(df)}")
    print(f"Sensors analyzed: {len(sensor_columns)}")

    print("\nTemporal information:")
    print(f"First: {temporal_information['first_timestamp']}")
    print(f"Last: {temporal_information['last_timestamp']}")

    print("\nGenerated analyses:")
    print("- Distribution statistics")
    print("- Temporal variations")
    print("- Autocorrelation")
    print("- Sensor correlation matrix")
    print("- Machine status distribution")

    print(f"\nReport saved to: {OUTPUT_FILE}")

    print("=" * 60)


if __name__ == "__main__":
    calculate_sensor_statistics()
