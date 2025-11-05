#!/usr/bin/env python3
"""
File Handler Service
--------------------
Single-responsibility helper that takes care of *all* file system
operations used by the PDF pipeline – currently only hashing, but it is
ready to be extended with e.g. atomic move / cleanup utilities.
"""

import hashlib
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class FileHandler:
    """Encapsulates file-related helper methods."""

    CHUNK_SIZE = 4 * 1024  # 4 KiB: balance sys-call overhead and memory

    def calculate_file_hash(self, file_path: Path) -> str:
        """
        Return a SHA-256 hex digest for *file_path*.

        The implementation **streams** the file in fixed-size chunks so
        memory consumption stays constant even for 300 MB+ PDFs.
        """
        hasher = hashlib.sha256()
        try:
            with open(file_path, "rb") as f:
                # Read and update hash in chunks of 4K
                for chunk in iter(lambda: f.read(self.CHUNK_SIZE), b""):
                    hasher.update(chunk)
            return hasher.hexdigest()
        except FileNotFoundError:
            logger.error("File not found during hashing: %s", file_path)
            return ""
        except Exception as exc:
            logger.error("Error calculating hash for %s: %s", file_path, exc)
            return "" 