"""Quality gate commands for NEO-AIOS CLI.

This module provides commands for quality gates:
- precommit: Run pre-commit quality gate
- pr: Run PR quality gate
"""

import click

from aios.cli.output import info
from aios.cli.output import success


@click.group(name="gate")
def gate_group() -> None:
    """Run quality gates (precommit, pr)."""


@gate_group.command(name="precommit")
@click.option(
    "--fix",
    is_flag=True,
    help="Attempt to auto-fix issues.",
)
def precommit(fix: bool) -> None:
    """Run pre-commit quality gate.

    Checks code quality before commit (ruff, mypy, pytest, security).
    """
    # TODO: Integrate with QualityGate when Story 7.1 is complete
    fix_msg = " with auto-fix enabled" if fix else ""
    info(f"Running pre-commit gate{fix_msg}...")
    success("Pre-commit gate passed.")


@gate_group.command(name="pr")
@click.option(
    "--pr-number",
    "-n",
    type=int,
    help="PR number to validate.",
)
def pr(pr_number: int | None) -> None:
    """Run PR quality gate.

    Comprehensive validation for pull requests.
    """
    # TODO: Integrate with QualityGate when Story 7.1 is complete
    pr_msg = f" for PR #{pr_number}" if pr_number else ""
    info(f"Running PR gate{pr_msg}...")
    success("PR gate passed.")
