
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import platform

import pandas as pd



PROJECT_ROOT = Path(".")

ORIGINAL_FILE = Path(
    "datasets/raw/extracted/sensor.csv"
)

SELECTED_FILE = Path(
    "datasets/raw/extracted/sensor_selected.csv"
)

TEMPORAL_FILE = Path(
    "datasets/raw/extracted/sensor_temporal.csv"
)

METADATA_FILE = Path(
    "datasets/metadata/sensor_metadata.json"
)

LINEAGE_DIR = Path(
    "datasets/metadata/lineage"
)

MANIFEST_FILE = LINEAGE_DIR / "ingestion_manifest.json"

HISTORY_FILE = LINEAGE_DIR / "ingestion_history.json"

PIPELINE_VERSION = "1.0.0"


# =====================================================
# HASH CALCULATION
# =====================================================

def calculate_sha256(file_path):

    sha256 = hashlib.sha256()

    with open(file_path, "rb") as file:

        for chunk in iter(
            lambda: file.read(1024 * 1024),
            b""
        ):
            sha256.update(chunk)

    return sha256.hexdigest()


# =====================================================
# FILE INFORMATION
# =====================================================

def get_file_information(file_path):

    if not file_path.exists():
        raise FileNotFoundError(file_path)

    return {
        "file_name": file_path.name,
        "file_path": file_path.as_posix(),
        "file_size_bytes": file_path.stat().st_size,
        "sha256": calculate_sha256(file_path),
        "last_modified": datetime.fromtimestamp(
            file_path.stat().st_mtime,
            tz=timezone.utc
        ).isoformat()
    }




def get_dataset_information():

    df = pd.read_csv(TEMPORAL_FILE)

    df["timestamp"] = pd.to_datetime(
        df["timestamp"],
        errors="raise"
    )

    return {
        "rows": len(df),
        "columns": len(df.columns),
        "start_timestamp": df["timestamp"].min().isoformat(),
        "end_timestamp": df["timestamp"].max().isoformat(),
        "sampling_frequency": "1 minute",
        "sensor_count": len(df.columns) - 2
    }



def load_history():

    if not HISTORY_FILE.exists():
        return []

    with open(HISTORY_FILE, "r", encoding="utf-8") as file:
        return json.load(file)


def track_lineage():

    print("=" * 60)
    print("DATA LINEAGE MANAGEMENT")
    print("=" * 60)

    required_files = [
        ORIGINAL_FILE,
        SELECTED_FILE,
        TEMPORAL_FILE,
        METADATA_FILE
    ]

    for file_path in required_files:
        if not file_path.exists():
            raise FileNotFoundError(
                f"Required file not found: {file_path}"
            )

    # 1. Execution information
    execution_time = datetime.now(
        timezone.utc
    ).isoformat()

    # 2. File information
    files_information = {
        "original_dataset": get_file_information(
            ORIGINAL_FILE
        ),
        "selected_dataset": get_file_information(
            SELECTED_FILE
        ),
        "temporal_dataset": get_file_information(
            TEMPORAL_FILE
        ),
        "sensor_metadata": get_file_information(
            METADATA_FILE
        )
    }

    # 3. Dataset information
    dataset_information = get_dataset_information()

    # 4. Load sensor metadata
    with open(
        METADATA_FILE,
        "r",
        encoding="utf-8"
    ) as file:
        metadata = json.load(file)

    # 5. Build lineage record
    lineage_record = {
        "execution_id": (
            "ingestion_"
            + datetime.now(timezone.utc).strftime(
                "%Y%m%dT%H%M%S%fZ"
            )
        ),

        "execution_time_utc": execution_time,

        "pipeline": {
            "name": "predictive-maintenance-data-ingestion",
            "version": PIPELINE_VERSION,
            "python_version": platform.python_version(),
            "platform": platform.platform()
        },

        "source": {
            "provider": "Kaggle",
            "dataset": "nphantawee/pump-sensor-data",
            "original_file": ORIGINAL_FILE.as_posix()
        },

        "date_transformation": metadata[
            "dataset"
        ]["date_transformation"],

        "dataset_information": dataset_information,

        "files": files_information
    }

    # 6. Create lineage directory
    LINEAGE_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    # 7. Save current manifest
    with open(
        MANIFEST_FILE,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            lineage_record,
            file,
            indent=4,
            ensure_ascii=False
        )

    # 8. Update history
    history = load_history()

    history.append(lineage_record)

    with open(
        HISTORY_FILE,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            history,
            file,
            indent=4,
            ensure_ascii=False
        )

    # 9. Display results
    print("\nDATASET INFORMATION")

    for key, value in dataset_information.items():
        print(f"{key}: {value}")

    print("\nFILE HASHES")

    for name, information in files_information.items():
        print(f"\n{name}")
        print(f"SHA-256: {information['sha256']}")

    print(f"\nManifest saved: {MANIFEST_FILE}")
    print(f"History saved: {HISTORY_FILE}")
    print(f"Total recorded executions: {len(history)}")

    print("\n" + "=" * 60)
    print("DATA LINEAGE COMPLETED")
    print("=" * 60)


if __name__ == "__main__":
    track_lineage()
