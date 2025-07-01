import asyncio
from typing import Dict, List, Optional
from httpx import AsyncClient, HTTPError
import logging
import re
from datetime import datetime
from pathlib import Path
import json

logger = logging.getLogger(__name__)


# PERMANENT FIX: Use absolute path from project root
PROJECT_ROOT = Path(__file__).resolve().parents[3]  # Go up to Lambda/ root
PDF_STORAGE_DIR = PROJECT_ROOT / "src" / "downloads" / "rockwool_datasheets"
DEBUG_FILE_PATH = PROJECT_ROOT / "debug_termekadatlapok.html"

# Ensure directory exists
PDF_STORAGE_DIR.mkdir(parents=True, exist_ok=True)
