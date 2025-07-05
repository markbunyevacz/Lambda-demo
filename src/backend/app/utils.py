"""
Project-wide utility functions.
"""
import os
from pathlib import Path


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