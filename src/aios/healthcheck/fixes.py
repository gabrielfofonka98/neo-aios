"""Auto-fix implementations for health checks."""

from __future__ import annotations

import os
import stat
import subprocess
from pathlib import Path
from typing import Protocol


class Fix(Protocol):
    """Protocol for auto-fixes."""

    @property
    def name(self) -> str: ...

    @property
    def description(self) -> str: ...

    def can_fix(self) -> bool: ...

    def apply(self) -> None: ...


class GitRepoFix:
    """Fix missing git repository."""

    @property
    def name(self) -> str:
        return "git_repo"

    @property
    def description(self) -> str:
        return "Initialize git repository"

    def can_fix(self) -> bool:
        return not Path(".git").exists()

    def apply(self) -> None:
        subprocess.run(["git", "init"], check=True, capture_output=True)


class HooksPermissionFix:
    """Fix hook file permissions."""

    @property
    def name(self) -> str:
        return "hooks_permission"

    @property
    def description(self) -> str:
        return "Make hook files executable"

    def can_fix(self) -> bool:
        hooks_dir = Path(".claude/hooks")
        if not hooks_dir.exists():
            return False
        return any(not os.access(hook, os.X_OK) for hook in hooks_dir.glob("*.py"))

    def apply(self) -> None:
        hooks_dir = Path(".claude/hooks")
        for hook in hooks_dir.glob("*.py"):
            current = hook.stat().st_mode
            hook.chmod(current | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)


class PythonDepsFix:
    """Fix missing Python dependencies."""

    @property
    def name(self) -> str:
        return "python_deps"

    @property
    def description(self) -> str:
        return "Sync Python dependencies with uv"

    def can_fix(self) -> bool:
        try:
            subprocess.run(["uv", "--version"], check=True, capture_output=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False

    def apply(self) -> None:
        subprocess.run(["uv", "sync"], check=True, capture_output=True)
