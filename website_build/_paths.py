"""_paths
Absolute paths to avoid ambiguity when building the website.
"""
import os
from pathlib import Path

LOCATION_OF_THIS_FILE = Path(os.path.abspath(os.path.dirname(__file__)))

# Path to the root of the TLOModel-profiling repository
GIT_ROOT = (LOCATION_OF_THIS_FILE / "..").resolve()

# Default name for the directory to build the website in
DEFAULT_BUILD_DIR = (LOCATION_OF_THIS_FILE / ".." / "build").resolve()

# Source for website files, including templates into which tables/images are to be inserted
SRC_DIR = (GIT_ROOT / "source").resolve()
