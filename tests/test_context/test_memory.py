"""Tests for memory store."""

from pathlib import Path

from aios.context.memory import MemoryStore
from aios.context.memory_models import Memory
from aios.context.memory_models import MemoryDigest
from aios.context.memory_models import MemoryPriority
from aios.context.memory_models import MemoryType


class TestMemoryModels:
    def test_memory_not_expired(self) -> None:
        m = Memory(id="1", content="test", memory_type=MemoryType.LESSON)
        assert not m.is_expired

    def test_digest_count(self) -> None:
        digest = MemoryDigest(
            session_id="s1",
            memories=[
                Memory(id="1", content="a", memory_type=MemoryType.RULE),
                Memory(id="2", content="b", memory_type=MemoryType.PATTERN),
            ],
        )
        assert digest.count == 2

    def test_digest_by_type(self) -> None:
        digest = MemoryDigest(
            session_id="s1",
            memories=[
                Memory(id="1", content="a", memory_type=MemoryType.RULE),
                Memory(id="2", content="b", memory_type=MemoryType.PATTERN),
            ],
        )
        assert len(digest.by_type(MemoryType.RULE)) == 1


class TestMemoryStore:
    def test_add_and_list(self, tmp_path: Path) -> None:
        store = MemoryStore(memory_dir=tmp_path / "memories")
        store.add("test content", MemoryType.LESSON)
        memories = store.list_all()
        assert len(memories) == 1
        assert memories[0].content == "test content"

    def test_search(self, tmp_path: Path) -> None:
        store = MemoryStore(memory_dir=tmp_path / "memories")
        store.add("fix bug in router", MemoryType.INCIDENT)
        store.add("add new feature", MemoryType.DECISION)
        results = store.search("router")
        assert len(results) == 1

    def test_search_by_tag(self, tmp_path: Path) -> None:
        store = MemoryStore(memory_dir=tmp_path / "memories")
        store.add("some content", MemoryType.RULE, tags=["auth", "security"])
        results = store.search("auth")
        assert len(results) == 1

    def test_delete(self, tmp_path: Path) -> None:
        store = MemoryStore(memory_dir=tmp_path / "memories")
        m = store.add("to delete", MemoryType.LESSON)
        assert store.delete(m.id)
        assert store.get(m.id) is None

    def test_count(self, tmp_path: Path) -> None:
        store = MemoryStore(memory_dir=tmp_path / "memories")
        store.add("a", MemoryType.RULE)
        store.add("b", MemoryType.PATTERN)
        assert store.count() == 2

    def test_load_relevant_high_priority(self, tmp_path: Path) -> None:
        store = MemoryStore(memory_dir=tmp_path / "memories")
        store.add("critical info", MemoryType.RULE, priority=MemoryPriority.CRITICAL)
        store.add("low info", MemoryType.LESSON, priority=MemoryPriority.LOW)
        relevant = store.load_relevant()
        assert len(relevant) == 1
        assert relevant[0].priority == MemoryPriority.CRITICAL

    def test_prune(self, tmp_path: Path) -> None:
        store = MemoryStore(memory_dir=tmp_path / "memories")
        store.add("recent", MemoryType.LESSON, priority=MemoryPriority.LOW)
        # days=0 means cutoff=now, memory created microseconds before is older than cutoff
        removed = store.prune(days=0)
        assert removed == 1

    def test_prune_keeps_high_priority(self, tmp_path: Path) -> None:
        store = MemoryStore(memory_dir=tmp_path / "memories")
        store.add("important", MemoryType.RULE, priority=MemoryPriority.HIGH)
        removed = store.prune(days=0)
        assert removed == 0
        assert store.count() == 1
