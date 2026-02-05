"""CLI module for NEO-AIOS.

This module provides the command-line interface for interacting with
the NEO-AIOS agent system.
"""

from aios.cli.app import create_app
from aios.cli.output import console
from aios.cli.output import error
from aios.cli.output import info
from aios.cli.output import success
from aios.cli.output import warning

__all__ = [
    "console",
    "create_app",
    "error",
    "info",
    "success",
    "warning",
]
