"""
Standalone Deduplication Manager for the PDF Processing Pipeline.
"""
import argparse
import hashlib
import sys
from pathlib import Path

# Add project root to path BEFORE attempting to import project modules
# This helps resolve module import issues when run as a standalone script.
try:
    project_root = Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(project_root))
except IndexError:
    # Handle cases where the script is not in the expected directory structure
    raise RuntimeError(
        "Cannot determine project root. "
        "Ensure script is in a subdirectory of the project."
    )

from sqlalchemy.orm import Session
from src.backend.app.database import SessionLocal
from src.backend.app.models.processed_file_log import ProcessedFileLog


def calculate_file_hash(file_path: Path) -> str:
    """Calculates the SHA256 hash of a file."""
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            sha256.update(chunk)
    return sha256.hexdigest()


def get_existing_hashes(db_session: Session) -> set[str]:
    """Retrieves all existing file hashes from the database."""
    all_logs = db_session.query(ProcessedFileLog.file_hash).all()
    return {log.file_hash for log in all_logs}


def check_new_files(db_session: Session, directory: Path):
    """Checks a directory for new files and prints their paths."""
    if not directory.is_dir():
        print(f"Error: Directory not found at {directory}", file=sys.stderr)
        sys.exit(1)

    existing_hashes = get_existing_hashes(db_session)
    pdf_files = list(directory.glob("*.pdf"))

    for pdf_path in pdf_files:
        file_hash = calculate_file_hash(pdf_path)
        if file_hash not in existing_hashes:
            print(str(pdf_path))  # Print the full path of unique files


def add_new_file(db_session: Session, file_path: Path):
    """Adds a new file's hash to the database log."""
    if not file_path.is_file():
        print(f"Error: File not found at {file_path}", file=sys.stderr)
        sys.exit(1)

    file_hash = calculate_file_hash(file_path)
    exists = (
        db_session.query(ProcessedFileLog)
        .filter_by(file_hash=file_hash)
        .first()
    )
    if not exists:
        new_log = ProcessedFileLog(
            file_hash=file_hash,
            content_hash=file_hash,  # Placeholder for content hash
            source_filename=file_path.name,
        )
        db_session.add(new_log)
        db_session.commit()
        print(
            f"Successfully added {file_path.name} "
            f"to the database log."
        )
    else:
        print(f"Warning: {file_path.name} already exists in the log.")


def main():
    parser = argparse.ArgumentParser(description="Manage PDF deduplication log.")
    parser.add_argument(
        "--check", metavar="DIR", help="Check a directory for new PDFs."
    )
    parser.add_argument(
        "--add", metavar="FILE", help="Add a PDF's hash to the database log."
    )
    args = parser.parse_args()

    db_session: Session = SessionLocal()
    try:
        if args.check:
            check_new_files(db_session, Path(args.check))
        elif args.add:
            add_new_file(db_session, Path(args.add))
        else:
            parser.print_help()
    finally:
        db_session.close()


if __name__ == "__main__":
    main() 