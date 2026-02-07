"""File evolution tracker: detects multi-agent conflicts on shared files."""

from __future__ import annotations

import contextlib
import json
import os
import tempfile
from datetime import datetime
from datetime import timedelta
from pathlib import Path
from typing import Literal

from pydantic import BaseModel
from pydantic import Field

# Paths that are always critical when modified by multiple agents
_CRITICAL_PREFIXES = (".claude/", "src/aios/")

_SEVERITY_ORDER: dict[str, int] = {
    "low": 0,
    "medium": 1,
    "high": 2,
    "critical": 3,
}


class FileModification(BaseModel):
    """A single file modification event."""

    file_path: str
    agent_id: str
    task_id: str | None = None
    timestamp: datetime = Field(default_factory=datetime.now)


class ConflictInfo(BaseModel):
    """Conflict report for a single file."""

    file_path: str
    agents: list[str]
    modifications: list[FileModification]
    severity: Literal["low", "medium", "high", "critical"]


class DriftReport(BaseModel):
    """Drift report for files modified by multiple agents in a time window."""

    file_path: str
    agents: list[str]
    first_modification: datetime
    last_modification: datetime
    total_modifications: int
    severity: Literal["low", "medium", "high", "critical"]


class _FileRecord(BaseModel):
    """Internal storage: all modifications for a single file path."""

    modifications: list[FileModification] = Field(default_factory=list)


class _EvolutionStore(BaseModel):
    """Internal top-level storage model."""

    files: dict[str, _FileRecord] = Field(default_factory=dict)


class FileEvolutionTracker:
    """Tracks file modifications per agent to detect conflicts.

    Storage is a single JSON file inside the provided directory.
    Each file path maps to a list of modification records.
    """

    def __init__(self, storage_dir: Path) -> None:
        self._storage_dir = storage_dir
        self._storage_dir.mkdir(parents=True, exist_ok=True)
        self._storage_file = self._storage_dir / "evolution.json"

    @property
    def storage_dir(self) -> Path:
        """Directory containing the evolution data."""
        return self._storage_dir

    def record_modification(
        self,
        file_path: str,
        agent_id: str,
        task_id: str | None = None,
    ) -> None:
        """Record that an agent modified a file."""
        data = self._load()
        mod = FileModification(
            file_path=file_path,
            agent_id=agent_id,
            task_id=task_id,
            timestamp=datetime.now(),
        )

        if file_path not in data.files:
            data.files[file_path] = _FileRecord()
        data.files[file_path].modifications.append(mod)

        self._save(data)

    def check_conflicts(self, file_path: str) -> list[ConflictInfo]:
        """Check if multiple agents have modified the same file recently.

        Returns a list with zero or one ConflictInfo. Returns empty list
        if only one agent has touched the file.
        """
        data = self._load()
        record = data.files.get(file_path)
        if record is None:
            return []

        agents = _unique_agents(record.modifications)
        if len(agents) < 2:
            return []

        severity = _compute_severity(file_path, agents, record.modifications)
        return [
            ConflictInfo(
                file_path=file_path,
                agents=agents,
                modifications=record.modifications,
                severity=severity,
            )
        ]

    def get_agent_files(self, agent_id: str) -> list[str]:
        """Get all files modified by a specific agent."""
        data = self._load()
        result: list[str] = []
        for fpath, record in data.files.items():
            if any(m.agent_id == agent_id for m in record.modifications):
                result.append(fpath)
        return sorted(result)

    def detect_drift(self, window_minutes: int = 30) -> list[DriftReport]:
        """Detect files modified by multiple agents within time window.

        Scans all tracked files and returns a DriftReport for each file
        that was modified by 2+ agents within the specified window.
        """
        data = self._load()
        cutoff = datetime.now() - timedelta(minutes=window_minutes)
        reports: list[DriftReport] = []

        for fpath, record in data.files.items():
            recent = [m for m in record.modifications if m.timestamp >= cutoff]
            if not recent:
                continue

            agents = _unique_agents(recent)
            if len(agents) < 2:
                continue

            timestamps = [m.timestamp for m in recent]
            severity = _compute_severity(fpath, agents, recent)

            reports.append(
                DriftReport(
                    file_path=fpath,
                    agents=agents,
                    first_modification=min(timestamps),
                    last_modification=max(timestamps),
                    total_modifications=len(recent),
                    severity=severity,
                )
            )

        reports.sort(key=lambda r: _SEVERITY_ORDER.get(r.severity, 0), reverse=True)
        return reports

    def cleanup(self, max_age_days: int = 7) -> int:
        """Remove entries older than max_age_days. Return count removed."""
        data = self._load()
        cutoff = datetime.now() - timedelta(days=max_age_days)
        removed = 0

        files_to_delete: list[str] = []
        for fpath, record in data.files.items():
            before = len(record.modifications)
            record.modifications = [
                m for m in record.modifications if m.timestamp >= cutoff
            ]
            removed += before - len(record.modifications)
            if not record.modifications:
                files_to_delete.append(fpath)

        for fpath in files_to_delete:
            del data.files[fpath]

        self._save(data)
        return removed

    def _load(self) -> _EvolutionStore:
        """Load data from JSON file."""
        if not self._storage_file.exists():
            return _EvolutionStore()
        try:
            raw = self._storage_file.read_text(encoding="utf-8")
            return _EvolutionStore.model_validate(json.loads(raw))
        except (json.JSONDecodeError, OSError, ValueError):
            return _EvolutionStore()

    def _save(self, data: _EvolutionStore) -> None:
        """Persist data atomically."""
        content = data.model_dump_json(indent=2)
        self._atomic_write(self._storage_file, content)

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


def _unique_agents(modifications: list[FileModification]) -> list[str]:
    """Extract unique agent IDs preserving first-seen order."""
    seen: set[str] = set()
    result: list[str] = []
    for m in modifications:
        if m.agent_id not in seen:
            seen.add(m.agent_id)
            result.append(m.agent_id)
    return result


def _compute_severity(
    file_path: str,
    agents: list[str],
    modifications: list[FileModification],
) -> Literal["low", "medium", "high", "critical"]:
    """Compute conflict severity.

    Rules:
    - Any agent + file in .claude/ or src/aios/ = critical
    - 3+ agents, same file = high
    - 2 agents, same file, <10min apart = medium
    - 2 agents, same file, >10min apart = low
    """
    # Critical: sensitive paths
    for prefix in _CRITICAL_PREFIXES:
        if file_path.startswith(prefix):
            return "critical"

    if len(agents) >= 3:
        return "high"

    # Medium vs Low: time proximity
    if len(agents) >= 2 and len(modifications) >= 2:
        timestamps = sorted(m.timestamp for m in modifications)
        # Check consecutive modification pairs for proximity
        for i in range(len(timestamps) - 1):
            gap = timestamps[i + 1] - timestamps[i]
            if gap < timedelta(minutes=10):
                return "medium"

    return "low"
