"""Backward-compatible launcher.

Prefer running ``python main.py`` for the documented project entry point.
"""

from main import main


if __name__ == "__main__":
    main()
