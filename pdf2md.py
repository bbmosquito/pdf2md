#!/usr/bin/env python3
"""
PDF2MD - Main entry point.

Run this script to start the PDF2MD command-line tool.
"""

import sys
from pathlib import Path

# Add src directory to path
src_dir = Path(__file__).parent / "src"
sys.path.insert(0, str(src_dir))

# Import CLI module directly
if __name__ == "__main__":
    import src.cli as cli_module
    cli_module.main_entry()
