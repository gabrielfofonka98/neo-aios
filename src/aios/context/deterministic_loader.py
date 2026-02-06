"""Deterministic context loader — keyword matching, no LLM."""

from __future__ import annotations

from pathlib import Path

from aios.context.models import ContextCategory
from aios.context.models import ContextPayload
from aios.context.models import ContextRule

# Context rules (ordered by specificity)
DEFAULT_RULES: list[ContextRule] = [
    ContextRule(
        category=ContextCategory.IDENTITY,
        keywords=["quem sou", "who am i", "qual agente", "which agent", "meu papel", "my role"],
        files=[".aios/session-state.json"],
        max_tokens=1000,
        description="Agent identity context",
    ),
    ContextRule(
        category=ContextCategory.SESSION,
        keywords=["sessao", "session", "estado", "state", "contexto atual", "current context"],
        files=[".aios/session-state.json", "config/neo-aios.yaml"],
        max_tokens=3000,
        description="Current session state",
    ),
    ContextRule(
        category=ContextCategory.BACKLOG,
        keywords=["backlog", "stories", "epics", "tasks", "tarefas", "prioridades", "priorities"],
        files=["docs/product/backlog.md", "docs/product/roadmap.md"],
        max_tokens=5000,
        description="Product backlog context",
    ),
    ContextRule(
        category=ContextCategory.ARCHITECTURE,
        keywords=[
            "arquitetura",
            "architecture",
            "design",
            "sistema",
            "system",
            "stack",
            "infra",
            "infrastructure",
        ],
        files=[
            "docs/architecture/system-design.md",
            "docs/architecture/adr/",
            ".aios-custom/STANDARDS.md",
        ],
        max_tokens=10000,
        description="Architecture and design context",
    ),
    ContextRule(
        category=ContextCategory.AGENT,
        keywords=["agent", "agente", "skill", "capability", "escopo", "scope"],
        files=[".claude/skills/"],
        max_tokens=5000,
        description="Agent definitions",
    ),
    ContextRule(
        category=ContextCategory.PROJECT,
        keywords=["projeto", "project", "config", "setup", "configuracao"],
        files=["config/neo-aios.yaml", "pyproject.toml", ".env"],
        max_tokens=5000,
        description="Project configuration",
    ),
]

# Average chars per token estimate
CHARS_PER_TOKEN = 4


class DeterministicLoader:
    """Loads context based on keyword matching (<1ms)."""

    def __init__(
        self,
        rules: list[ContextRule] | None = None,
        project_root: Path | None = None,
    ) -> None:
        self._rules = rules or DEFAULT_RULES
        self._root = project_root or Path()

    def classify(self, query: str) -> ContextCategory:
        """Classify a query into a context category."""
        query_lower = query.lower()

        for rule in self._rules:
            for keyword in rule.keywords:
                if keyword in query_lower:
                    return rule.category

        return ContextCategory.FULL

    def load(self, query: str) -> ContextPayload:
        """Load context relevant to the query."""
        category = self.classify(query)

        if category == ContextCategory.FULL:
            return ContextPayload(
                category=category,
                deterministic=False,
            )

        rule = self._get_rule(category)
        if rule is None:
            return ContextPayload(category=category)

        files_loaded: list[str] = []
        content_parts: list[str] = []
        total_chars = 0
        max_chars = rule.max_tokens * CHARS_PER_TOKEN

        for file_pattern in rule.files:
            file_path = self._root / file_pattern

            if file_path.is_dir():
                # Load directory contents
                for child in sorted(file_path.rglob("*.md")):
                    if total_chars >= max_chars:
                        break
                    text = self._read_file(child, max_chars - total_chars)
                    if text:
                        files_loaded.append(str(child))
                        content_parts.append(f"--- {child.name} ---\n{text}")
                        total_chars += len(text)
            elif file_path.exists():
                text = self._read_file(file_path, max_chars - total_chars)
                if text:
                    files_loaded.append(str(file_path))
                    content_parts.append(text)
                    total_chars += len(text)

        content = "\n\n".join(content_parts)
        token_estimate = len(content) // CHARS_PER_TOKEN

        return ContextPayload(
            category=category,
            files_loaded=files_loaded,
            content=content,
            token_estimate=token_estimate,
            deterministic=True,
        )

    def _get_rule(self, category: ContextCategory) -> ContextRule | None:
        """Get the rule for a category."""
        for rule in self._rules:
            if rule.category == category:
                return rule
        return None

    @staticmethod
    def _read_file(path: Path, max_chars: int) -> str | None:
        """Read a file up to max_chars."""
        try:
            content = path.read_text()
            if len(content) > max_chars:
                content = content[:max_chars] + "\n... (truncated)"
            return content
        except OSError:
            return None
