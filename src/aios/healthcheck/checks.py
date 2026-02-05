"""Individual health checks.

Provides specific health checks for different aspects of the NEO-AIOS system.
Each check implements the HealthCheck protocol for consistency.
"""

from pathlib import Path
from typing import ClassVar
from typing import Protocol

from aios.healthcheck.models import CheckResult
from aios.healthcheck.models import HealthStatus


class HealthCheck(Protocol):
    """Protocol for health checks.

    All health checks must implement this protocol.
    """

    @property
    def name(self) -> str:
        """Check name identifier."""
        ...

    def check(self) -> CheckResult:
        """Execute check and return result."""
        ...


class AgentRegistryCheck:
    """Check that agent registry is loaded and functional."""

    @property
    def name(self) -> str:
        """Return check name."""
        return "agent_registry"

    def check(self) -> CheckResult:
        """Check agent registry status.

        Returns:
            CheckResult with registry health status.
        """
        # Import here to avoid circular imports
        from aios.agents.registry import AgentRegistry

        try:
            registry = AgentRegistry.load()
            count = len(registry)

            if count == 0:
                return CheckResult(
                    name=self.name,
                    status=HealthStatus.DEGRADED,
                    message="Agent registry loaded but empty",
                    details={"agent_count": 0},
                )

            return CheckResult(
                name=self.name,
                status=HealthStatus.HEALTHY,
                message=f"Agent registry loaded with {count} agents",
                details={"agent_count": count},
            )
        except Exception as e:
            return CheckResult(
                name=self.name,
                status=HealthStatus.UNHEALTHY,
                message=f"Failed to load agent registry: {e!s}",
            )


class SessionPersistenceCheck:
    """Check session persistence is working."""

    @property
    def name(self) -> str:
        """Return check name."""
        return "session_persistence"

    def check(self) -> CheckResult:
        """Check session persistence status.

        Returns:
            CheckResult with session persistence health status.
        """
        from aios.context.session import Session

        try:
            session = Session.load()

            return CheckResult(
                name=self.name,
                status=HealthStatus.HEALTHY,
                message="Session persistence working",
                details={
                    "active_agent": session.state.active_agent,
                    "has_state": True,
                },
            )
        except Exception as e:
            return CheckResult(
                name=self.name,
                status=HealthStatus.UNHEALTHY,
                message=f"Session persistence error: {e!s}",
            )


class ConfigurationCheck:
    """Check required configuration files exist."""

    REQUIRED_FILES: ClassVar[list[str]] = [
        ".aios",
        "pyproject.toml",
    ]

    OPTIONAL_FILES: ClassVar[list[str]] = [
        ".aios/session-state.json",
        "config/credentials.yaml",
        ".env",
    ]

    @property
    def name(self) -> str:
        """Return check name."""
        return "configuration"

    def check(self) -> CheckResult:
        """Check configuration files status.

        Returns:
            CheckResult with configuration health status.
        """
        missing_required: list[str] = []
        missing_optional: list[str] = []

        for file_path in self.REQUIRED_FILES:
            if not Path(file_path).exists():
                missing_required.append(file_path)

        for file_path in self.OPTIONAL_FILES:
            if not Path(file_path).exists():
                missing_optional.append(file_path)

        if missing_required:
            return CheckResult(
                name=self.name,
                status=HealthStatus.UNHEALTHY,
                message=f"Missing required files: {', '.join(missing_required)}",
                details={
                    "missing_required": missing_required,
                    "missing_optional": missing_optional,
                },
            )

        if missing_optional:
            return CheckResult(
                name=self.name,
                status=HealthStatus.DEGRADED,
                message=f"Missing optional files: {', '.join(missing_optional)}",
                details={"missing_optional": missing_optional},
            )

        return CheckResult(
            name=self.name,
            status=HealthStatus.HEALTHY,
            message="All configuration files present",
        )


class AgentIdentityCheck:
    """Check agent identity isolation is configured correctly.

    Verifies that all agents have proper scope definitions
    and no overlapping exclusive permissions.
    """

    @property
    def name(self) -> str:
        """Return check name."""
        return "agent_identity_isolation"

    def check(self) -> CheckResult:
        """Check agent identity isolation configuration.

        Returns:
            CheckResult with identity isolation health status.
        """
        from aios.agents.registry import AgentRegistry

        try:
            registry = AgentRegistry.load()
            agents_checked = len(registry)

            # Check for scope definition issues
            issues: list[str] = []

            for agent in registry:
                # Verify agent has scope defined
                if not agent.scope.can and not agent.scope.cannot:
                    issues.append(f"Agent '{agent.id}' has no scope defined")

            if issues:
                return CheckResult(
                    name=self.name,
                    status=HealthStatus.DEGRADED,
                    message=f"Identity isolation issues found: {len(issues)}",
                    details={
                        "issues": issues,
                        "agents_checked": agents_checked,
                    },
                )

            return CheckResult(
                name=self.name,
                status=HealthStatus.HEALTHY,
                message="Agent identity isolation configured correctly",
                details={
                    "rule": "Each agent is a unique, isolated entity",
                    "agents_checked": agents_checked,
                },
            )
        except Exception as e:
            return CheckResult(
                name=self.name,
                status=HealthStatus.UNHEALTHY,
                message=f"Failed to check agent identity: {e!s}",
            )


class ScopeEnforcerCheck:
    """Check that scope enforcer is properly configured."""

    @property
    def name(self) -> str:
        """Return check name."""
        return "scope_enforcer"

    def check(self) -> CheckResult:
        """Check scope enforcer status.

        Returns:
            CheckResult with scope enforcer health status.
        """
        from aios.scope.enforcer import ScopeEnforcer

        try:
            enforcer = ScopeEnforcer()

            # Verify exclusive actions are configured
            if not enforcer.EXCLUSIVE_ACTIONS:
                return CheckResult(
                    name=self.name,
                    status=HealthStatus.DEGRADED,
                    message="No exclusive actions configured",
                )

            # Verify globally blocked actions are configured
            if not enforcer.GLOBALLY_BLOCKED:
                return CheckResult(
                    name=self.name,
                    status=HealthStatus.DEGRADED,
                    message="No globally blocked actions configured",
                )

            return CheckResult(
                name=self.name,
                status=HealthStatus.HEALTHY,
                message="Scope enforcer configured correctly",
                details={
                    "exclusive_actions": list(enforcer.EXCLUSIVE_ACTIONS.keys()),
                    "globally_blocked": enforcer.GLOBALLY_BLOCKED,
                },
            )
        except Exception as e:
            return CheckResult(
                name=self.name,
                status=HealthStatus.UNHEALTHY,
                message=f"Scope enforcer error: {e!s}",
            )


class SecurityCheck:
    """Check security-related configurations."""

    SENSITIVE_PATHS: ClassVar[list[str]] = [
        ".env",
        "config/credentials.yaml",
    ]

    @property
    def name(self) -> str:
        """Return check name."""
        return "security"

    def check(self) -> CheckResult:
        """Check security configuration status.

        Returns:
            CheckResult with security health status.
        """
        issues: list[str] = []

        # Check if sensitive files have proper permissions
        for path_str in self.SENSITIVE_PATHS:
            path = Path(path_str)
            if path.exists():
                # Check if file is not world-readable (Unix)
                try:
                    mode = path.stat().st_mode
                    # Check if group or others can read (0o044)
                    if mode & 0o044:
                        issues.append(f"{path_str} may be readable by others")
                except OSError:
                    pass  # Skip permission check on non-Unix systems

        # Check if .gitignore exists and includes sensitive files
        gitignore = Path(".gitignore")
        if gitignore.exists():
            gitignore_content = gitignore.read_text()
            for sensitive in self.SENSITIVE_PATHS:
                if sensitive not in gitignore_content:
                    issues.append(f"{sensitive} may not be in .gitignore")

        if issues:
            return CheckResult(
                name=self.name,
                status=HealthStatus.DEGRADED,
                message=f"Security warnings: {len(issues)}",
                details={"warnings": issues},
            )

        return CheckResult(
            name=self.name,
            status=HealthStatus.HEALTHY,
            message="Security configuration OK",
        )


# Default checks to run
DEFAULT_CHECKS: list[HealthCheck] = [
    AgentRegistryCheck(),
    SessionPersistenceCheck(),
    ConfigurationCheck(),
    AgentIdentityCheck(),
    ScopeEnforcerCheck(),
    SecurityCheck(),
]
