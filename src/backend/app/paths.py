"""
Centralized Path Management for the Lambda.hu Project.

This module provides robust, absolute paths to key directories,
making scripts independent of the current working directory.
"""
from pathlib import Path

# The absolute path to the project's root directory (Lambda/)
# This is now robust, going up four levels from src/backend/app/paths.py
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent

# Path to the backend directory (src/backend/)
BACKEND_DIR = PROJECT_ROOT / "src" / "backend"

# Path to the general downloads directory (corrected path)
DOWNLOADS_DIR = BACKEND_DIR / "src" / "downloads"

# Specific path to the Rockwool datasheets
ROCKWOOL_DATASHEETS_DIR = DOWNLOADS_DIR / "rockwool_datasheets"

# Path for reports and analysis outputs
REPORTS_DIR = BACKEND_DIR 

# Ensure key directories exist
DOWNLOADS_DIR.mkdir(parents=True, exist_ok=True)
ROCKWOOL_DATASHEETS_DIR.mkdir(parents=True, exist_ok=True)
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

# Example usage:
# from app.paths import ROCKWOOL_DATASHEETS_DIR
# pdf_files = list(ROCKWOOL_DATASHEETS_DIR.glob("*.pdf")) 