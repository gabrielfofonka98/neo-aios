"""Entry point for NEO-AIOS CLI.

This module serves as the main entry point for the `aios` command.
The entry point is configured in pyproject.toml:

    [project.scripts]
    aios = "aios.cli.main:cli"

Usage:
    aios --help
    aios version
    aios agent list
    aios scan quick
    aios health check
    aios gate precommit
"""

from aios.cli.app import cli

__all__ = ["cli"]

if __name__ == "__main__":
    cli()
