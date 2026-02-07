"""Tests for gotchas memory."""

from pathlib import Path

from aios.memory.gotchas import Gotcha
from aios.memory.gotchas import GotchasMemory
from aios.memory.gotchas import IssueRecord


class TestIssueRecord:
    def test_create_minimal(self) -> None:
        record = IssueRecord(category="imports", description="circular import")
        assert record.category == "imports"
        assert record.description == "circular import"
        assert record.count == 1
        assert record.context is None

    def test_create_with_context(self) -> None:
        record = IssueRecord(
            category="db",
            description="timeout on large query",
            context="users table with 1M rows",
        )
        assert record.context == "users table with 1M rows"


class TestGotcha:
    def test_create_minimal(self) -> None:
        gotcha = Gotcha(
            category="deploy",
            description="always check env vars",
            occurrence_count=5,
        )
        assert gotcha.category == "deploy"
        assert gotcha.occurrence_count == 5
        assert gotcha.context is None

    def test_create_with_context(self) -> None:
        gotcha = Gotcha(
            category="deploy",
            description="always check env vars",
            context="staging environment",
            occurrence_count=3,
        )
        assert gotcha.context == "staging environment"


class TestGotchasMemory:
    def test_record_single_issue(self, tmp_path: Path) -> None:
        mem = GotchasMemory(storage_path=tmp_path / "gotchas.json")
        mem.record_issue("auth", "token expiry not handled")

        issues = mem.get_issues()
        assert len(issues) == 1
        assert issues[0].category == "auth"
        assert issues[0].count == 1

    def test_record_increments_count(self, tmp_path: Path) -> None:
        mem = GotchasMemory(storage_path=tmp_path / "gotchas.json")
        mem.record_issue("auth", "token expiry not handled")
        mem.record_issue("auth", "token expiry not handled")

        issues = mem.get_issues()
        assert len(issues) == 1
        assert issues[0].count == 2

    def test_different_issues_tracked_separately(self, tmp_path: Path) -> None:
        mem = GotchasMemory(storage_path=tmp_path / "gotchas.json")
        mem.record_issue("auth", "token expiry")
        mem.record_issue("db", "connection pool exhausted")

        issues = mem.get_issues()
        assert len(issues) == 2

    def test_threshold_promotion(self, tmp_path: Path) -> None:
        mem = GotchasMemory(storage_path=tmp_path / "gotchas.json")
        mem.record_issue("auth", "token expiry")
        mem.record_issue("auth", "token expiry")
        mem.record_issue("auth", "token expiry")

        # Should be promoted: no more issues, one gotcha
        issues = mem.get_issues()
        gotchas = mem.get_gotchas()
        assert len(issues) == 0
        assert len(gotchas) == 1
        assert gotchas[0].category == "auth"
        assert gotchas[0].occurrence_count == 3

    def test_custom_threshold(self, tmp_path: Path) -> None:
        mem = GotchasMemory(storage_path=tmp_path / "gotchas.json", threshold=2)
        mem.record_issue("test", "flaky test")
        assert len(mem.get_gotchas()) == 0

        mem.record_issue("test", "flaky test")
        assert len(mem.get_gotchas()) == 1

    def test_get_gotchas_by_category(self, tmp_path: Path) -> None:
        mem = GotchasMemory(storage_path=tmp_path / "gotchas.json", threshold=1)
        mem.record_issue("auth", "issue A")
        mem.record_issue("db", "issue B")
        mem.record_issue("auth", "issue C")

        auth_gotchas = mem.get_gotchas(category="auth")
        assert len(auth_gotchas) == 2
        assert all(g.category == "auth" for g in auth_gotchas)

        db_gotchas = mem.get_gotchas(category="db")
        assert len(db_gotchas) == 1

    def test_get_gotchas_all(self, tmp_path: Path) -> None:
        mem = GotchasMemory(storage_path=tmp_path / "gotchas.json", threshold=1)
        mem.record_issue("auth", "issue A")
        mem.record_issue("db", "issue B")

        all_gotchas = mem.get_gotchas()
        assert len(all_gotchas) == 2

    def test_format_for_prompt_empty(self, tmp_path: Path) -> None:
        mem = GotchasMemory(storage_path=tmp_path / "gotchas.json")
        result = mem.format_for_prompt()
        assert result == ""

    def test_format_for_prompt_with_gotchas(self, tmp_path: Path) -> None:
        mem = GotchasMemory(storage_path=tmp_path / "gotchas.json", threshold=1)
        mem.record_issue("auth", "always validate tokens")
        mem.record_issue("db", "use connection pooling", context="PostgreSQL")

        result = mem.format_for_prompt()
        assert "## Known Gotchas" in result
        assert "[auth]" in result
        assert "[db]" in result
        assert "(PostgreSQL)" in result

    def test_format_for_prompt_max_lines(self, tmp_path: Path) -> None:
        mem = GotchasMemory(storage_path=tmp_path / "gotchas.json", threshold=1)
        for i in range(10):
            mem.record_issue("cat", f"issue {i}")

        result = mem.format_for_prompt(max_lines=5)
        lines = result.strip().split("\n")
        assert len(lines) <= 6  # header + blank + max_lines items + "... and N more"

    def test_context_updated_on_rerecord(self, tmp_path: Path) -> None:
        mem = GotchasMemory(storage_path=tmp_path / "gotchas.json")
        mem.record_issue("auth", "token expiry", context="v1")
        mem.record_issue("auth", "token expiry", context="v2")

        issues = mem.get_issues()
        assert issues[0].context == "v2"

    def test_markdown_sync(self, tmp_path: Path) -> None:
        mem = GotchasMemory(storage_path=tmp_path / "gotchas.json", threshold=1)
        mem.record_issue("auth", "always validate tokens")

        md_path = tmp_path / "gotchas.md"
        assert md_path.exists()
        content = md_path.read_text()
        assert "# Gotchas" in content
        assert "Confirmed Gotchas" in content
        assert "always validate tokens" in content

    def test_markdown_sync_with_tracked_issues(self, tmp_path: Path) -> None:
        mem = GotchasMemory(storage_path=tmp_path / "gotchas.json")
        mem.record_issue("auth", "token issue")

        md_path = tmp_path / "gotchas.md"
        content = md_path.read_text()
        assert "Tracked Issues" in content
        assert "1/3" in content  # count/threshold

    def test_persistence_across_instances(self, tmp_path: Path) -> None:
        path = tmp_path / "gotchas.json"
        mem1 = GotchasMemory(storage_path=path)
        mem1.record_issue("auth", "token expiry")
        mem1.record_issue("auth", "token expiry")

        # New instance from same file
        mem2 = GotchasMemory(storage_path=path)
        mem2.record_issue("auth", "token expiry")

        # Should be promoted after 3rd occurrence
        gotchas = mem2.get_gotchas()
        assert len(gotchas) == 1
        assert gotchas[0].occurrence_count == 3

    def test_storage_path_property(self, tmp_path: Path) -> None:
        path = tmp_path / "gotchas.json"
        mem = GotchasMemory(storage_path=path)
        assert mem.storage_path == path

    def test_threshold_property(self, tmp_path: Path) -> None:
        mem = GotchasMemory(storage_path=tmp_path / "g.json", threshold=5)
        assert mem.threshold == 5

    def test_corrupted_json_handled(self, tmp_path: Path) -> None:
        path = tmp_path / "gotchas.json"
        path.write_text("not valid json {{{")
        mem = GotchasMemory(storage_path=path)
        # Should not crash, treat as empty
        issues = mem.get_issues()
        assert issues == []
        gotchas = mem.get_gotchas()
        assert gotchas == []

    def test_issue_key_deterministic(self, tmp_path: Path) -> None:
        mem = GotchasMemory(storage_path=tmp_path / "gotchas.json")
        key1 = mem._issue_key("auth", "token expiry")
        key2 = mem._issue_key("auth", "token expiry")
        assert key1 == key2

    def test_issue_key_different_for_different_inputs(self, tmp_path: Path) -> None:
        mem = GotchasMemory(storage_path=tmp_path / "gotchas.json")
        key1 = mem._issue_key("auth", "token expiry")
        key2 = mem._issue_key("auth", "different issue")
        assert key1 != key2

    def test_storage_directory_created(self, tmp_path: Path) -> None:
        path = tmp_path / "subdir" / "deep" / "gotchas.json"
        GotchasMemory(storage_path=path)
        assert path.parent.exists()
