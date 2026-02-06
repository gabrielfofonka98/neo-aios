"""Tests for StoryValidator."""

from pathlib import Path

from aios.quality.story_validator import StoryValidator
from aios.quality.story_validator import ValidationSeverity


class TestStoryValidator:
    def setup_method(self) -> None:
        self.validator = StoryValidator()

    def test_valid_story(self, tmp_path: Path) -> None:
        story = tmp_path / "story-01.md"
        story.write_text(
            "# Login Feature\n\n"
            "Como usuario, quero fazer login\n\n"
            "## Criterios de Aceitacao\n\n"
            "- [ ] Login com email\n"
            "- [ ] Login com Google\n\n"
            "## Definicao de Done\n\n"
            "- Testes passando\n\n"
            "Prioridade: high\n"
        )
        result = self.validator.validate(str(story))
        assert result.is_valid
        assert result.error_count == 0

    def test_missing_user_story(self, tmp_path: Path) -> None:
        story = tmp_path / "story-02.md"
        story.write_text(
            "# Feature\n\n"
            "## Criterios de Aceitacao\n\n"
            "- [ ] Item 1\n\n"
            "Prioridade: high\n"
        )
        result = self.validator.validate(str(story))
        assert not result.is_valid
        errors = [i for i in result.issues if i.severity == ValidationSeverity.ERROR]
        assert any("user story format" in i.message.lower() for i in errors)

    def test_missing_acceptance_criteria(self, tmp_path: Path) -> None:
        story = tmp_path / "story-03.md"
        story.write_text(
            "# Feature\n\n"
            "Como usuario, quero fazer algo\n\n"
            "Prioridade: high\n"
        )
        result = self.validator.validate(str(story))
        assert any(i.rule == "acceptance_criteria" for i in result.issues)

    def test_missing_priority(self, tmp_path: Path) -> None:
        story = tmp_path / "story-04.md"
        story.write_text(
            "# Feature\n\n"
            "Como usuario, quero fazer algo\n\n"
            "## Criterios de Aceitacao\n\n"
            "- [ ] Item\n"
        )
        result = self.validator.validate(str(story))
        assert any(i.rule == "priority" for i in result.issues)

    def test_file_not_found(self) -> None:
        result = self.validator.validate("/nonexistent/story.md")
        assert not result.is_valid
        assert result.error_count == 1

    def test_empty_file(self, tmp_path: Path) -> None:
        story = tmp_path / "story-05.md"
        story.write_text("short")
        result = self.validator.validate(str(story))
        assert not result.is_valid

    def test_validate_directory(self, tmp_path: Path) -> None:
        (tmp_path / "story-01.md").write_text(
            "# S1\n\nComo usuario, quero X\n\n"
            "## Criterios de Aceitacao\n\n- [ ] A\n\nPrioridade: high\n"
        )
        (tmp_path / "story-02.md").write_text(
            "# S2\n\nComo admin, quero Y\n\n"
            "## Criterios de Aceitacao\n\n- [ ] B\n\nPrioridade: low\n"
        )
        results = self.validator.validate_directory(str(tmp_path))
        assert len(results) == 2

    def test_acceptance_criteria_english(self, tmp_path: Path) -> None:
        story = tmp_path / "story-06.md"
        story.write_text(
            "# Feature\n\n"
            "Como usuario, quero algo\n\n"
            "## Acceptance Criteria\n\n"
            "- [ ] Item 1\n\n"
            "Priority: high\n"
        )
        result = self.validator.validate(str(story))
        # Should accept English headers too
        assert not any(i.rule == "acceptance_criteria" for i in result.issues)
