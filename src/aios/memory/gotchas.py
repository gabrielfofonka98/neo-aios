"""Gotchas memory: tracks recurring issues and auto-promotes to rules."""

from __future__ import annotations

import contextlib
import hashlib
import json
import os
import tempfile
from datetime import datetime
from pathlib import Path

from pydantic import BaseModel
from pydantic import Field

DEFAULT_THRESHOLD = 3


class IssueRecord(BaseModel):
    """A tracked issue occurrence with count."""

    category: str
    description: str
    context: str | None = None
    count: int = 1
    first_seen: datetime = Field(default_factory=datetime.now)
    last_seen: datetime = Field(default_factory=datetime.now)


class Gotcha(BaseModel):
    """A confirmed gotcha promoted from a recurring issue."""

    category: str
    description: str
    context: str | None = None
    promoted_at: datetime = Field(default_factory=datetime.now)
    occurrence_count: int = 0


class _GotchasData(BaseModel):
    """Internal storage model for the gotchas JSON file."""

    issues: dict[str, IssueRecord] = Field(default_factory=dict)
    gotchas: dict[str, Gotcha] = Field(default_factory=dict)


class GotchasMemory:
    """Tracks recurring issues and auto-promotes to gotchas after threshold.

    Issues are keyed by a hash of category + description. When an issue
    reaches the threshold count, it is promoted to a gotcha and removed
    from the issues dict. The JSON file is the source of truth; a
    human-readable markdown file is kept in sync.
    """

    def __init__(
        self,
        storage_path: Path,
        threshold: int = DEFAULT_THRESHOLD,
    ) -> None:
        self._storage_path = storage_path
        self._md_path = storage_path.with_suffix(".md")
        self._threshold = threshold
        self._storage_path.parent.mkdir(parents=True, exist_ok=True)

    @property
    def storage_path(self) -> Path:
        """Path to the JSON storage file."""
        return self._storage_path

    @property
    def threshold(self) -> int:
        """Number of occurrences required for promotion."""
        return self._threshold

    def record_issue(
        self,
        category: str,
        description: str,
        context: str | None = None,
    ) -> None:
        """Record an issue occurrence. If count >= threshold, promote to gotcha."""
        data = self._load()
        key = self._issue_key(category, description)
        now = datetime.now()

        if key in data.issues:
            issue = data.issues[key]
            issue.count += 1
            issue.last_seen = now
            if context is not None:
                issue.context = context
        else:
            data.issues[key] = IssueRecord(
                category=category,
                description=description,
                context=context,
                first_seen=now,
                last_seen=now,
            )

        if data.issues[key].count >= self._threshold:
            self._promote_to_gotcha(data, key)

        self._save(data)
        self._sync_markdown(data)

    def get_gotchas(self, category: str | None = None) -> list[Gotcha]:
        """Get all confirmed gotchas, optionally filtered by category."""
        data = self._load()
        gotchas = list(data.gotchas.values())
        if category is not None:
            gotchas = [g for g in gotchas if g.category == category]
        return sorted(gotchas, key=lambda g: g.promoted_at)

    def get_issues(self) -> list[IssueRecord]:
        """Get all tracked but not yet promoted issues."""
        data = self._load()
        return sorted(
            data.issues.values(),
            key=lambda i: i.count,
            reverse=True,
        )

    def format_for_prompt(self, max_lines: int = 20) -> str:
        """Format gotchas for injection into agent context. Compact markdown."""
        gotchas = self.get_gotchas()
        if not gotchas:
            return ""

        lines: list[str] = ["## Known Gotchas", ""]
        for gotcha in gotchas:
            line = f"- **[{gotcha.category}]** {gotcha.description}"
            if gotcha.context:
                line += f" ({gotcha.context})"
            lines.append(line)
            if len(lines) >= max_lines:
                remaining = len(gotchas) - (len(lines) - 2)
                if remaining > 0:
                    lines.append(f"- ... and {remaining} more")
                break

        return "\n".join(lines)

    def _promote_to_gotcha(self, data: _GotchasData, issue_key: str) -> None:
        """Promote issue to gotcha when threshold reached."""
        issue = data.issues.pop(issue_key)
        data.gotchas[issue_key] = Gotcha(
            category=issue.category,
            description=issue.description,
            context=issue.context,
            promoted_at=datetime.now(),
            occurrence_count=issue.count,
        )

    def _sync_markdown(self, data: _GotchasData) -> None:
        """Write human-readable gotchas.md from data."""
        lines: list[str] = [
            "# Gotchas",
            "",
            f"_Auto-generated. {len(data.gotchas)} gotchas, "
            f"{len(data.issues)} tracked issues._",
            "",
        ]

        if data.gotchas:
            lines.append("## Confirmed Gotchas")
            lines.append("")
            for gotcha in sorted(data.gotchas.values(), key=lambda g: g.promoted_at):
                lines.append(f"### [{gotcha.category}] {gotcha.description}")
                if gotcha.context:
                    lines.append(f"Context: {gotcha.context}")
                lines.append(
                    f"Occurrences: {gotcha.occurrence_count} | "
                    f"Promoted: {gotcha.promoted_at.isoformat()}"
                )
                lines.append("")

        if data.issues:
            lines.append("## Tracked Issues (not yet promoted)")
            lines.append("")
            for issue in sorted(
                data.issues.values(), key=lambda i: i.count, reverse=True
            ):
                lines.append(
                    f"- **[{issue.category}]** {issue.description} "
                    f"(count: {issue.count}/{self._threshold})"
                )
            lines.append("")

        content = "\n".join(lines)
        self._atomic_write(self._md_path, content)

    def _load(self) -> _GotchasData:
        """Load data from JSON file, or return empty data if not found."""
        if not self._storage_path.exists():
            return _GotchasData()
        try:
            raw = self._storage_path.read_text(encoding="utf-8")
            return _GotchasData.model_validate(json.loads(raw))
        except (json.JSONDecodeError, OSError, ValueError):
            return _GotchasData()

    def _save(self, data: _GotchasData) -> None:
        """Persist data to JSON file atomically."""
        content = data.model_dump_json(indent=2)
        self._atomic_write(self._storage_path, content)

    @staticmethod
    def _atomic_write(path: Path, content: str) -> None:
        """Write content to file atomically via temp file + rename."""
        path.parent.mkdir(parents=True, exist_ok=True)
        fd, tmp_name = tempfile.mkstemp(
            dir=str(path.parent),
            prefix=f".{path.name}.",
            suffix=".tmp",
        )
        tmp_path = Path(tmp_name)
        try:
            tmp_path.write_text(content, encoding="utf-8")
            tmp_path.replace(path)
        except BaseException:
            tmp_path.unlink(missing_ok=True)
            raise
        finally:
            with contextlib.suppress(OSError):
                os.close(fd)

    @staticmethod
    def _issue_key(category: str, description: str) -> str:
        """Generate a stable key for an issue from category + description."""
        raw = f"{category}::{description}"
        return hashlib.sha256(raw.encode()).hexdigest()[:16]
