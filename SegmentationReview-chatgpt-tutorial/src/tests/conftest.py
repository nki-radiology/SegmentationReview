"""Shared pytest fixtures and configuration."""

import sys
from pathlib import Path

# Make the src/ package importable without installing
sys.path.insert(0, str(Path(__file__).parent))
