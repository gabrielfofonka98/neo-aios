"""Tests for Glue Generator."""

from pathlib import Path

from aios.core.glue import GlueGenerator
from aios.core.glue_models import GlueConfig
from aios.core.glue_models import GlueOutput
from aios.core.glue_models import GlueSection


class TestGlueModels:
    def test_section_count(self) -> None:
        output = GlueOutput(sections=[
            GlueSection(title="A", content="test", line_count=1),
        ])
        assert output.section_count == 1

    def test_to_markdown(self) -> None:
        output = GlueOutput(sections=[
            GlueSection(title="Story", content="As a user..."),
        ])
        md = output.to_markdown()
        assert "# Story" in md
        assert "As a user..." in md


class TestGlueGenerator:
    def test_compose_story_only(self, tmp_path: Path) -> None:
        story = tmp_path / "story.md"
        story.write_text("# Story\n\nAs a user, I want X")

        config = GlueConfig(
            story_path=str(story),
            project_root=str(tmp_path),
            include_standards=False,
            include_prd=False,
            include_epic=False,
        )

        gen = GlueGenerator()
        result = gen.compose(config)
        assert result.section_count == 1
        assert result.sections[0].title == "Story"

    def test_compose_with_standards(self, tmp_path: Path) -> None:
        story = tmp_path / "story.md"
        story.write_text("# Story\n\nContent")

        standards_dir = tmp_path / ".aios-custom"
        standards_dir.mkdir()
        (standards_dir / "STANDARDS.md").write_text("# Standards\n\nRule 1")

        config = GlueConfig(
            story_path=str(story),
            project_root=str(tmp_path),
            include_standards=True,
            include_prd=False,
            include_epic=False,
        )

        gen = GlueGenerator()
        result = gen.compose(config)
        assert result.section_count == 2

    def test_truncation(self, tmp_path: Path) -> None:
        story = tmp_path / "story.md"
        story.write_text("\n".join(f"Line {i}" for i in range(100)))

        config = GlueConfig(
            story_path=str(story),
            project_root=str(tmp_path),
            max_lines=50,
            include_standards=False,
            include_prd=False,
            include_epic=False,
        )

        gen = GlueGenerator()
        result = gen.compose(config)
        assert result.total_lines <= 101  # Story is always kept in full

    def test_compose_missing_files(self, tmp_path: Path) -> None:
        story = tmp_path / "story.md"
        story.write_text("# Story")

        config = GlueConfig(
            story_path=str(story),
            project_root=str(tmp_path),
        )

        gen = GlueGenerator()
        result = gen.compose(config)
        # Only story section since other files don't exist
        assert result.section_count == 1
