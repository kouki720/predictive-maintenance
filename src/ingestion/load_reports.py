
from __future__ import annotations

from pathlib import Path
import gdown


# ============================================================
# CONFIGURATION
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

DRIVE_FOLDER_URL = (
    "https://drive.google.com/drive/folders/"
    "1hKo4r_UoUiydrez3pXBNl838TuXCCfcc"
)

STAGING_DIR = (
    PROJECT_ROOT
    / "datasets"
    / "staging"
    / "reports"
)


# ============================================================
# CHECK EXISTING REPORTS
# ============================================================

def get_existing_reports() -> list[Path]:
    """
    Return existing PDF reports in the staging directory.
    """

    if not STAGING_DIR.exists():
        return []

    return sorted(
        file_path
        for file_path in STAGING_DIR.rglob("*")
        if file_path.is_file()
        and file_path.suffix.lower() == ".pdf"
        and file_path.stat().st_size > 0
    )


# ============================================================
# DOWNLOAD REPORTS
# ============================================================

def download_reports() -> None:
    """
    Download PDF reports only when no existing PDF is found.
    Existing reports are preserved.
    """

    print("\n" + "=" * 60)
    print("PDF REPORTS ACQUISITION")
    print("=" * 60)

    STAGING_DIR.mkdir(parents=True, exist_ok=True)

    # Check whether reports already exist
    existing_reports = get_existing_reports()

    if existing_reports:
        print(
            f"{len(existing_reports)} existing PDF report(s) found."
        )
        print("Google Drive download skipped.")

        for report in existing_reports:
            print(f"Existing report: {report.name}")

        print("\nExisting reports will be preserved.")
        return

    print("No existing PDF reports found.")
    print("Starting Google Drive download...")

    downloaded_files = gdown.download_folder(
        url=DRIVE_FOLDER_URL,
        output=str(STAGING_DIR),
        quiet=False,
        use_cookies=False,
    )

    if not downloaded_files:
        raise RuntimeError(
            "Google Drive download returned no files."
        )

    # Verify downloaded reports
    reports = get_existing_reports()

    if not reports:
        raise RuntimeError(

        )

    print("\nPDF DOWNLOAD COMPLETED")
    print(f"Downloaded/available PDF reports: {len(reports)}")

    for report in reports:
        print(f"- {report.name}")


# ============================================================
# MAIN
# ============================================================

def main() -> None:
    download_reports()


if __name__ == "__main__":
    main()
