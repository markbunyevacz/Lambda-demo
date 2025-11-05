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
from typing import Optional

from sqlalchemy.orm import Session


logger = logging.getLogger(__name__)


class FileHandler:
    """Handles file operations like hashing and duplicate checks."""

    CHUNK_SIZE = 4 * 1024  # 4 KiB: balance sys-call overhead and memory

    def __init__(self, db_session: Session):
        self.db_session = db_session

    def calculate_file_hash(self, pdf_path: Path) -> Optional[str]:
        """
        Calculate SHA-256 hash for the file.
        
        The implementation streams the file in fixed-size chunks so
        memory consumption stays constant even for 300 MB+ PDFs.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            SHA-256 hex digest string, or None if error occurs
        """
        hasher = hashlib.sha256()
        try:
            with open(pdf_path, "rb") as f:
                for chunk in iter(lambda: f.read(self.CHUNK_SIZE), b""):
                    hasher.update(chunk)
            return hasher.hexdigest()
        except FileNotFoundError:
            logger.error(f"File not found during hashing: {pdf_path}")
            return None
        except Exception as exc:
            logger.error(f"Error calculating hash for {pdf_path}: {exc}")
            return None

    def is_duplicate(self, file_hash: str) -> bool:
        """
        Check if file hash exists in processed_file_logs table.
        
        Args:
            file_hash: SHA-256 hash of the file
            
        Returns:
            True if file has been processed before, False otherwise
        """
        if not file_hash:
            return False
            
        try:
            from app.models.processed_file_log import ProcessedFileLog
            existing = self.db_session.query(ProcessedFileLog).filter(
                ProcessedFileLog.file_hash == file_hash
            ).first()
            return existing is not None
        except Exception as exc:
            logger.error(f"Error checking duplicate for hash {file_hash[:10]}...: {exc}")
            return False

    def add_to_log(self, file_hash: str, content_hash: str, filename: str):
        """
        Add processed file to the log.
        
        Args:
            file_hash: SHA-256 hash of the file
            content_hash: Hash of the extracted content
            filename: Original filename
        """
        try:
            from app.models.processed_file_log import ProcessedFileLog
            log_entry = ProcessedFileLog(
                file_hash=file_hash,
                content_hash=content_hash,
                source_filename=filename
            )
            self.db_session.add(log_entry)
            self.db_session.commit()
            logger.info(f"Added file to processed log: {filename}")
        except Exception as exc:
            logger.error(f"Error adding to log: {exc}")
            self.db_session.rollback()   