import logging
from pathlib import Path
from httpx import AsyncClient, ClientError

logger = logging.getLogger(__name__)


# PERMANENT FIX: Use absolute path from project root
PROJECT_ROOT = Path(__file__).resolve().parents[3]  # Go up to Lambda/ root
PDF_STORAGE_DIR = PROJECT_ROOT / "src" / "downloads" / "rockwool_datasheets"
DEBUG_FILE_PATH = PROJECT_ROOT / "debug_termekadatlapok.html"

# Ensure directory exists
PDF_STORAGE_DIR.mkdir(parents=True, exist_ok=True)
