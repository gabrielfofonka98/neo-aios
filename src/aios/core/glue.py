"""Glue Generator — composes agent prompts from project context."""

from __future__ import annotations

from pathlib import Path

from aios.core.glue_models import GlueConfig
from aios.core.glue_models import GlueOutput
from aios.core.glue_models import GlueSection


class GlueGenerator:
    """Reads story + PRD + epic + STANDARDS.md and composes a unified prompt."""

    def compose(self, config: GlueConfig) -> GlueOutput:
        """Compose a glue script from project context."""
        root = Path(config.project_root)
        story_path = Path(config.story_path)
        sections: list[GlueSection] = []
        total_lines = 0

        # Section 1: Story (mandatory)
        story_section = self._read_section("Story", story_path)
        if story_section:
            sections.append(story_section)
            total_lines += story_section.line_count

        # Section 2: Epic context (parent directory)
        if config.include_epic:
            epic_dir = story_path.parent
            epic_readme = epic_dir / "README.md"
            if not epic_readme.exists():
                # Try epic.md
                epic_readme = epic_dir / "epic.md"
            epic_section = self._read_section("Epic Context", epic_readme)
            if epic_section:
                sections.append(epic_section)
                total_lines += epic_section.line_count

        # Section 3: PRD
        if config.include_prd:
            prd_candidates = [
                story_path.parent.parent / "prd.md",
                root / "docs" / "product" / "prd.md",
            ]
            for prd_path in prd_candidates:
                prd_section = self._read_section("PRD", prd_path)
                if prd_section:
                    sections.append(prd_section)
                    total_lines += prd_section.line_count
                    break

        # Section 4: Technical Standards
        if config.include_standards:
            standards_path = root / ".aios-custom" / "STANDARDS.md"
            std_section = self._read_section("Technical Standards", standards_path)
            if std_section:
                sections.append(std_section)
                total_lines += std_section.line_count

        # Truncate if over limit
        truncated = False
        if total_lines > config.max_lines:
            sections, total_lines = self._truncate_sections(
                sections, config.max_lines
            )
            truncated = True

        return GlueOutput(
            sections=sections,
            total_lines=total_lines,
            truncated=truncated,
        )

    def _read_section(self, title: str, path: Path) -> GlueSection | None:
        """Read a file as a GlueSection."""
        if not path.exists():
            return None
        try:
            content = path.read_text()
            line_count = content.count("\n") + 1
            return GlueSection(
                title=title,
                content=content.strip(),
                source_path=str(path),
                line_count=line_count,
            )
        except OSError:
            return None

    def _truncate_sections(
        self,
        sections: list[GlueSection],
        max_lines: int,
    ) -> tuple[list[GlueSection], int]:
        """Truncate sections to fit within max_lines. Story always kept in full."""
        if not sections:
            return sections, 0

        # Story (first section) is always kept
        result: list[GlueSection] = [sections[0]]
        remaining = max_lines - sections[0].line_count

        for section in sections[1:]:
            if remaining <= 0:
                break
            if section.line_count <= remaining:
                result.append(section)
                remaining -= section.line_count
            else:
                # Truncate this section
                lines = section.content.split("\n")[:remaining]
                truncated_section = GlueSection(
                    title=section.title + " (truncated)",
                    content="\n".join(lines),
                    source_path=section.source_path,
                    line_count=len(lines),
                )
                result.append(truncated_section)
                remaining = 0

        total = sum(s.line_count for s in result)
        return result, total
