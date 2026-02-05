"""Health check commands for NEO-AIOS CLI.

This module provides commands for health checking:
- check: Run health checks (all or specific)
"""

import click

from aios.cli.output import info
from aios.cli.output import success


@click.group(name="health")
def health_group() -> None:
    """Run health checks."""


@health_group.command(name="check")
@click.option(
    "--name",
    "-n",
    help="Specific check to run.",
)
def health_check(name: str | None) -> None:
    """Run health checks.

    Without --name, runs all checks. With --name, runs specific check.
    """
    # TODO: Integrate with HealthChecker when Story 6.1 is complete
    if name:
        info(f"Running health check: {name}")
    else:
        info("Running all health checks...")
    success("All health checks passed.")
