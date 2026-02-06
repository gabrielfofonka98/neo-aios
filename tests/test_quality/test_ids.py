"""Tests for IDS Engine."""

from pathlib import Path

from aios.quality.ids import IDSEngine
from aios.quality.ids_models import IDSAction
from aios.quality.ids_models import IDSDecision
from aios.quality.ids_models import IDSMatch
from aios.quality.ids_models import IDSStats


class TestIDSStats:
    def test_initial_create_rate(self) -> None:
        stats = IDSStats()
        assert stats.create_rate == 0.0

    def test_record_action(self) -> None:
        stats = IDSStats()
        stats.record(IDSAction.REUSE)
        assert stats.total_checks == 1
        assert stats.reuse_count == 1

    def test_create_rate(self) -> None:
        stats = IDSStats()
        stats.record(IDSAction.CREATE)
        stats.record(IDSAction.REUSE)
        assert stats.create_rate == 0.5


class TestIDSDecision:
    def test_best_match_empty(self) -> None:
        decision = IDSDecision(action=IDSAction.CREATE, target_path="test.py")
        assert decision.best_match is None

    def test_best_match(self) -> None:
        decision = IDSDecision(
            action=IDSAction.ADAPT,
            target_path="test.py",
            matches=[
                IDSMatch(path="a.py", similarity=0.5, match_type="filename"),
                IDSMatch(path="b.py", similarity=0.9, match_type="filename"),
            ],
        )
        assert decision.best_match is not None
        assert decision.best_match.path == "b.py"


class TestIDSEngine:
    def test_check_nonexistent(self, tmp_path: Path) -> None:
        engine = IDSEngine(search_paths=[tmp_path])
        decision = engine.check("totally_unique_file_xyz.py")
        assert decision.action == IDSAction.CREATE

    def test_check_similar_file(self, tmp_path: Path) -> None:
        # Create a file to match against
        (tmp_path / "router.py").write_text("# router")
        engine = IDSEngine(search_paths=[tmp_path])
        decision = engine.check("router.py")
        assert decision.action == IDSAction.REUSE

    def test_check_partial_match(self, tmp_path: Path) -> None:
        (tmp_path / "task_router.py").write_text("# task router")
        engine = IDSEngine(search_paths=[tmp_path])
        decision = engine.check("router.py")
        # "router" vs "task_router" should have moderate similarity
        assert decision.action in (IDSAction.ADAPT, IDSAction.CREATE)

    def test_name_similarity(self) -> None:
        assert IDSEngine._name_similarity("router", "router") == 1.0
        assert IDSEngine._name_similarity("router", "xxxxx") < 0.5

    def test_get_stats(self) -> None:
        engine = IDSEngine()
        stats = engine.get_stats()
        assert isinstance(stats, IDSStats)
