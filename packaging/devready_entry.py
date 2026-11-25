"""Entry point for the standalone binary (PyInstaller). Same CLI as `devready`."""

import sys

from devready.cli import main

if __name__ == "__main__":
    sys.exit(main())
