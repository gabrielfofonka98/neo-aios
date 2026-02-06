"""Models for glue script generation."""

from __future__ import annotations

from pydantic import BaseModel
from pydantic import Field


class GlueSection(BaseModel):
    """A section in the glue output."""

    title: str
    content: str
    source_path: str | None = None
    line_count: int = 0


class GlueConfig(BaseModel):
    """Configuration for glue generation."""

    story_path: str
    project_root: str = "."
    max_lines: int = 1500
    include_standards: bool = True
    include_prd: bool = True
    include_epic: bool = True


class GlueOutput(BaseModel):
    """Result of glue generation."""

    sections: list[GlueSection] = Field(default_factory=list)
    total_lines: int = 0
    truncated: bool = False

    @property
    def section_count(self) -> int:
        return len(self.sections)

    def to_markdown(self) -> str:
        """Render all sections as markdown."""
        parts: list[str] = []
        for section in self.sections:
            parts.append(f"# {section.title}")
            if section.source_path:
                parts.append(f"<!-- Source: {section.source_path} -->")
            parts.append("")
            parts.append(section.content)
            parts.append("")
        return "\n".join(parts)
