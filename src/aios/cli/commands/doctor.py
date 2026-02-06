"""Doctor commands for NEO-AIOS CLI."""

import click
from rich.console import Console
from rich.table import Table

from aios.healthcheck.doctor import DoctorEngine
from aios.healthcheck.fixes import GitRepoFix
from aios.healthcheck.fixes import HooksPermissionFix
from aios.healthcheck.fixes import PythonDepsFix
from aios.healthcheck.models import HealthStatus

console = Console()


def _create_doctor() -> DoctorEngine:
    """Create DoctorEngine with registered fixes."""
    doctor = DoctorEngine()
    doctor.register_fix("git_repo", GitRepoFix())
    doctor.register_fix("hooks_active", HooksPermissionFix())
    doctor.register_fix("python_deps", PythonDepsFix())
    return doctor


def _status_icon(status: HealthStatus) -> str:
    """Get icon for health status."""
    icons: dict[HealthStatus, str] = {
        HealthStatus.HEALTHY: "[green]✓[/green]",
        HealthStatus.DEGRADED: "[yellow]⚠[/yellow]",
        HealthStatus.UNHEALTHY: "[red]✗[/red]",
        HealthStatus.UNKNOWN: "[dim]?[/dim]",
    }
    return icons.get(status, "?")


@click.group(name="doctor")
def doctor_group() -> None:
    """Health check and auto-fix system."""


@doctor_group.command(name="run")
@click.option("--fix", is_flag=True, help="Auto-fix issues when possible.")
def doctor_run(fix: bool) -> None:
    """Run all health checks."""
    doctor = _create_doctor()
    result = doctor.run(auto_fix=fix)

    table = Table(title="AIOS Doctor Report")
    table.add_column("Status", width=6)
    table.add_column("Check", min_width=20)
    table.add_column("Message")

    for check in result.check_results:
        icon = _status_icon(check.status)
        fixed = " [green](fixed)[/green]" if check.name in result.fixes_applied else ""
        table.add_row(icon, check.name, (check.message or "") + fixed)

    console.print(table)
    console.print(f"\n{result.summary}")

    if result.fixes_failed:
        console.print(
            f"[red]Failed to fix: {', '.join(result.fixes_failed)}[/red]"
        )


@doctor_group.command(name="list")
def doctor_list() -> None:
    """List all available checks."""
    doctor = _create_doctor()
    checks = doctor.list_checks()

    console.print("[bold]Available checks:[/bold]")
    for name in checks:
        console.print(f"  • {name}")
    console.print(f"\nTotal: {len(checks)} checks")
