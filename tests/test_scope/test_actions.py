"""Tests for action mapper."""

import pytest

from aios.scope.actions import ActionMapper, action_mapper


@pytest.fixture
def mapper() -> ActionMapper:
    """Create an action mapper instance."""
    return ActionMapper()


class TestActionMapperMap:
    """Tests for ActionMapper.map method."""

    def test_map_git_push(self, mapper: ActionMapper) -> None:
        """Map git push variations."""
        assert mapper.map("git push") == "git_push"
        assert mapper.map("git_push") == "git_push"
        assert mapper.map("push") == "git_push"

    def test_map_create_pr(self, mapper: ActionMapper) -> None:
        """Map PR creation variations."""
        assert mapper.map("gh pr create") == "create_pr"
        assert mapper.map("create_pr") == "create_pr"
        assert mapper.map("create pr") == "create_pr"

    def test_map_deploy(self, mapper: ActionMapper) -> None:
        """Map deploy variations."""
        assert mapper.map("deploy") == "deploy_production"
        assert mapper.map("vercel deploy") == "deploy_production"
        assert mapper.map("deploy --prod") == "deploy_production"

    def test_map_ddl(self, mapper: ActionMapper) -> None:
        """Map DDL variations."""
        assert mapper.map("create table") == "execute_ddl"
        assert mapper.map("alter table") == "execute_ddl"
        assert mapper.map("drop table") == "execute_ddl"
        assert mapper.map("execute_ddl") == "execute_ddl"

    def test_map_security_audit(self, mapper: ActionMapper) -> None:
        """Map security audit variations."""
        assert mapper.map("security audit") == "security_audit"
        assert mapper.map("security_audit") == "security_audit"
        assert mapper.map("scan security") == "security_audit"

    def test_map_write_code(self, mapper: ActionMapper) -> None:
        """Map code writing variations."""
        assert mapper.map("write_code") == "write_code"
        assert mapper.map("write code") == "write_code"
        assert mapper.map("implement") == "write_code"

    def test_map_code_review(self, mapper: ActionMapper) -> None:
        """Map code review variations."""
        assert mapper.map("code_review") == "code_review"
        assert mapper.map("review code") == "code_review"
        assert mapper.map("review") == "code_review"

    def test_map_normalizes_case(self, mapper: ActionMapper) -> None:
        """Map should normalize to lowercase."""
        assert mapper.map("GIT PUSH") == "git_push"
        assert mapper.map("Git Push") == "git_push"
        assert mapper.map("CREATE TABLE") == "execute_ddl"

    def test_map_strips_whitespace(self, mapper: ActionMapper) -> None:
        """Map should strip whitespace."""
        assert mapper.map("  git push  ") == "git_push"
        assert mapper.map("\tpush\n") == "git_push"

    def test_map_partial_match(self, mapper: ActionMapper) -> None:
        """Map should match partial strings."""
        assert mapper.map("git push origin main") == "git_push"
        assert mapper.map("please deploy now") == "deploy_production"

    def test_map_unknown_returns_normalized(self, mapper: ActionMapper) -> None:
        """Unknown operations return normalized input."""
        assert mapper.map("unknown_action") == "unknown_action"
        assert mapper.map("SOME_ACTION") == "some_action"
        assert mapper.map("  Custom Action  ") == "custom action"


class TestActionMapperGetActionForCommand:
    """Tests for ActionMapper.get_action_for_command method."""

    def test_git_push_command(self, mapper: ActionMapper) -> None:
        """Detect git push commands."""
        assert mapper.get_action_for_command("git push origin main") == "git_push"
        assert mapper.get_action_for_command("git push -f") == "git_push"

    def test_create_pr_command(self, mapper: ActionMapper) -> None:
        """Detect gh pr create commands."""
        assert mapper.get_action_for_command("gh pr create") == "create_pr"
        assert (
            mapper.get_action_for_command("gh pr create --title 'Fix'") == "create_pr"
        )

    def test_ddl_commands(self, mapper: ActionMapper) -> None:
        """Detect DDL commands."""
        assert (
            mapper.get_action_for_command("CREATE TABLE users (id INT)")
            == "execute_ddl"
        )
        assert (
            mapper.get_action_for_command("ALTER TABLE users ADD COLUMN name VARCHAR")
            == "execute_ddl"
        )
        assert mapper.get_action_for_command("DROP TABLE old_users") == "execute_ddl"

    def test_vercel_deploy_command(self, mapper: ActionMapper) -> None:
        """Detect Vercel deploy commands."""
        assert mapper.get_action_for_command("vercel deploy") == "deploy_production"
        assert mapper.get_action_for_command("vercel --prod") == "deploy_production"
        assert (
            mapper.get_action_for_command("vercel deploy --prod") == "deploy_production"
        )

    def test_unrecognized_command_returns_none(self, mapper: ActionMapper) -> None:
        """Unrecognized commands return None."""
        assert mapper.get_action_for_command("npm install") is None
        assert mapper.get_action_for_command("ls -la") is None
        assert mapper.get_action_for_command("python script.py") is None

    def test_case_insensitive(self, mapper: ActionMapper) -> None:
        """Command detection is case insensitive."""
        assert mapper.get_action_for_command("GIT PUSH") == "git_push"
        assert mapper.get_action_for_command("CREATE TABLE") == "execute_ddl"


class TestGlobalActionMapperInstance:
    """Tests for the global action_mapper instance."""

    def test_global_instance_exists(self) -> None:
        """Global action_mapper instance should exist."""
        assert action_mapper is not None
        assert isinstance(action_mapper, ActionMapper)

    def test_global_instance_is_functional(self) -> None:
        """Global instance should be functional."""
        assert action_mapper.map("git push") == "git_push"
        assert action_mapper.get_action_for_command("gh pr create") == "create_pr"


class TestActionMapperIntegration:
    """Integration tests combining mapper with common scenarios."""

    def test_typical_dev_workflow_actions(self, mapper: ActionMapper) -> None:
        """Test mapping of typical dev workflow actions."""
        actions = [
            "write code",
            "run tests",
            "commit changes",
            "review code",
        ]
        mapped = [mapper.map(a) for a in actions]

        assert "write_code" in mapped
        assert "code_review" in mapped

    def test_typical_devops_workflow_actions(self, mapper: ActionMapper) -> None:
        """Test mapping of typical devops workflow actions."""
        commands = [
            "git push origin feature-branch",
            "gh pr create --title 'New feature'",
            "vercel deploy --prod",
        ]
        mapped = [mapper.get_action_for_command(c) for c in commands]

        assert mapped == ["git_push", "create_pr", "deploy_production"]
