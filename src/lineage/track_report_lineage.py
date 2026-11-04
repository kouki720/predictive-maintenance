
from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


# ============================================================
# CONFIGURATION
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

REPORTS_DIR = PROJECT_ROOT / "datasets" / "reports"

STAGING_DIR = (
    PROJECT_ROOT / "datasets" / "staging" / "reports"
)

VALIDATION_FILE = (
    REPORTS_DIR / "validation" / "reports_validation.json"
)

GLOBAL_METADATA_FILE = (
    REPORTS_DIR / "metadata" / "reports_metadata.json"
)

LINEAGE_DIR = REPORTS_DIR / "lineage"

LINEAGE_FILE = LINEAGE_DIR / "reports_lineage.json"

DRIVE_FOLDER_ID = "1hKo4r_UoUiydrez3pXBNl838TuXCCfcc"


# ============================================================
# LOGGING
# ============================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)

logger = logging.getLogger(__name__)


# ============================================================
# HELPERS
# ============================================================

def current_timestamp() -> str:
    """Return the current UTC timestamp."""

    return datetime.now(timezone.utc).isoformat()


def load_json(file_path: Path) -> Any:
    """Load a JSON file."""

    if not file_path.exists():
        raise FileNotFoundError(
            f"Required file not found: {file_path}"
        )

    with file_path.open("r", encoding="utf-8") as file:
        return json.load(file)


def get_storage_category(result: dict) -> str:
    """Determine the final storage branch."""

    if result.get("is_duplicate", False):
        return "duplicates"

    if result.get("is_valid", False):
        return "valid"

    return "invalid"


def get_storage_path(file_name: str, category: str) -> str | None:
    """Find the stored PDF."""

    branch = REPORTS_DIR / category

    if not branch.exists():
        return None

    candidates = list(branch.rglob(file_name))

    if not candidates:
        return None

    return str(candidates[0])


# ============================================================
# BUILD REPORT LINEAGE
# ============================================================

def build_report_lineage(
    validation_result: dict,
    metadata: dict | None = None,
) -> dict:
    """Build the lineage record for one PDF report."""

    file_name = validation_result["file_name"]

    category = get_storage_category(validation_result)

    source_path = validation_result.get("file_path")

    stored_path = get_storage_path(file_name, category)

    sha256 = validation_result.get("sha256")

    if metadata:
        sha256 = metadata.get(
            "file_information", {}
        ).get("sha256", sha256)

    lineage = {
        "report_id": sha256 or file_name,
        "file_name": file_name,

        "source": {
            "platform": "Google Drive",
            "folder_id": DRIVE_FOLDER_ID,
            "original_path": source_path,
        },

        "processing_history": [
            {
                "stage": "ingestion",
                "status": (
                    "completed"
                    if source_path and Path(source_path).exists()
                    else "source_missing"
                ),
                "location": source_path,
            },
            {
                "stage": "validation",
                "status": (
                    "passed"
                    if validation_result.get("is_valid", False)
                    else "failed"
                ),
                "timestamp": current_timestamp(),
                "sha256": sha256,
                "errors": validation_result.get("errors", []),
                "warnings": validation_result.get("warnings", []),
            },
            {
                "stage": "storage",
                "status": (
                    "completed"
                    if stored_path
                    else "not_found"
                ),
                "category": category,
                "location": stored_path,
                "timestamp": current_timestamp(),
            },
            {
                "stage": "metadata",
                "status": (
                    "completed"
                    if metadata is not None
                    else "not_found"
                ),
                "timestamp": current_timestamp(),
            },
        ],

        "final_status": category,

        "integrity": {
            "sha256": sha256,
            "file_size_bytes": validation_result.get(
                "file_size_bytes", 0
            ),
        },

        "lineage_created_at": current_timestamp(),
    }

    return lineage


# ============================================================
# CREATE ALL LINEAGE RECORDS
# ============================================================

def track_report_lineage() -> list[dict]:
    """Generate lineage records for all ingested PDF reports."""

    logger.info("Starting report lineage tracking.")

    validation_results = load_json(VALIDATION_FILE)

    if not isinstance(validation_results, list):
        raise ValueError("Invalid validation results format.")

    metadata_data = load_json(GLOBAL_METADATA_FILE)

    metadata_records = metadata_data.get("reports", [])

    metadata_by_name = {
        item["file_name"]: item
        for item in metadata_records
    }

    lineage_records = []

    for result in validation_results:
        file_name = result["file_name"]

        metadata = metadata_by_name.get(file_name)

        lineage = build_report_lineage(
            validation_result=result,
            metadata=metadata,
        )

        lineage_records.append(lineage)

        logger.info(
            "Lineage created for: %s",
            file_name,
        )

    return lineage_records


# ============================================================
# SAVE LINEAGE
# ============================================================

def save_lineage(records: list[dict]) -> None:
    """Save all lineage records into a JSON file."""

    LINEAGE_DIR.mkdir(parents=True, exist_ok=True)

    output = {
        "dataset_name": "maintenance_reports",
        "source": "Google Drive",
        "total_reports": len(records),
        "generated_at": current_timestamp(),
        "reports": records,
    }

    with LINEAGE_FILE.open("w", encoding="utf-8") as file:
        json.dump(
            output,
            file,
            indent=4,
            ensure_ascii=False,
        )

    logger.info("Lineage saved: %s", LINEAGE_FILE)


# ============================================================
# SUMMARY
# ============================================================

def print_summary(records: list[dict]) -> None:
    """Print lineage tracking summary."""

    total = len(records)

    valid = sum(
        record["final_status"] == "valid"
        for record in records
    )

    invalid = sum(
        record["final_status"] == "invalid"
        for record in records
    )

    duplicates = sum(
        record["final_status"] == "duplicates"
        for record in records
    )

    print("\n========== REPORT LINEAGE SUMMARY ==========")
    print(f"Total reports tracked : {total}")
    print(f"Valid reports         : {valid}")
    print(f"Invalid reports       : {invalid}")
    print(f"Duplicate reports     : {duplicates}")
    print(f"Lineage file          : {LINEAGE_FILE}")
    print("============================================\n")


# ============================================================
# EXECUTION
# ============================================================

if __name__ == "__main__":
    records = track_report_lineage()

    save_lineage(records)

    print_summary(records)
