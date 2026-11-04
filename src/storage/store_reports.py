
from __future__ import annotations

import json
import logging
import shutil
from pathlib import Path


# ============================================================
# CONFIGURATION
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

VALIDATION_FILE = (
    PROJECT_ROOT
    / "datasets"
    / "reports"
    / "validation"
    / "reports_validation.json"
)

STORAGE_DIR = PROJECT_ROOT / "datasets" / "reports"

VALID_DIR = STORAGE_DIR / "valid"
INVALID_DIR = STORAGE_DIR / "invalid"
DUPLICATES_DIR = STORAGE_DIR / "duplicates"


# ============================================================
# LOGGING
# ============================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)

logger = logging.getLogger(__name__)


# ============================================================
# CREATE STORAGE BRANCHES
# ============================================================

def create_storage_branches() -> None:
    """Create the three report storage branches."""

    for directory in (
        VALID_DIR,
        INVALID_DIR,
        DUPLICATES_DIR,
    ):
        directory.mkdir(parents=True, exist_ok=True)

    logger.info("Storage branches created.")


# ============================================================
# LOAD VALIDATION RESULTS
# ============================================================

def load_validation_results() -> list[dict]:
    """Load the JSON validation report."""

    if not VALIDATION_FILE.exists():
        raise FileNotFoundError(
            f"Validation file not found: {VALIDATION_FILE}. "
            "Run validate_reports.py first."
        )

    with VALIDATION_FILE.open("r", encoding="utf-8") as file:
        results = json.load(file)

    if not isinstance(results, list):
        raise ValueError("Invalid validation results format.")

    return results


# ============================================================
# STORE REPORTS
# ============================================================

def store_reports() -> dict:
    """
    Organize PDF reports into storage branches.

    Priority:
    1. Duplicates
    2. Valid reports
    3. Invalid reports

    Source files are copied, never moved or modified.
    """

    logger.info("Starting report storage.")

    create_storage_branches()

    results = load_validation_results()

    summary = {
        "valid": 0,
        "invalid": 0,
        "duplicates": 0,
        "missing": 0,
    }

    for result in results:

        source_path = Path(result["file_path"])

        if not source_path.exists():
            logger.warning(
                "Source file missing: %s",
                source_path,
            )
            summary["missing"] += 1
            continue

        if result.get("is_duplicate", False):
            destination_dir = DUPLICATES_DIR
            category = "duplicates"

        elif result.get("is_valid", False):
            destination_dir = VALID_DIR
            category = "valid"

        else:
            destination_dir = INVALID_DIR
            category = "invalid"

        destination_path = destination_dir / source_path.name

        # Avoid overwriting an existing file.
        if destination_path.exists():
            logger.warning(
                "Destination already exists, skipping: %s",
                destination_path,
            )
            continue

        try:
            shutil.copy2(source_path, destination_path)

            summary[category] += 1

            logger.info(
                "[%s] Stored: %s",
                category.upper(),
                source_path.name,
            )

        except OSError:
            logger.exception(
                "Failed to store report: %s",
                source_path.name,
            )
            raise

    return summary


# ============================================================
# SUMMARY
# ============================================================

def print_summary(summary: dict) -> None:

    print("\n========== REPORT STORAGE SUMMARY ==========")
    print(f"Valid reports      : {summary['valid']}")
    print(f"Invalid reports    : {summary['invalid']}")
    print(f"Duplicate reports  : {summary['duplicates']}")
    print(f"Missing files      : {summary['missing']}")
    print("============================================\n")


# ============================================================
# EXECUTION
# ============================================================

if __name__ == "__main__":

    summary = store_reports()

    print_summary(summary)
