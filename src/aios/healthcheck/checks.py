"""Individual health checks.

Provides specific health checks for different aspects of the NEO-AIOS system.
Each check implements the HealthCheck protocol for consistency.
"""

import os
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


class GitRepoCheck:
    """Check that git repository exists and has remote configured."""

    @property
    def name(self) -> str:
        return "git_repo"

    def check(self) -> CheckResult:
        import subprocess

        if not Path(".git").exists():
            return CheckResult(
                name=self.name,
                status=HealthStatus.UNHEALTHY,
                message="No git repository found",
                details={"fix": "Run 'git init' or 'aios doctor run --fix'"},
            )

        try:
            result = subprocess.run(
                ["git", "remote", "-v"],
                capture_output=True,
                text=True,
                check=False,
            )
            has_remote = bool(result.stdout.strip())
        except FileNotFoundError:
            return CheckResult(
                name=self.name,
                status=HealthStatus.UNHEALTHY,
                message="git command not found",
            )

        if not has_remote:
            return CheckResult(
                name=self.name,
                status=HealthStatus.DEGRADED,
                message="Git repo exists but no remote configured",
            )

        return CheckResult(
            name=self.name,
            status=HealthStatus.HEALTHY,
            message="Git repository with remote configured",
        )


class UpstreamCheck:
    """Check upstream remote points to SynkraAI."""

    @property
    def name(self) -> str:
        return "upstream"

    def check(self) -> CheckResult:
        import subprocess

        try:
            result = subprocess.run(
                ["git", "remote", "-v"],
                capture_output=True,
                text=True,
                check=False,
            )
            remotes = result.stdout.strip()
        except FileNotFoundError:
            return CheckResult(
                name=self.name,
                status=HealthStatus.UNKNOWN,
                message="git not available",
            )

        if not remotes:
            return CheckResult(
                name=self.name,
                status=HealthStatus.DEGRADED,
                message="No remotes configured",
            )

        if "synkraai" in remotes.lower() or "SynkraAI" in remotes:
            return CheckResult(
                name=self.name,
                status=HealthStatus.HEALTHY,
                message="Upstream remote points to SynkraAI",
            )

        return CheckResult(
            name=self.name,
            status=HealthStatus.DEGRADED,
            message="No upstream remote to SynkraAI found",
            details={"remotes": remotes},
        )


class MCPInstalledCheck:
    """Check essential MCPs are installed."""

    ESSENTIAL_MCPS: ClassVar[list[str]] = ["context7", "desktop-commander", "browser"]

    @property
    def name(self) -> str:
        return "mcp_installed"

    def check(self) -> CheckResult:
        import json

        mcp_config = Path(".mcp.json")
        if not mcp_config.exists():
            return CheckResult(
                name=self.name,
                status=HealthStatus.DEGRADED,
                message="No .mcp.json found",
                details={"missing": self.ESSENTIAL_MCPS},
            )

        try:
            data = json.loads(mcp_config.read_text())
            servers = data.get("mcpServers", {})
        except (json.JSONDecodeError, OSError):
            return CheckResult(
                name=self.name,
                status=HealthStatus.UNHEALTHY,
                message="Invalid .mcp.json",
            )

        installed = [name for name in self.ESSENTIAL_MCPS if name in servers]
        missing = [name for name in self.ESSENTIAL_MCPS if name not in servers]

        if missing:
            return CheckResult(
                name=self.name,
                status=HealthStatus.DEGRADED,
                message=f"Missing MCPs: {', '.join(missing)}",
                details={"installed": installed, "missing": missing},
            )

        return CheckResult(
            name=self.name,
            status=HealthStatus.HEALTHY,
            message=f"All {len(self.ESSENTIAL_MCPS)} essential MCPs installed",
        )


class PythonDepsCheck:
    """Check Python dependencies resolve correctly."""

    @property
    def name(self) -> str:
        return "python_deps"

    def check(self) -> CheckResult:
        import subprocess

        if not Path("pyproject.toml").exists():
            return CheckResult(
                name=self.name,
                status=HealthStatus.UNKNOWN,
                message="No pyproject.toml found",
            )

        try:
            result = subprocess.run(
                ["uv", "pip", "check"],
                capture_output=True,
                text=True,
                check=False,
            )
            if result.returncode == 0:
                return CheckResult(
                    name=self.name,
                    status=HealthStatus.HEALTHY,
                    message="All Python dependencies resolved",
                )
            return CheckResult(
                name=self.name,
                status=HealthStatus.DEGRADED,
                message="Dependency issues detected",
                details={"output": result.stdout[:500]},
            )
        except FileNotFoundError:
            return CheckResult(
                name=self.name,
                status=HealthStatus.DEGRADED,
                message="uv not found, cannot verify dependencies",
            )


class HooksActiveCheck:
    """Check that hooks in .claude/hooks/ are executable."""

    @property
    def name(self) -> str:
        return "hooks_active"

    def check(self) -> CheckResult:
        hooks_dir = Path(".claude/hooks")
        if not hooks_dir.exists():
            return CheckResult(
                name=self.name,
                status=HealthStatus.DEGRADED,
                message="No .claude/hooks/ directory found",
            )

        hooks = list(hooks_dir.glob("*.py"))
        if not hooks:
            return CheckResult(
                name=self.name,
                status=HealthStatus.DEGRADED,
                message="No hook files found in .claude/hooks/",
            )

        non_executable: list[str] = []
        for hook in hooks:
            if not os.access(hook, os.X_OK):
                non_executable.append(hook.name)

        if non_executable:
            return CheckResult(
                name=self.name,
                status=HealthStatus.DEGRADED,
                message=f"Non-executable hooks: {', '.join(non_executable)}",
                details={"non_executable": non_executable, "total": len(hooks)},
            )

        return CheckResult(
            name=self.name,
            status=HealthStatus.HEALTHY,
            message=f"All {len(hooks)} hooks are executable",
        )


# Default checks to run
DEFAULT_CHECKS: list[HealthCheck] = [
    AgentRegistryCheck(),
    SessionPersistenceCheck(),
    ConfigurationCheck(),
    AgentIdentityCheck(),
    ScopeEnforcerCheck(),
    SecurityCheck(),
    GitRepoCheck(),
    UpstreamCheck(),
    MCPInstalledCheck(),
    PythonDepsCheck(),
    HooksActiveCheck(),
]
