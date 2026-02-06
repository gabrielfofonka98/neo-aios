"""Persistent memory store."""

from __future__ import annotations

import json
import uuid
from datetime import datetime
from datetime import timedelta
from pathlib import Path

from aios.context.memory_models import Memory
from aios.context.memory_models import MemoryDigest
from aios.context.memory_models import MemoryPriority
from aios.context.memory_models import MemoryType

DEFAULT_MEMORY_DIR = Path(".aios/memories")
PRUNE_DAYS = 30


class MemoryStore:
    """JSON-based persistent memory store."""

    def __init__(self, memory_dir: Path | None = None) -> None:
        self._memory_dir = memory_dir or DEFAULT_MEMORY_DIR
        self._memory_dir.mkdir(parents=True, exist_ok=True)

    @property
    def memory_dir(self) -> Path:
        return self._memory_dir

    def add(
        self,
        content: str,
        memory_type: MemoryType,
        priority: MemoryPriority = MemoryPriority.MEDIUM,
        tags: list[str] | None = None,
        agent_id: str | None = None,
        project: str | None = None,
        epic: str | None = None,
    ) -> Memory:
        """Add a new memory."""
        memory = Memory(
            id=str(uuid.uuid4())[:8],
            content=content,
            memory_type=memory_type,
            priority=priority,
            tags=tags or [],
            agent_id=agent_id,
            project=project,
            epic=epic,
        )
        self._save_memory(memory)
        return memory

    def list_all(self) -> list[Memory]:
        """List all stored memories."""
        memories: list[Memory] = []
        for file in self._memory_dir.glob("*.json"):
            try:
                data = json.loads(file.read_text())
                memories.append(Memory.model_validate(data))
            except (json.JSONDecodeError, OSError, ValueError):
                continue
        memories.sort(key=lambda m: m.created_at, reverse=True)
        return memories

    def search(self, keyword: str) -> list[Memory]:
        """Search memories by keyword in content and tags."""
        keyword_lower = keyword.lower()
        results: list[Memory] = []
        for memory in self.list_all():
            if keyword_lower in memory.content.lower() or any(
                keyword_lower in tag.lower() for tag in memory.tags
            ):
                results.append(memory)
        return results

    def load_relevant(
        self,
        agent_id: str | None = None,
        project: str | None = None,
        epic: str | None = None,
    ) -> list[Memory]:
        """Load memories relevant to current context."""
        all_memories = self.list_all()
        relevant: list[Memory] = []

        for memory in all_memories:
            if memory.is_expired:
                continue
            # Match by context
            if (
                (agent_id and memory.agent_id == agent_id)
                or (project and memory.project == project)
                or (epic and memory.epic == epic)
                or memory.priority in (MemoryPriority.CRITICAL, MemoryPriority.HIGH)
            ):
                relevant.append(memory)

        return relevant

    def create_digest(self, session_id: str) -> MemoryDigest:
        """Create a digest of recent memories."""
        recent = [
            m for m in self.list_all()
            if (datetime.now() - m.created_at).days < 1
        ]
        return MemoryDigest(session_id=session_id, memories=recent)

    def prune(self, days: int = PRUNE_DAYS) -> int:
        """Remove old low-priority memories. Returns count removed."""
        cutoff = datetime.now() - timedelta(days=days)
        removed = 0

        for file in self._memory_dir.glob("*.json"):
            try:
                data = json.loads(file.read_text())
                memory = Memory.model_validate(data)
                if (
                    memory.priority == MemoryPriority.LOW
                    and memory.created_at < cutoff
                ) or memory.is_expired:
                    file.unlink()
                    removed += 1
            except (json.JSONDecodeError, OSError, ValueError):
                continue

        return removed

    def get(self, memory_id: str) -> Memory | None:
        """Get a specific memory by ID."""
        file = self._memory_dir / f"{memory_id}.json"
        if not file.exists():
            return None
        try:
            data = json.loads(file.read_text())
            return Memory.model_validate(data)
        except (json.JSONDecodeError, OSError, ValueError):
            return None

    def delete(self, memory_id: str) -> bool:
        """Delete a specific memory."""
        file = self._memory_dir / f"{memory_id}.json"
        if file.exists():
            file.unlink()
            return True
        return False

    def count(self) -> int:
        """Count total memories."""
        return len(list(self._memory_dir.glob("*.json")))

    def _save_memory(self, memory: Memory) -> None:
        """Persist a memory to disk."""
        file = self._memory_dir / f"{memory.id}.json"
        file.write_text(memory.model_dump_json(indent=2))
