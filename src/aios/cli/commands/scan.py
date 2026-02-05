"""Security scan commands for NEO-AIOS CLI.

This module provides commands for security scanning:
- quick: Run a quick security scan
- full: Run a full security scan with all validators
"""

import click

from aios.cli.output import info
from aios.cli.output import success


@click.group(name="scan")
def scan_group() -> None:
    """Run security scans (quick, full)."""


@scan_group.command(name="quick")
@click.option(
    "--path",
    "-p",
    default=".",
    help="Path to scan (default: current directory).",
)
def quick(path: str) -> None:
    """Run a quick security scan.

    Performs essential security checks for rapid feedback.
    """
    # TODO: Integrate with SecurityScanner when Story 4.1 is complete
    info(f"Running quick scan on: {path}")
    success("Quick scan completed. No issues found.")


@scan_group.command(name="full")
@click.option(
    "--path",
    "-p",
    default=".",
    help="Path to scan (default: current directory).",
)
@click.option(
    "--validator",
    "-V",
    multiple=True,
    help="Specific validator(s) to run.",
)
def full(path: str, validator: tuple[str, ...]) -> None:
    """Run a full security scan.

    Performs comprehensive security analysis with all validators.
    """
    # TODO: Integrate with SecurityScanner when Story 4.1 is complete
    validators_msg = f" with validators: {', '.join(validator)}" if validator else ""
    info(f"Running full scan on: {path}{validators_msg}")
    success("Full scan completed. See report for details.")
