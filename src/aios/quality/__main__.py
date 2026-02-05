"""Entry point for running pre-commit checks as a module.

Usage:
    python -m aios.quality [files...]

If no files are provided, it will get staged files from git.
"""

import sys

from aios.quality.precommit import run_precommit_hook


def main() -> None:
    """Main entry point for pre-commit module."""
    # Get files from command line args (skip the module name)
    files = sys.argv[1:] if len(sys.argv) > 1 else None
    exit_code = run_precommit_hook(files)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
