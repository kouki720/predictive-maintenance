
from __future__ import annotations

import hashlib
import json
import logging
from datetime import datetime, timezone
from pathlib import Path


# ============================================================
# CONFIGURATION
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

REPORTS_DIR = PROJECT_ROOT / "datasets" / "reports"

VALIDATION_FILE = (
    REPORTS_DIR / "validation" / "reports_validation.json"
)

METADATA_DIR = REPORTS_DIR / "metadata"
INDIVIDUAL_METADATA_DIR = METADATA_DIR / "individual"

GLOBAL_METADATA_FILE = METADATA_DIR / "reports_metadata.json"


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

def calculate_sha256(file_path: Path) -> str:
    """Calculate the SHA-256 checksum of a PDF."""

    sha256 = hashlib.sha256()

    with file_path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            sha256.update(chunk)

    return sha256.hexdigest()


def get_stored_file(file_name: str, category: str) -> Path | None:
    """Locate a report in its corresponding storage branch."""

    directories = {
        "valid": REPORTS_DIR / "valid",
        "invalid": REPORTS_DIR / "invalid",
        "duplicates": REPORTS_DIR / "duplicates",
    }

    directory = directories.get(category)

    if directory is None or not directory.exists():
        return None

    candidates = list(directory.rglob(file_name))

    return candidates[0] if candidates else None


# ============================================================
# LOAD VALIDATION RESULTS
# ============================================================

def load_validation_results() -> list[dict]:
    """Load the PDF validation results."""

    if not VALIDATION_FILE.exists():
        raise FileNotFoundError(
            f"Validation results not found: {VALIDATION_FILE}"
        )

    with VALIDATION_FILE.open("r", encoding="utf-8") as file:
        results = json.load(file)

    if not isinstance(results, list):
        raise ValueError("Invalid validation JSON structure.")

    return results


# ============================================================
# BUILD REPORT METADATA
# ============================================================

def build_report_metadata(result: dict) -> dict:
    """Build metadata for one report."""

    file_name = result["file_name"]

    if result.get("is_duplicate", False):
        category = "duplicates"
    elif result.get("is_valid", False):
        category = "valid"
    else:
        category = "invalid"

    stored_path = get_stored_file(file_name, category)

    # Fallback to the staging file if storage has not been run.
    source_path = Path(result["file_path"])

    file_path = (
        stored_path
        if stored_path is not None
        else source_path
    )

    if file_path.exists():
        file_size = file_path.stat().st_size
        sha256 = calculate_sha256(file_path)
    else:
        file_size = result.get("file_size_bytes", 0)
        sha256 = result.get("sha256")

    metadata = {
        "file_name": file_name,
        "source": {
            "type": "google_drive",
            "folder_id": "1hKo4r_UoUiydrez3pXBNl838TuXCCfcc",
            "original_path": result.get("file_path"),
        },
        "storage": {
            "category": category,
            "stored_path": (
                str(stored_path) if stored_path else None
            ),
        },
        "file_information": {
            "extension": file_path.suffix.lower(),
            "size_bytes": file_size,
            "sha256": sha256,
            "page_count": result.get("page_count", 0),
        },
        "validation": {
            "is_pdf": result.get("is_pdf", False),
            "is_readable": result.get("is_readable", False),
            "is_encrypted": result.get("is_encrypted", False),
            "has_extractable_text": result.get(
                "has_extractable_text", False
            ),
            "is_valid": result.get("is_valid", False),
            "is_duplicate": result.get("is_duplicate", False),
            "errors": result.get("errors", []),
            "warnings": result.get("warnings", []),
        },
        "ingestion": {
            "ingestion_date": datetime.now(
                timezone.utc
            ).isoformat(),
            "pipeline": "predictive_maintenance",
        },
    }

    return metadata


# ============================================================
# SAVE INDIVIDUAL METADATA
# ============================================================

def save_individual_metadata(metadata: dict) -> Path:
    """Save metadata for one PDF."""

    INDIVIDUAL_METADATA_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    file_name = Path(metadata["file_name"]).stem

    metadata_path = (
        INDIVIDUAL_METADATA_DIR / f"{file_name}.json"
    )

    with metadata_path.open("w", encoding="utf-8") as file:
        json.dump(
            metadata,
            file,
            indent=4,
            ensure_ascii=False,
        )

    return metadata_path


# ============================================================
# SAVE GLOBAL METADATA
# ============================================================

def save_global_metadata(metadata_list: list[dict]) -> None:
    """Save metadata for all reports in one JSON file."""

    METADATA_DIR.mkdir(parents=True, exist_ok=True)

    global_metadata = {
        "dataset_name": "maintenance_reports",
        "source": "Google Drive",
        "generation_date": datetime.now(
            timezone.utc
        ).isoformat(),
        "total_reports": len(metadata_list),
        "reports": metadata_list,
    }

    with GLOBAL_METADATA_FILE.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            global_metadata,
            file,
            indent=4,
            ensure_ascii=False,
        )

    logger.info("Global metadata saved: %s", GLOBAL_METADATA_FILE)


# ============================================================
# METADATA PIPELINE
# ============================================================

def create_report_metadata() -> list[dict]:
    """Create individual and global metadata for all reports."""

    logger.info("Starting report metadata generation.")

    validation_results = load_validation_results()

    metadata_list = []

    for result in validation_results:
        metadata = build_report_metadata(result)

        metadata_path = save_individual_metadata(metadata)

        metadata_list.append(metadata)

        logger.info(
            "Metadata created: %s",
            metadata_path.name,
        )

    save_global_metadata(metadata_list)

    logger.info(
        "Metadata generation completed. Total reports: %d",
        len(metadata_list),
    )

    return metadata_list


# ============================================================
# EXECUTION
# ============================================================

if __name__ == "__main__":
    metadata = create_report_metadata()

    print("\n========== METADATA SUMMARY ==========")
    print(f"Total reports: {len(metadata)}")
    print(f"Global metadata: {GLOBAL_METADATA_FILE}")
    print(f"Individual metadata: {INDIVIDUAL_METADATA_DIR}")
    print("======================================\n")
