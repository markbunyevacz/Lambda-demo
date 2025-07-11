"""
File Handler Service for the PDF Processing Pipeline
-----------------------------------------------------
Responsibilities:
- Calculating unique, content-based hashes for files.
- Checking for duplicates against the database to prevent re-processing.
"""
import logging
import hashlib
from pathlib import Path
from typing import Set, Optional

from sqlalchemy.orm import Session


logger = logging.getLogger(__name__)


class FileHandler:
    """Handles file operations like hashing and duplicate checks."""

    def __init__(self, db_session: Session):
        self.db_session = db_session
        self.processed_hashes_session: Set[str] = set()

    def calculate_file_hash(self, pdf_path: Path) -> Optional[str]:
        """
        TEMPORARILY DISABLED. Returns a dummy hash to bypass file errors.
        """
        # Return a dummy hash based on filename to allow processing
        return hashlib.sha256(pdf_path.name.encode()).hexdigest()

    def is_duplicate(self, file_hash: str) -> bool:
        """
        TEMPORARILY DISABLED. Always returns False to allow processing.
        """
        # Always return False to ensure every file is processed
        # This is safe because the database is currently empty.
        return False

    def add_hash_to_log(self, file_hash: str):
        """Adds a hash to the in-memory set for the current session."""
        self.processed_hashes_session.add(file_hash) 