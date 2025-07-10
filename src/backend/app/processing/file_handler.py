"""
File Handler Service for the PDF Processing Pipeline
-----------------------------------------------------
Responsibilities:
- Calculating unique, content-based hashes for files.
- Checking for duplicates against the database to prevent re-processing.
"""
import hashlib
from pathlib import Path
import logging

from sqlalchemy.orm import Session
from app.models.processed_file_log import ProcessedFileLog

logger = logging.getLogger(__name__)

class FileHandler:
    """Handles file operations like hashing and duplicate checking."""

    def __init__(self, db_session: Session):
        self.db_session = db_session
        self.processed_hashes = self._load_processed_hashes()

    def _load_processed_hashes(self) -> set:
        """Loads all previously processed file hashes from the database."""
        try:
            return {log.file_hash for log in self.db_session.query(ProcessedFileLog.file_hash).all()}
        except Exception as e:
            logger.error(f"Could not load processed file hashes from database: {e}")
            return set()

    def is_duplicate(self, file_hash: str) -> bool:
        """Checks if a file hash has already been processed."""
        return file_hash in self.processed_hashes

    def calculate_file_hash(self, file_path: Path) -> str:
        """
        Calculates a SHA256 hash of the file's content in a memory-efficient way.
        Reads the file in chunks to avoid loading the entire file into memory.
        """
        hasher = hashlib.sha256()
        try:
            with open(file_path, "rb") as f:
                while chunk := f.read(65536):  # Read in 64k chunks
                    hasher.update(chunk)
            return hasher.hexdigest()
        except FileNotFoundError:
            logger.error(f"File not found during hash calculation: {file_path}")
            return ""
        except Exception as e:
            logger.error(f"Error calculating hash for {file_path}: {e}")
            return ""

    def add_hash_to_log(self, file_hash: str):
        """Adds a new hash to the in-memory set of processed files."""
        self.processed_hashes.add(file_hash) 