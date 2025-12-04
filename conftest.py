"""
Pytest configuration file to ensure proper module imports.

This file ensures that the 'src' package can be imported by all tests
without needing to set PYTHONPATH manually.
"""

import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))
