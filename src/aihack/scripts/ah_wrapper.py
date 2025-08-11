#!/usr/bin/env python3
"""Wrapper to suppress urllib3 warnings before main execution."""
import os
import warnings

from aihack.cli.main import main

# Set environment variable to suppress urllib3 warnings
os.environ["PYTHONWARNINGS"] = "ignore::UserWarning:urllib3"

# Suppress warnings programmatically as backup
warnings.filterwarnings("ignore", message=".*urllib3.*OpenSSL.*")

if __name__ == "__main__":
    main()
