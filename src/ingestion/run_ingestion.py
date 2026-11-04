
from __future__ import annotations

import json
import subprocess
import sys
import urllib.error
import urllib.request

from pathlib import Path


# ============================================================
# PROJECT CONFIGURATION
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

# Main source dataset
SOURCE_FILE = (
    PROJECT_ROOT
    / "datasets"
    / "raw"
    / "extracted"
    / "sensor.csv"
)

# Sensor statistics report
STATISTICS_FILE = (
    PROJECT_ROOT
    / "datasets"
    / "metadata"
    / "sensor_statistics.json"
)

# FastAPI simulator
SIMULATOR_BASE_URL = "http://127.0.0.1:8000"

HEALTH_ENDPOINT = f"{SIMULATOR_BASE_URL}/health"

SIMULATION_ENDPOINT = (
    f"{SIMULATOR_BASE_URL}/api/simulation/run"
)

REQUEST_TIMEOUT = 30


# ============================================================
# SENSOR INGESTION PIPELINE
# ============================================================

PIPELINE_STEPS = [
    ("Sensor selection", "src.ingestion.select_sensors"),
    ("Temporal data management", "src.ingestion.manage_temporal_data"),
    ("Sensor metadata management", "src.metadata.create_sensor_metadata"),
    ("Data validation", "src.validation.validate_dataset"),
    ("Data lineage", "src.lineage.track_lineage"),
    ("Bronze storage", "src.storage.create_bronze"),
]


# ============================================================
# PDF REPORTS INGESTION PIPELINE
# ============================================================

REPORT_PIPELINE_STEPS = [
    ("PDF reports ingestion", "src.ingestion.load_reports"),
    ("PDF reports validation", "src.validation.validate_reports"),
    ("PDF reports storage", "src.storage.store_reports"),
    ("PDF reports metadata", "src.metadata.create_report_metadata"),
    ("PDF reports lineage", "src.lineage.track_report_lineage"),
]


# ============================================================
# STEP 1: DATASET ACQUISITION
# ============================================================

def acquire_dataset() -> None:
    """
    Download the dataset only when the source file does not exist.
    Never force a new download when the file is already present.
    """

    print("\n" + "=" * 60)
    print("1. DATA SOURCE ACQUISITION")
    print("=" * 60)

    if SOURCE_FILE.exists():
        print(f"Dataset already exists: {SOURCE_FILE}")
        print("Download skipped. Existing dataset will be preserved.")

    else:
        print("Dataset not found. Starting Kaggle download...")

        subprocess.run(
            [
                sys.executable,
                "-m",
                "src.ingestion.download_data",
            ],
            cwd=PROJECT_ROOT,
            check=True,
        )

    if not SOURCE_FILE.exists():
        raise FileNotFoundError(
            f"Dataset acquisition failed: {SOURCE_FILE}"
        )

    if SOURCE_FILE.stat().st_size == 0:
        raise ValueError(
            "The source dataset exists but is empty. "
            "No automatic replacement or download will be performed."
        )

    print(f"Source dataset ready: {SOURCE_FILE}")
    print(f"File size: {SOURCE_FILE.stat().st_size:,} bytes")


# ============================================================
# STEP 2: RUN PIPELINE MODULES
# ============================================================

def run_step(step_name: str, module_name: str) -> None:
    """Execute one pipeline module."""

    print("\n" + "=" * 60)
    print(f"RUNNING: {step_name}")
    print("=" * 60)

    subprocess.run(
        [
            sys.executable,
            "-m",
            module_name,
        ],
        cwd=PROJECT_ROOT,
        check=True,
    )

    print(f"\n{step_name}: COMPLETED")


# ============================================================
# STEP 3: SENSOR STATISTICS
# ============================================================

def ensure_sensor_statistics() -> None:
    """
    Check whether sensor_statistics.json exists.

    If it does not exist, execute the existing
    sensor statistics analysis module.
    """

    print("\n" + "=" * 60)
    print("SENSOR STATISTICS REPORT")
    print("=" * 60)

    if STATISTICS_FILE.exists():

        if STATISTICS_FILE.stat().st_size == 0:
            raise ValueError(
                f"Statistics file exists but is empty: {STATISTICS_FILE}"
            )

        print(f"Statistics report already exists: {STATISTICS_FILE}")
        print("Statistics analysis skipped.")

        return

    print("Statistics report not found.")
    print("Starting sensor statistics analysis...")

    subprocess.run(
        [
            sys.executable,
            "-m",
            "src.simulator.analyze_sensor_statistics",
        ],
        cwd=PROJECT_ROOT,
        check=True,
    )

    if not STATISTICS_FILE.exists():
        raise FileNotFoundError(
            "Sensor statistics analysis completed "
            "but the JSON report was not generated."
        )

    if STATISTICS_FILE.stat().st_size == 0:
        raise ValueError(
            "Generated sensor statistics JSON is empty."
        )

    print("Sensor statistics report generated successfully.")


# ============================================================
# STEP 4: CHECK FASTAPI HEALTH
# ============================================================

def check_simulator_health() -> bool:
    """
    Check whether the FastAPI simulator is operational.

    Returns True only when the endpoint responds successfully
    with an accepted health status.
    """

    print("\n" + "=" * 60)
    print("SIMULATOR HEALTH CHECK")
    print("=" * 60)

    print(f"Checking: {HEALTH_ENDPOINT}")

    request = urllib.request.Request(
        HEALTH_ENDPOINT,
        method="GET",
        headers={
            "Accept": "application/json",
        },
    )

    try:
        with urllib.request.urlopen(
            request,
            timeout=REQUEST_TIMEOUT,
        ) as response:

            if response.status != 200:
                print(
                    f"Health check failed: HTTP {response.status}"
                )
                return False

            health_data = json.loads(
                response.read().decode("utf-8")
            )

            health_status = str(
                health_data.get("status", "")
            ).lower()

            if health_status in {"ok", "healthy"}:

                print("SIMULATOR HEALTH: OK")
                print(f"Response: {health_data}")

                return True

            print("SIMULATOR HEALTH: NOT READY")
            print(f"Response: {health_data}")

            return False

    except urllib.error.URLError as error:

        print("SIMULATOR HEALTH: NOT AVAILABLE")
        print(f"Reason: {error}")

        return False

    except (TimeoutError, json.JSONDecodeError) as error:

        print("SIMULATOR HEALTH: ERROR")
        print(f"Reason: {error}")

        return False


# ============================================================
# STEP 5: CALL SIMULATION API
# ============================================================

def run_simulation_api() -> None:
    """
    Call POST /api/simulation/run only after a successful
    GET /health check.
    """

    print("\n" + "=" * 60)
    print("RUNNING SENSOR SIMULATION")
    print("=" * 60)

    print(f"POST: {SIMULATION_ENDPOINT}")

    request = urllib.request.Request(
        SIMULATION_ENDPOINT,
        data=b"",
        method="POST",
        headers={
            "Accept": "application/json",
        },
    )

    try:
        with urllib.request.urlopen(
            request,
            timeout=REQUEST_TIMEOUT,
        ) as response:

            response_data = json.loads(
                response.read().decode("utf-8")
            )

            if response.status != 200:
                raise RuntimeError(
                    f"Simulation API returned HTTP {response.status}"
                )

            if response_data.get("status") != "success":
                raise RuntimeError(
                    f"Simulation failed: {response_data}"
                )

            print("SIMULATION: COMPLETED")

            print(
                "Generated measurements:",
                response_data.get("generated_count", 0),
            )

            print(
                "Machine status:",
                response_data.get("machine_status"),
            )

            print(
                "First generated timestamp:",
                response_data.get("first_generated_timestamp"),
            )

            print(
                "Last generated timestamp:",
                response_data.get("last_generated_timestamp"),
            )

            print(
                "Simulation plan:",
                response_data.get("simulation_plan"),
            )

    except urllib.error.HTTPError as error:

        error_body = error.read().decode(
            "utf-8",
            errors="replace",
        )

        raise RuntimeError(
            f"Simulation API HTTP error {error.code}: "
            f"{error_body}"
        ) from error

    except urllib.error.URLError as error:

        raise RuntimeError(
            f"Cannot reach simulation API: {error}"
        ) from error


# ============================================================
# COMPLETE PIPELINE
# ============================================================

def run_pipeline() -> None:
    """Execute the complete predictive maintenance pipeline."""

    print("\n")
    print("#" * 60)
    print("PREDICTIVE MAINTENANCE - COMPLETE PIPELINE")
    print("#" * 60)

    try:

        # STEP 1: Acquire source dataset
        acquire_dataset()

        # STEP 2: Execute sensor ingestion operations
        print("\n" + "#" * 60)
        print("SENSOR DATA INGESTION PIPELINE")
        print("#" * 60)

        for step_name, module_name in PIPELINE_STEPS:
            run_step(step_name, module_name)

        # STEP 3: Execute PDF reports pipeline
        print("\n" + "#" * 60)
        print("MAINTENANCE PDF REPORTS PIPELINE")
        print("#" * 60)

        for step_name, module_name in REPORT_PIPELINE_STEPS:
            run_step(step_name, module_name)

        # STEP 4: Ensure sensor statistics JSON exists
        ensure_sensor_statistics()

        # STEP 5: Verify FastAPI health
        simulator_ready = check_simulator_health()

        if not simulator_ready:

            print("\n" + "!" * 60)
            print("SIMULATION SKIPPED")
            print("FastAPI simulator is not operational.")
            print("Start the simulator server and retry.")
            print("!" * 60)

            return

        # STEP 6: Call simulation endpoint
        run_simulation_api()

        print("\n" + "#" * 60)
        print("COMPLETE PIPELINE FINISHED SUCCESSFULLY")
        print("#" * 60)

    except subprocess.CalledProcessError as error:

        print("\n" + "!" * 60)
        print("PIPELINE FAILED")
        print(f"Failed module: {error.cmd}")
        print(f"Exit code: {error.returncode}")
        print("The remaining steps were not executed.")
        print("!" * 60)

        raise

    except Exception as error:

        print("\n" + "!" * 60)
        print("PIPELINE FAILED")
        print(f"Reason: {error}")
        print("!" * 60)

        raise


if __name__ == "__main__":
    run_pipeline()
