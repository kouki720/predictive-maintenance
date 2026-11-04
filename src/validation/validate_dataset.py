
from pathlib import Path
import json

import numpy as np
import pandas as pd


# =====================================================
# CONFIGURATION
# =====================================================

INPUT_FILE = Path(
    "datasets/raw/extracted/sensor_temporal.csv"
)

METADATA_FILE = Path(
    "datasets/metadata/sensor_metadata.json"
)

REPORT_DIR = Path(
    "datasets/reports/validation"
)

REPORT_FILE = REPORT_DIR / "validation_report.json"


# =====================================================
# VALIDATION
# =====================================================

def validate_dataset():

    print("=" * 60)
    print("DATA VALIDATION")
    print("=" * 60)

    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"Dataset not found: {INPUT_FILE}"
        )

    if not METADATA_FILE.exists():
        raise FileNotFoundError(
            f"Metadata not found: {METADATA_FILE}"
        )

    # 1. Load dataset and metadata
    df = pd.read_csv(INPUT_FILE)

    with open(METADATA_FILE, "r", encoding="utf-8") as file:
        metadata = json.load(file)

    sensors = metadata["sensors"]

    sensor_columns = [
        sensor["selected_column"] for sensor in sensors
    ]

    required_columns = [
        "timestamp",
        *sensor_columns,
        "machine_status"
    ]

    results = {}

    print(f"\nDataset dimensions: {df.shape}")

    # =================================================
    # 2. SCHEMA VALIDATION
    # =================================================

    print("\n1. SCHEMA VALIDATION")

    missing_columns = [
        col for col in required_columns
        if col not in df.columns
    ]

    unexpected_columns = [
        col for col in df.columns
        if col not in required_columns
    ]

    schema_valid = (
        len(missing_columns) == 0
        and len(unexpected_columns) == 0
    )

    results["schema"] = {
        "valid": schema_valid,
        "expected_columns": len(required_columns),
        "actual_columns": len(df.columns),
        "missing_columns": missing_columns,
        "unexpected_columns": unexpected_columns
    }

    print(f"Schema valid: {schema_valid}")
    print(f"Missing columns: {missing_columns}")
    print(f"Unexpected columns: {unexpected_columns}")

    # =================================================
    # 3. DATA TYPE VALIDATION
    # =================================================

    print("\n2. DATA TYPE VALIDATION")

    type_errors = []

    if "timestamp" not in df.columns:
        type_errors.append("timestamp column missing")
    else:
        parsed_timestamp = pd.to_datetime(
            df["timestamp"],
            errors="coerce"
        )

        if parsed_timestamp.isna().any():
            type_errors.append("Invalid timestamp values")

    for column in sensor_columns:

        if column not in df.columns:
            continue

        if not pd.api.types.is_numeric_dtype(df[column]):
            type_errors.append(
                f"{column} must be numeric"
            )

    if "machine_status" in df.columns:
        if not pd.api.types.is_string_dtype(
            df["machine_status"].dtype
        ):
            type_errors.append(
                "machine_status must be textual"
            )

    results["data_types"] = {
        "valid": len(type_errors) == 0,
        "errors": type_errors
    }

    print(f"Type validation: {len(type_errors) == 0}")

    for error in type_errors:
        print(f"ERROR: {error}")

    # =================================================
    # 4. MISSING VALUES
    # =================================================

    print("\n3. MISSING VALUES")

    missing_counts = df[required_columns].isna().sum()

    missing_report = {}

    for column, count in missing_counts.items():

        percentage = (
            count / len(df) * 100
            if len(df) > 0 else 0
        )

        missing_report[column] = {
            "count": int(count),
            "percentage": round(float(percentage), 4)
        }

        if count > 0:
            print(
                f"{column}: {count} "
                f"({percentage:.2f}%)"
            )

    results["missing_values"] = {
        "total_missing": int(missing_counts.sum()),
        "columns": missing_report
    }

    # =================================================
    # 5. INFINITE VALUES
    # =================================================

    print("\n4. INFINITE VALUES")

    numeric_columns = [
        col for col in sensor_columns
        if col in df.columns
    ]

    infinite_report = {}

    for column in numeric_columns:

        values = df[column].to_numpy(
            dtype=float,
            na_value=np.nan
        )

        count = int(np.isinf(values).sum())

        infinite_report[column] = count

        if count > 0:
            print(f"{column}: {count} infinite values")

    total_infinite = sum(infinite_report.values())

    results["infinite_values"] = {
        "total": total_infinite,
        "columns": infinite_report
    }

    # =================================================
    # 6. NUMERIC VALUE VALIDATION
    # =================================================

    print("\n5. NUMERIC VALUE VALIDATION")

    numeric_report = {}

    for column in numeric_columns:

        numeric_report[column] = {
            "minimum": (
                float(df[column].min())
                if pd.notna(df[column].min())
                else None
            ),
            "maximum": (
                float(df[column].max())
                if pd.notna(df[column].max())
                else None
            )
        }

    results["numeric_values"] = {
        "note": (
            "Observed minimum and maximum values. "
            "No official engineering limits were supplied."
        ),
        "columns": numeric_report
    }

    print("Numeric ranges collected.")
    print("No undocumented physical limits were imposed.")

    # =================================================
    # 7. TIMESTAMP VALIDATION
    # =================================================

    print("\n6. TIMESTAMP VALIDATION")

    timestamp = pd.to_datetime(
        df["timestamp"],
        errors="coerce"
    )

    invalid_timestamps = int(timestamp.isna().sum())

    valid_timestamp = timestamp.dropna()

    chronological = bool(
        valid_timestamp.is_monotonic_increasing
    )

    duplicate_timestamps = int(
        timestamp.duplicated().sum()
    )

    intervals = valid_timestamp.diff().dropna()

    gaps = int(
        (intervals > pd.Timedelta(minutes=1)).sum()
    )

    timestamp_report = {
        "invalid_timestamps": invalid_timestamps,
        "chronological": chronological,
        "duplicate_timestamps": duplicate_timestamps,
        "gaps": gaps,
        "start": (
            str(valid_timestamp.iloc[0])
            if not valid_timestamp.empty else None
        ),
        "end": (
            str(valid_timestamp.iloc[-1])
            if not valid_timestamp.empty else None
        )
    }

    results["timestamp"] = timestamp_report

    print(f"Invalid timestamps: {invalid_timestamps}")
    print(f"Chronological: {chronological}")
    print(f"Duplicate timestamps: {duplicate_timestamps}")
    print(f"Temporal gaps: {gaps}")

    # =================================================
    # 8. METADATA VALIDATION
    # =================================================

    print("\n7. METADATA VALIDATION")

    metadata_columns = {
        sensor["selected_column"]
        for sensor in sensors
    }

    actual_sensor_columns = set(sensor_columns)

    metadata_valid = (
        len(sensors) == 20
        and metadata_columns == actual_sensor_columns
        and all(
            sensor.get("sensor_id")
            and sensor.get("sensor_name")
            and sensor.get("sensor_type")
            for sensor in sensors
        )
    )

    results["metadata"] = {
        "valid": metadata_valid,
        "declared_sensors": len(sensors),
        "matched_columns": len(
            metadata_columns.intersection(df.columns)
        )
    }

    print(f"Metadata valid: {metadata_valid}")

    # =================================================
    # 9. FINAL VALIDATION STATUS
    # =================================================

    validation_passed = all([
        schema_valid,
        len(type_errors) == 0,
        total_infinite == 0,
        invalid_timestamps == 0,
        chronological,
        duplicate_timestamps == 0,
        gaps == 0,
        metadata_valid
    ])

    results["summary"] = {
        "validation_passed": validation_passed,
        "rows": len(df),
        "columns": len(df.columns),
        "sensor_count": len(sensors)
    }

    # =================================================
    # 10. SAVE REPORT
    # =================================================

    REPORT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    with open(
        REPORT_FILE,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            results,
            file,
            indent=4,
            ensure_ascii=False,
            allow_nan=False
        )

    print("\n" + "=" * 60)

    print(
        "VALIDATION PASSED"
        if validation_passed
        else "VALIDATION COMPLETED WITH ISSUES"
    )

    print(f"Report saved to: {REPORT_FILE}")

    print("=" * 60)

    return results


if __name__ == "__main__":
    validate_dataset()
