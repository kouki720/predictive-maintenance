
from __future__ import annotations

import hashlib
import json
import logging
from pathlib import Path

from pypdf import PdfReader


# ============================================================
# CONFIGURATION
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

STAGING_DIR = PROJECT_ROOT / "datasets" / "staging" / "reports"

VALIDATION_DIR = (
    PROJECT_ROOT / "datasets" / "reports" / "validation"
)

VALIDATION_FILE = VALIDATION_DIR / "reports_validation.json"


# ============================================================
# LOGGING
# ============================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)

logger = logging.getLogger(__name__)


# ============================================================
# HASHING
# ============================================================

def calculate_sha256(file_path: Path) -> str:
    """Calculate the SHA-256 hash of a file."""

    sha256 = hashlib.sha256()

    with file_path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            sha256.update(chunk)

    return sha256.hexdigest()


# ============================================================
# PDF VALIDATION
# ============================================================

def validate_pdf(file_path: Path) -> dict:
    """Validate the technical integrity and readability of a PDF."""

    result = {
        "file_name": file_path.name,
        "file_path": str(file_path),
        "file_size_bytes": 0,
        "sha256": None,
        "page_count": 0,
        "is_pdf": False,
        "is_readable": False,
        "is_encrypted": False,
        "has_extractable_text": False,
        "is_valid": False,
        "is_duplicate": False,
        "errors": [],
        "warnings": [],
    }

    try:
        if not file_path.exists() or not file_path.is_file():
            raise FileNotFoundError("File does not exist.")

        if file_path.suffix.lower() != ".pdf":
            result["errors"].append("Invalid file extension.")
            return result

        result["file_size_bytes"] = file_path.stat().st_size

        if result["file_size_bytes"] == 0:
            result["errors"].append("PDF file is empty.")
            return result

        result["sha256"] = calculate_sha256(file_path)

        reader = PdfReader(str(file_path), strict=True)

        result["is_pdf"] = True

        if reader.is_encrypted:
            result["is_encrypted"] = True
            result["errors"].append("PDF is encrypted.")
            return result

        result["page_count"] = len(reader.pages)

        if result["page_count"] == 0:
            result["errors"].append("PDF contains no pages.")
            return result

        result["is_readable"] = True

        extracted_text = []

        for page in reader.pages:
            text = page.extract_text()
            if text:
                extracted_text.append(text)

        result["has_extractable_text"] = any(
            text.strip() for text in extracted_text
        )

        if not result["has_extractable_text"]:
            result["warnings"].append(
                "PDF has no extractable text. "
                "It may be a scanned document."
            )

        # Technical validity is independent of text extraction.
        result["is_valid"] = True

    except Exception as error:
        result["errors"].append(str(error))

    return result


# ============================================================
# DUPLICATE DETECTION
# ============================================================

def detect_duplicates(results: list[dict]) -> None:
    """Identify files sharing the same SHA-256 hash."""

    seen_hashes = {}

    for result in results:
        file_hash = result["sha256"]

        if not file_hash:
            continue

        if file_hash in seen_hashes:
            result["is_duplicate"] = True
            result["warnings"].append(
                f"Duplicate of {seen_hashes[file_hash]}"
            )
        else:
            seen_hashes[file_hash] = result["file_name"]


# ============================================================
# VALIDATE ALL REPORTS
# ============================================================

def validate_reports() -> list[dict]:
    """Validate every PDF found in the staging directory."""

    logger.info("Starting PDF validation.")

    if not STAGING_DIR.exists():
        raise FileNotFoundError(
            f"Staging directory not found: {STAGING_DIR}"
        )

    pdf_files = sorted(
        file_path
        for file_path in STAGING_DIR.rglob("*")
        if file_path.is_file()
        and file_path.suffix.lower() == ".pdf"
    )

    logger.info("PDF files found: %d", len(pdf_files))

    results = [
        validate_pdf(file_path)
        for file_path in pdf_files
    ]

    detect_duplicates(results)

    return results


# ============================================================
# SAVE VALIDATION RESULTS
# ============================================================

def save_validation_results(results: list[dict]) -> None:
    """Save validation results as JSON."""

    VALIDATION_DIR.mkdir(parents=True, exist_ok=True)

    with VALIDATION_FILE.open("w", encoding="utf-8") as file:
        json.dump(
            results,
            file,
            indent=4,
            ensure_ascii=False,
        )

    logger.info("Validation results saved: %s", VALIDATION_FILE)


# ============================================================
# SUMMARY
# ============================================================

def print_summary(results: list[dict]) -> None:
    """Print a summary of PDF validation."""

    total = len(results)

    valid = sum(
        result["is_valid"] for result in results
    )

    invalid = total - valid

    readable = sum(
        result["has_extractable_text"] for result in results
    )

    duplicates = sum(
        result["is_duplicate"] for result in results
    )

    print("\n========== PDF VALIDATION SUMMARY ==========")
    print(f"Total PDF files       : {total}")
    print(f"Valid PDF files       : {valid}")
    print(f"Invalid PDF files     : {invalid}")
    print(f"PDFs with text        : {readable}")
    print(f"PDFs without text     : {total - readable}")
    print(f"Duplicate files       : {duplicates}")
    print("============================================\n")


# ============================================================
# EXECUTION
# ============================================================

if __name__ == "__main__":
    results = validate_reports()

    save_validation_results(results)

    print_summary(results)
