"""
Project-wide utility functions.
"""
import os
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


def get_project_root() -> Path:
    """
    Get project root using multiple fallback strategies.
    Avoids IndexError and works in any environment.
    """
    # Strategy 1: Environment variable
    root_env = os.environ.get('PROJECT_ROOT')
    if root_env and Path(root_env).exists():
        return Path(root_env)

    # Strategy 2: Look for project markers
    markers = [
        '.git', 'pyproject.toml', 'requirements.txt', 'docker-compose.yml'
    ]
    current = Path(__file__).resolve().parent

    for parent in [current] + list(current.parents):
        for marker in markers:
            if (parent / marker).exists():
                return parent

    # Strategy 3: Fallback to a hardcoded assumption (less ideal)
    # This might be necessary if no markers are found in the container's path.
    # We go up from this utils file to the 'src/backend' level.
    try:
        return Path(__file__).resolve().parents[2]
    except IndexError:
        # Final fallback
        return Path.cwd()


def clean_utf8(text: str) -> str:
    """
    Cleans a string to ensure it's valid UTF-8.
    It handles improperly encoded characters by attempting to decode using
    common fallbacks and replacing errors if necessary.
    """
    if not isinstance(text, str):
        return text
    try:
        # Check if the text is already valid UTF-8
        text.encode('utf-8')
        return text
    except UnicodeEncodeError:
        logger.warning(f"Fixing UTF-8 encoding issue in text: {text[:50]}...")
        # Attempt to fix the string by decoding with a common fallback and re-encoding
        try:
            return text.encode('latin-1').decode('utf-8')
        except UnicodeError:
            # Final fallback: replace invalid characters
            return text.encode('utf-8', 'replace').decode('utf-8') 