
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import shutil


# =====================================================
# CONFIGURATION
# =====================================================

SOURCE_FILE = Path(
    "datasets/raw/extracted/sensor.csv"
)

BRONZE_ROOT = Path(
    "datasets/bronze/pump_sensor_data"
)

PIPELINE_VERSION = "1.0.0"


# =====================================================
# SHA-256
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
# BRONZE STORAGE
# =====================================================

def create_bronze_storage():

    print("=" * 60)
    print("RAW / BRONZE STORAGE")
    print("=" * 60)

    # 1. Verify source file
    if not SOURCE_FILE.exists():
        raise FileNotFoundError(
            f"Source file not found: {SOURCE_FILE}"
        )

    print(f"\nSource: {SOURCE_FILE}")

    # 2. Calculate source hash
    source_hash = calculate_sha256(SOURCE_FILE)

    print(f"Source SHA-256: {source_hash}")

    # 3. Create version directory
    version = source_hash[:12]

    version_dir = BRONZE_ROOT / version

    version_dir.mkdir(
        parents=True,
        exist_ok=True
    )

    bronze_file = version_dir / "sensor.csv"

    metadata_file = version_dir / "bronze_metadata.json"

    # 4. Check whether this version already exists
    if bronze_file.exists():

        existing_hash = calculate_sha256(bronze_file)

        if existing_hash != source_hash:
            raise ValueError(
                "Existing Bronze file has a different hash."
            )

        print("\nThis dataset version already exists.")
        print("No new copy created.")

    else:

        # 5. Copy original file without modifying it
        shutil.copy2(
            SOURCE_FILE,
            bronze_file
        )

        # 6. Verify copied file
        bronze_hash = calculate_sha256(bronze_file)

        if bronze_hash != source_hash:
            raise ValueError(
                "Bronze copy verification failed."
            )

        print("\nBronze copy created successfully.")
        print("SHA-256 verification: PASSED")

    # 7. Build Bronze metadata
    bronze_metadata = {

        "storage_layer": "BRONZE",

        "dataset_name": "Pump Sensor Data",

        "source": {
            "provider": "Kaggle",
            "dataset": "nphantawee/pump-sensor-data",
            "original_file": SOURCE_FILE.as_posix()
        },

        "bronze_file": {
            "file_name": bronze_file.name,
            "file_path": bronze_file.as_posix(),
            "file_size_bytes": bronze_file.stat().st_size,
            "sha256": source_hash,
            "version": version
        },

        "ingestion": {
            "ingestion_timestamp_utc": datetime.now(
                timezone.utc
            ).isoformat(),

            "pipeline_version": PIPELINE_VERSION,

            "copy_method": "shutil.copy2",

            "source_preserved": True,

            "hash_verification": "passed"
        },

        "data_preservation": {
            "original_data_modified": False,
            "date_shift_applied_to_bronze": False,
            "description": (
                "Bronze contains an exact copy of the original "
                "dataset. Date shifting and sensor selection "
                "remain separate operations in extracted files."
            )
        },

        "related_files": {
            "selected_dataset": (
                "datasets/raw/extracted/sensor_selected.csv"
            ),

            "temporal_dataset": (
                "datasets/raw/extracted/sensor_temporal.csv"
            )
        }
    }

    # 8. Save metadata
    with open(
        metadata_file,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            bronze_metadata,
            file,
            indent=4,
            ensure_ascii=False
        )

    # 9. Display results
    print("\nBRONZE STORAGE SUMMARY")
    print("-" * 60)

    print(f"Dataset version: {version}")
    print(f"Bronze file: {bronze_file}")
    print(f"Metadata: {metadata_file}")
    print(f"File size: {bronze_file.stat().st_size:,} bytes")
    print(f"SHA-256: {source_hash}")

    print("\nOriginal dataset preserved: YES")
    print("Bronze copy verified: YES")

    print("\n" + "=" * 60)
    print("BRONZE STORAGE COMPLETED")
    print("=" * 60)


if __name__ == "__main__":
    create_bronze_storage()
