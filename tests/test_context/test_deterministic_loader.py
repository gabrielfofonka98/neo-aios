"""Tests for Deterministic Context Loader."""

from pathlib import Path

from aios.context.deterministic_loader import DeterministicLoader
from aios.context.models import ContextCategory
from aios.context.models import ContextPayload
from aios.context.models import ContextRule


class TestContextModels:
    def test_payload_file_count(self) -> None:
        payload = ContextPayload(
            category=ContextCategory.SESSION,
            files_loaded=["a.json", "b.yaml"],
        )
        assert payload.file_count == 2

    def test_rule_creation(self) -> None:
        rule = ContextRule(
            category=ContextCategory.IDENTITY,
            keywords=["test"],
            files=["test.json"],
        )
        assert rule.max_tokens == 5000


class TestDeterministicLoader:
    def setup_method(self) -> None:
        self.loader = DeterministicLoader()

    def test_classify_identity(self) -> None:
        assert self.loader.classify("quem sou eu?") == ContextCategory.IDENTITY

    def test_classify_backlog(self) -> None:
        assert self.loader.classify("qual o backlog?") == ContextCategory.BACKLOG

    def test_classify_architecture(self) -> None:
        assert self.loader.classify("como é a arquitetura?") == ContextCategory.ARCHITECTURE

    def test_classify_session(self) -> None:
        assert self.loader.classify("qual o estado da sessao?") == ContextCategory.SESSION

    def test_classify_unknown(self) -> None:
        assert self.loader.classify("xyzzy foobar baz") == ContextCategory.FULL

    def test_load_identity(self, tmp_path: Path) -> None:
        aios_dir = tmp_path / ".aios"
        aios_dir.mkdir()
        state_file = aios_dir / "session-state.json"
        state_file.write_text('{"activeAgent": "dev"}')

        loader = DeterministicLoader(project_root=tmp_path)
        payload = loader.load("quem sou eu?")
        assert payload.category == ContextCategory.IDENTITY
        assert payload.deterministic
        assert len(payload.files_loaded) == 1
        assert "dev" in payload.content

    def test_load_missing_files(self, tmp_path: Path) -> None:
        loader = DeterministicLoader(project_root=tmp_path)
        payload = loader.load("quem sou eu?")
        assert payload.files_loaded == []

    def test_load_full_context(self) -> None:
        payload = self.loader.load("something completely random")
        assert payload.category == ContextCategory.FULL
        assert not payload.deterministic

    def test_load_directory(self, tmp_path: Path) -> None:
        skills_dir = tmp_path / ".claude" / "skills"
        skills_dir.mkdir(parents=True)
        (skills_dir / "dev.md").write_text("# Dev Agent")
        (skills_dir / "qa.md").write_text("# QA Agent")

        rules = [
            ContextRule(
                category=ContextCategory.AGENT,
                keywords=["agent"],
                files=[".claude/skills/"],
                max_tokens=5000,
            ),
        ]
        loader = DeterministicLoader(rules=rules, project_root=tmp_path)
        payload = loader.load("which agent?")
        assert payload.file_count == 2
        assert payload.deterministic

    def test_token_estimate(self, tmp_path: Path) -> None:
        aios_dir = tmp_path / ".aios"
        aios_dir.mkdir()
        state_file = aios_dir / "session-state.json"
        state_file.write_text("x" * 400)  # 400 chars = 100 tokens

        loader = DeterministicLoader(project_root=tmp_path)
        payload = loader.load("quem sou eu?")
        assert payload.token_estimate == 100
