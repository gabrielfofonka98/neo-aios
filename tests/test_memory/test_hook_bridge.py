"""Tests for hook bridge CLI."""

from __future__ import annotations

import json
from pathlib import Path

from click.testing import CliRunner

from aios.memory.hook_bridge import cli


class TestRecordFileChange:
    """Tests for the record-file-change subcommand."""

    def test_record_create_action(self, tmp_path: Path) -> None:
        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "--project-dir", str(tmp_path),
                "record-file-change",
                "--agent", "dev",
                "--file", "src/main.py",
                "--action", "create",
            ],
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["status"] == "ok"
        assert data["agent"] == "dev"
        assert data["file"] == "src/main.py"
        assert data["action"] == "create"

    def test_record_modify_action(self, tmp_path: Path) -> None:
        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "--project-dir", str(tmp_path),
                "record-file-change",
                "--agent", "data-engineer",
                "--file", "database/migrations/001.sql",
                "--action", "modify",
            ],
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["action"] == "modify"

    def test_record_delete_action(self, tmp_path: Path) -> None:
        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "--project-dir", str(tmp_path),
                "record-file-change",
                "--agent", "dev",
                "--file", "src/old.py",
                "--action", "delete",
            ],
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["action"] == "delete"

    def test_invalid_action_rejected(self, tmp_path: Path) -> None:
        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "--project-dir", str(tmp_path),
                "record-file-change",
                "--agent", "dev",
                "--file", "src/main.py",
                "--action", "invalid",
            ],
        )
        assert result.exit_code != 0

    def test_missing_agent_rejected(self, tmp_path: Path) -> None:
        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "--project-dir", str(tmp_path),
                "record-file-change",
                "--file", "src/main.py",
                "--action", "create",
            ],
        )
        assert result.exit_code != 0

    def test_missing_file_rejected(self, tmp_path: Path) -> None:
        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "--project-dir", str(tmp_path),
                "record-file-change",
                "--agent", "dev",
                "--action", "create",
            ],
        )
        assert result.exit_code != 0

    def test_storage_created(self, tmp_path: Path) -> None:
        runner = CliRunner()
        runner.invoke(
            cli,
            [
                "--project-dir", str(tmp_path),
                "record-file-change",
                "--agent", "dev",
                "--file", "src/main.py",
                "--action", "create",
            ],
        )
        evolution_dir = tmp_path / ".aios" / "memory" / "file-evolution"
        assert evolution_dir.exists()


class TestCheckConflicts:
    """Tests for the check-conflicts subcommand."""

    def test_no_conflicts_empty(self, tmp_path: Path) -> None:
        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "--project-dir", str(tmp_path),
                "check-conflicts",
                "--agent", "dev",
            ],
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data == []

    def test_no_conflicts_single_agent(self, tmp_path: Path) -> None:
        runner = CliRunner()
        # Record two files by same agent
        runner.invoke(
            cli,
            [
                "--project-dir", str(tmp_path),
                "record-file-change",
                "--agent", "dev",
                "--file", "src/a.py",
                "--action", "create",
            ],
        )
        runner.invoke(
            cli,
            [
                "--project-dir", str(tmp_path),
                "record-file-change",
                "--agent", "dev",
                "--file", "src/b.py",
                "--action", "modify",
            ],
        )

        result = runner.invoke(
            cli,
            [
                "--project-dir", str(tmp_path),
                "check-conflicts",
                "--agent", "dev",
            ],
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data == []

    def test_detects_conflict(self, tmp_path: Path) -> None:
        runner = CliRunner()
        # Two agents modify the same file
        runner.invoke(
            cli,
            [
                "--project-dir", str(tmp_path),
                "record-file-change",
                "--agent", "dev",
                "--file", "src/shared.py",
                "--action", "modify",
            ],
        )
        runner.invoke(
            cli,
            [
                "--project-dir", str(tmp_path),
                "record-file-change",
                "--agent", "qa",
                "--file", "src/shared.py",
                "--action", "modify",
            ],
        )

        result = runner.invoke(
            cli,
            [
                "--project-dir", str(tmp_path),
                "check-conflicts",
                "--agent", "dev",
            ],
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert len(data) == 1
        assert data[0]["file_path"] == "src/shared.py"
        assert "dev" in data[0]["agents"]
        assert "qa" in data[0]["agents"]

    def test_conflict_json_structure(self, tmp_path: Path) -> None:
        runner = CliRunner()
        runner.invoke(
            cli,
            [
                "--project-dir", str(tmp_path),
                "record-file-change",
                "--agent", "dev",
                "--file", "src/app.py",
                "--action", "create",
            ],
        )
        runner.invoke(
            cli,
            [
                "--project-dir", str(tmp_path),
                "record-file-change",
                "--agent", "data-engineer",
                "--file", "src/app.py",
                "--action", "modify",
            ],
        )

        result = runner.invoke(
            cli,
            [
                "--project-dir", str(tmp_path),
                "check-conflicts",
                "--agent", "dev",
            ],
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert len(data) == 1
        conflict = data[0]
        assert "file_path" in conflict
        assert "agents" in conflict
        assert "severity" in conflict
        assert "modification_count" in conflict
        assert isinstance(conflict["agents"], list)
        assert isinstance(conflict["modification_count"], int)

    def test_missing_agent_rejected(self, tmp_path: Path) -> None:
        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "--project-dir", str(tmp_path),
                "check-conflicts",
            ],
        )
        assert result.exit_code != 0


class TestRecordGotcha:
    """Tests for the record-gotcha subcommand."""

    def test_record_basic_gotcha(self, tmp_path: Path) -> None:
        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "--project-dir", str(tmp_path),
                "record-gotcha",
                "--agent", "dev",
                "--category", "auth",
                "--description", "token expiry not handled",
            ],
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["status"] == "ok"
        assert data["agent"] == "dev"
        assert data["category"] == "auth"
        assert data["promoted"] is False

    def test_record_gotcha_with_file(self, tmp_path: Path) -> None:
        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "--project-dir", str(tmp_path),
                "record-gotcha",
                "--agent", "dev",
                "--category", "imports",
                "--description", "circular import detected",
                "--file", "src/aios/core.py",
            ],
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["status"] == "ok"

    def test_auto_promotion_after_threshold(self, tmp_path: Path) -> None:
        runner = CliRunner()
        # Record the same issue 3 times (threshold = 3)
        for _ in range(2):
            runner.invoke(
                cli,
                [
                    "--project-dir", str(tmp_path),
                    "record-gotcha",
                    "--agent", "dev",
                    "--category", "auth",
                    "--description", "token not refreshed",
                ],
            )

        # Third time should trigger promotion
        result = runner.invoke(
            cli,
            [
                "--project-dir", str(tmp_path),
                "record-gotcha",
                "--agent", "dev",
                "--category", "auth",
                "--description", "token not refreshed",
            ],
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["promoted"] is True
        assert data["total_gotchas"] >= 1

    def test_missing_category_rejected(self, tmp_path: Path) -> None:
        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "--project-dir", str(tmp_path),
                "record-gotcha",
                "--agent", "dev",
                "--description", "some issue",
            ],
        )
        assert result.exit_code != 0

    def test_missing_description_rejected(self, tmp_path: Path) -> None:
        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "--project-dir", str(tmp_path),
                "record-gotcha",
                "--agent", "dev",
                "--category", "auth",
            ],
        )
        assert result.exit_code != 0

    def test_missing_agent_rejected(self, tmp_path: Path) -> None:
        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "--project-dir", str(tmp_path),
                "record-gotcha",
                "--category", "auth",
                "--description", "issue",
            ],
        )
        assert result.exit_code != 0

    def test_storage_created(self, tmp_path: Path) -> None:
        runner = CliRunner()
        runner.invoke(
            cli,
            [
                "--project-dir", str(tmp_path),
                "record-gotcha",
                "--agent", "dev",
                "--category", "test",
                "--description", "some issue",
            ],
        )
        gotchas_path = tmp_path / ".aios" / "memory" / "gotchas.json"
        assert gotchas_path.exists()


class TestGetGotchas:
    """Tests for the get-gotchas subcommand."""

    def test_empty_gotchas_text(self, tmp_path: Path) -> None:
        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "--project-dir", str(tmp_path),
                "get-gotchas",
                "--agent", "dev",
            ],
        )
        assert result.exit_code == 0
        # Empty output or just whitespace
        assert result.output.strip() == ""

    def test_empty_gotchas_json(self, tmp_path: Path) -> None:
        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "--project-dir", str(tmp_path),
                "get-gotchas",
                "--agent", "dev",
                "--format", "json",
            ],
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data == []

    def test_gotchas_text_format(self, tmp_path: Path) -> None:
        runner = CliRunner()
        # Create a gotcha by recording 3 times
        for _ in range(3):
            runner.invoke(
                cli,
                [
                    "--project-dir", str(tmp_path),
                    "record-gotcha",
                    "--agent", "dev",
                    "--category", "auth",
                    "--description", "always validate tokens",
                ],
            )

        result = runner.invoke(
            cli,
            [
                "--project-dir", str(tmp_path),
                "get-gotchas",
                "--agent", "dev",
            ],
        )
        assert result.exit_code == 0
        assert "Known Gotchas" in result.output
        assert "auth" in result.output
        assert "always validate tokens" in result.output

    def test_gotchas_json_format(self, tmp_path: Path) -> None:
        runner = CliRunner()
        for _ in range(3):
            runner.invoke(
                cli,
                [
                    "--project-dir", str(tmp_path),
                    "record-gotcha",
                    "--agent", "dev",
                    "--category", "db",
                    "--description", "always use connection pooling",
                ],
            )

        result = runner.invoke(
            cli,
            [
                "--project-dir", str(tmp_path),
                "get-gotchas",
                "--agent", "dev",
                "--format", "json",
            ],
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert len(data) == 1
        assert data[0]["category"] == "db"
        assert data[0]["description"] == "always use connection pooling"
        assert "occurrence_count" in data[0]
        assert "promoted_at" in data[0]

    def test_filter_by_category(self, tmp_path: Path) -> None:
        runner = CliRunner()
        # Create two gotchas in different categories
        for _ in range(3):
            runner.invoke(
                cli,
                [
                    "--project-dir", str(tmp_path),
                    "record-gotcha",
                    "--agent", "dev",
                    "--category", "auth",
                    "--description", "auth issue",
                ],
            )
        for _ in range(3):
            runner.invoke(
                cli,
                [
                    "--project-dir", str(tmp_path),
                    "record-gotcha",
                    "--agent", "dev",
                    "--category", "db",
                    "--description", "db issue",
                ],
            )

        result = runner.invoke(
            cli,
            [
                "--project-dir", str(tmp_path),
                "get-gotchas",
                "--agent", "dev",
                "--category", "auth",
                "--format", "json",
            ],
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert len(data) == 1
        assert data[0]["category"] == "auth"

    def test_min_severity_warning(self, tmp_path: Path) -> None:
        runner = CliRunner()
        # Create a gotcha with exactly 3 occurrences (threshold)
        for _ in range(3):
            runner.invoke(
                cli,
                [
                    "--project-dir", str(tmp_path),
                    "record-gotcha",
                    "--agent", "dev",
                    "--category", "test",
                    "--description", "threshold gotcha",
                ],
            )

        result = runner.invoke(
            cli,
            [
                "--project-dir", str(tmp_path),
                "get-gotchas",
                "--agent", "dev",
                "--min-severity", "warning",
                "--format", "json",
            ],
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        # Gotcha with count=3 passes warning filter (>= 3)
        assert len(data) == 1

    def test_min_severity_error(self, tmp_path: Path) -> None:
        runner = CliRunner()
        # Create a gotcha with exactly 3 occurrences
        for _ in range(3):
            runner.invoke(
                cli,
                [
                    "--project-dir", str(tmp_path),
                    "record-gotcha",
                    "--agent", "dev",
                    "--category", "test",
                    "--description", "low count gotcha",
                ],
            )

        result = runner.invoke(
            cli,
            [
                "--project-dir", str(tmp_path),
                "get-gotchas",
                "--agent", "dev",
                "--min-severity", "error",
                "--format", "json",
            ],
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        # Gotcha with count=3 does NOT pass error filter (>= 5)
        assert len(data) == 0

    def test_missing_agent_rejected(self, tmp_path: Path) -> None:
        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "--project-dir", str(tmp_path),
                "get-gotchas",
            ],
        )
        assert result.exit_code != 0


class TestIntegration:
    """Integration tests verifying bridge <-> module interaction."""

    def test_file_change_then_conflict_check(self, tmp_path: Path) -> None:
        """Full flow: record changes from two agents, detect conflict."""
        runner = CliRunner()

        # Agent dev modifies a file
        result1 = runner.invoke(
            cli,
            [
                "--project-dir", str(tmp_path),
                "record-file-change",
                "--agent", "dev",
                "--file", "src/shared.py",
                "--action", "modify",
            ],
        )
        assert result1.exit_code == 0

        # Agent qa modifies the same file
        result2 = runner.invoke(
            cli,
            [
                "--project-dir", str(tmp_path),
                "record-file-change",
                "--agent", "qa",
                "--file", "src/shared.py",
                "--action", "modify",
            ],
        )
        assert result2.exit_code == 0

        # Check conflicts for dev
        result3 = runner.invoke(
            cli,
            [
                "--project-dir", str(tmp_path),
                "check-conflicts",
                "--agent", "dev",
            ],
        )
        assert result3.exit_code == 0
        conflicts = json.loads(result3.output)
        assert len(conflicts) == 1
        assert "dev" in conflicts[0]["agents"]
        assert "qa" in conflicts[0]["agents"]

    def test_gotcha_full_lifecycle(self, tmp_path: Path) -> None:
        """Full flow: record issue 3 times, verify promotion, retrieve."""
        runner = CliRunner()

        # Record same issue 3 times
        for i in range(3):
            result = runner.invoke(
                cli,
                [
                    "--project-dir", str(tmp_path),
                    "record-gotcha",
                    "--agent", "dev",
                    "--category", "deploy",
                    "--description", "always verify env vars",
                    "--file", "config/env.yaml",
                ],
            )
            assert result.exit_code == 0
            data = json.loads(result.output)
            if i < 2:
                assert data["promoted"] is False
            else:
                assert data["promoted"] is True

        # Retrieve gotchas in JSON format
        result = runner.invoke(
            cli,
            [
                "--project-dir", str(tmp_path),
                "get-gotchas",
                "--agent", "dev",
                "--format", "json",
            ],
        )
        assert result.exit_code == 0
        gotchas = json.loads(result.output)
        assert len(gotchas) == 1
        assert gotchas[0]["description"] == "always verify env vars"
        assert gotchas[0]["occurrence_count"] == 3

        # Retrieve gotchas in text format
        result = runner.invoke(
            cli,
            [
                "--project-dir", str(tmp_path),
                "get-gotchas",
                "--agent", "dev",
            ],
        )
        assert result.exit_code == 0
        assert "Known Gotchas" in result.output
        assert "deploy" in result.output

    def test_multiple_agents_gotchas_independent(self, tmp_path: Path) -> None:
        """Different agents recording issues share the same store."""
        runner = CliRunner()

        # Agent dev records an issue
        runner.invoke(
            cli,
            [
                "--project-dir", str(tmp_path),
                "record-gotcha",
                "--agent", "dev",
                "--category", "auth",
                "--description", "token refresh",
            ],
        )

        # Agent qa records a different issue
        runner.invoke(
            cli,
            [
                "--project-dir", str(tmp_path),
                "record-gotcha",
                "--agent", "qa",
                "--category", "security",
                "--description", "xss vulnerability",
            ],
        )

        # Both should be retrievable by any agent
        result = runner.invoke(
            cli,
            [
                "--project-dir", str(tmp_path),
                "get-gotchas",
                "--agent", "dev",
                "--format", "json",
            ],
        )
        assert result.exit_code == 0
        # Neither is promoted yet (only 1 occurrence each), so empty
        data = json.loads(result.output)
        assert data == []

    def test_project_dir_from_env(self, tmp_path: Path) -> None:
        """Test that CLAUDE_PROJECT_DIR env var is respected."""
        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "record-file-change",
                "--agent", "dev",
                "--file", "src/test.py",
                "--action", "create",
            ],
            env={"CLAUDE_PROJECT_DIR": str(tmp_path)},
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["status"] == "ok"

    def test_context_includes_agent_and_file(self, tmp_path: Path) -> None:
        """Verify that context in gotcha includes agent and file info."""
        runner = CliRunner()

        # Record 3 times to promote
        for _ in range(3):
            runner.invoke(
                cli,
                [
                    "--project-dir", str(tmp_path),
                    "record-gotcha",
                    "--agent", "dev",
                    "--category", "auth",
                    "--description", "check context",
                    "--file", "src/auth.py",
                ],
            )

        result = runner.invoke(
            cli,
            [
                "--project-dir", str(tmp_path),
                "get-gotchas",
                "--agent", "dev",
                "--format", "json",
            ],
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert len(data) == 1
        context = data[0]["context"]
        assert "agent:dev" in context
        assert "file:src/auth.py" in context
