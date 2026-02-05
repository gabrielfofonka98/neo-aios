"""Action mapping and normalization.

This module provides utilities for mapping user operations and commands
to normalized action names used by the scope enforcement system.

Example:
    >>> from aios.scope.actions import action_mapper
    >>> action_mapper.map("git push origin main")
    'git_push'
    >>> action_mapper.get_action_for_command("gh pr create")
    'create_pr'
"""

from typing import Final


class ActionMapper:
    """Maps operations to normalized action names.

    This class normalizes various operation formats (user input, commands,
    tool names) to consistent action identifiers used by ScopeEnforcer.

    Attributes:
        OPERATION_MAP: Mapping from operation patterns to normalized actions.
    """

    OPERATION_MAP: Final[dict[str, str]] = {
        # Git operations
        "git push": "git_push",
        "git_push": "git_push",
        "push": "git_push",
        # PR operations
        "gh pr create": "create_pr",
        "create_pr": "create_pr",
        "create pr": "create_pr",
        # Deploy operations
        "deploy": "deploy_production",
        "vercel deploy": "deploy_production",
        "deploy --prod": "deploy_production",
        # Database operations
        "create table": "execute_ddl",
        "alter table": "execute_ddl",
        "drop table": "execute_ddl",
        "execute_ddl": "execute_ddl",
        # Security operations
        "security audit": "security_audit",
        "security_audit": "security_audit",
        "scan security": "security_audit",
        # Code operations
        "write_code": "write_code",
        "write code": "write_code",
        "implement": "write_code",
        # Review operations
        "code_review": "code_review",
        "review code": "code_review",
        "review": "code_review",
    }

    def map(self, operation: str) -> str:
        """Map an operation to its normalized action name.

        Args:
            operation: The operation string to normalize.

        Returns:
            Normalized action name, or the original operation if no mapping found.
        """
        normalized = operation.lower().strip()

        # Direct match
        if normalized in self.OPERATION_MAP:
            return self.OPERATION_MAP[normalized]

        # Partial match
        for pattern, action in self.OPERATION_MAP.items():
            if pattern in normalized:
                return action

        # Return original if no mapping found
        return normalized

    def get_action_for_command(self, command: str) -> str | None:
        """Get action name for a bash command.

        Args:
            command: The bash command to analyze.

        Returns:
            Normalized action name if recognized, None otherwise.
        """
        command_lower = command.lower()

        if "git push" in command_lower:
            return "git_push"
        if "gh pr create" in command_lower:
            return "create_pr"
        if any(
            kw in command_lower for kw in ["create table", "alter table", "drop table"]
        ):
            return "execute_ddl"
        if "vercel" in command_lower and (
            "deploy" in command_lower or "--prod" in command_lower
        ):
            return "deploy_production"

        return None


# Global instance
action_mapper = ActionMapper()
