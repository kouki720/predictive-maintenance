
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[3]


DATASET_FILE = (
    PROJECT_ROOT
    / "datasets"
    / "raw"
    / "extracted"
    / "sensor_simulation.csv"
)


STATISTICS_FILE = (
    PROJECT_ROOT
    / "datasets"
    / "metadata"
    / "sensor_statistics.json"
)


APP_NAME = "Industrial IoT Sensor Simulator"
APP_VERSION = "1.0.0"

REFERENCE_TIMESTAMP = "2026-11-01 00:01:00"

SAMPLING_INTERVAL_MINUTES = 1

EXPECTED_SENSOR_COUNT = 20

TIMESTAMP_COLUMN = "timestamp"
STATUS_COLUMN = "machine_status"
