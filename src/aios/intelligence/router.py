"""Deterministic task router — 100% rule-based, no LLM."""

from __future__ import annotations

import re
from typing import ClassVar

from aios.intelligence.models import RoutingDecision
from aios.intelligence.models import TaskComplexity

# Agent -> effort level mapping
AGENT_EFFORT_MAP: dict[str, TaskComplexity] = {
    # --- MAX effort agents (routed to opus) ---
    "qa": TaskComplexity.MAX,
    "quinn": TaskComplexity.MAX,
    "architect": TaskComplexity.MAX,
    "aria": TaskComplexity.MAX,
    "spec": TaskComplexity.MAX,
    "rune": TaskComplexity.MAX,
    "deepthink": TaskComplexity.MAX,
    # --- HIGH effort agents (routed to opus) ---
    "dev": TaskComplexity.HIGH,
    "dex": TaskComplexity.HIGH,
    "data-engineer": TaskComplexity.HIGH,
    "dara": TaskComplexity.HIGH,
    "ralph": TaskComplexity.HIGH,
    "master": TaskComplexity.HIGH,
    "orion": TaskComplexity.HIGH,
    # --- MEDIUM effort agents (routed to sonnet) ---
    "pm": TaskComplexity.MEDIUM,
    "morgan": TaskComplexity.MEDIUM,
    "po": TaskComplexity.MEDIUM,
    "sm": TaskComplexity.MEDIUM,
    "doc": TaskComplexity.MEDIUM,
    "sage": TaskComplexity.MEDIUM,
    # --- LOW effort agents (routed to haiku) ---
    "fixer": TaskComplexity.LOW,
    "clear-agent": TaskComplexity.LOW,
    "test": TaskComplexity.LOW,
    "handoff": TaskComplexity.LOW,
}

# Complexity -> model mapping
COMPLEXITY_MODEL_MAP: dict[TaskComplexity, str] = {
    TaskComplexity.MAX: "opus",
    TaskComplexity.HIGH: "opus",
    TaskComplexity.MEDIUM: "sonnet",
    TaskComplexity.LOW: "haiku",
}


class TaskRouter:
    """Deterministic task router using rules only."""

    KEYWORD_PATTERNS: ClassVar[list[tuple[str, TaskComplexity]]] = [
        # MAX patterns
        (r"\b(security|audit|vulnerabilit|pentest|threat)\b", TaskComplexity.MAX),
        (r"\b(architect|design|system.design|infrastructure)\b", TaskComplexity.MAX),
        (r"\b(spec|specification|rfc|proposal)\b", TaskComplexity.MAX),
        (r"\b(deep.analysis|root.cause|investigate)\b", TaskComplexity.MAX),
        # HIGH patterns
        (r"\b(implement|develop|build|create|refactor)\b", TaskComplexity.HIGH),
        (r"\b(database|schema|migration|model)\b", TaskComplexity.HIGH),
        (r"\b(api|endpoint|service|integration)\b", TaskComplexity.HIGH),
        # MEDIUM patterns
        (r"\b(document|docs|readme|changelog)\b", TaskComplexity.MEDIUM),
        (r"\b(plan|roadmap|backlog|story|epic)\b", TaskComplexity.MEDIUM),
        (r"\b(review|feedback|comment)\b", TaskComplexity.MEDIUM),
        # LOW patterns
        (r"\b(fix.typo|rename|format|lint)\b", TaskComplexity.LOW),
        (r"\b(clear|reset|cleanup|handoff)\b", TaskComplexity.LOW),
        (r"\b(test.run|check|verify)\b", TaskComplexity.LOW),
    ]

    def classify_by_agent(self, agent_id: str) -> RoutingDecision:
        """Route based on agent identity."""
        normalized = agent_id.lower().strip()
        complexity = AGENT_EFFORT_MAP.get(normalized, TaskComplexity.HIGH)
        model = COMPLEXITY_MODEL_MAP[complexity]

        return RoutingDecision(
            complexity=complexity,
            model=model,
            agent_id=normalized,
            reason=f"Agent '{normalized}' maps to {complexity.value} effort",
        )

    def classify_by_description(self, description: str) -> RoutingDecision:
        """Route based on task description keywords."""
        text = description.lower()

        # Check patterns in priority order (max -> low)
        for pattern, complexity in self.KEYWORD_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                model = COMPLEXITY_MODEL_MAP[complexity]
                return RoutingDecision(
                    complexity=complexity,
                    model=model,
                    reason=f"Keyword match: '{pattern}' -> {complexity.value}",
                    confidence=0.8,
                )

        # No keyword matched, fall back to HIGH complexity
        return RoutingDecision(
            complexity=TaskComplexity.HIGH,
            model="opus",
            reason="No keyword match, defaulting to HIGH",
            confidence=0.5,
        )

    def classify(
        self,
        description: str,
        agent_id: str | None = None,
    ) -> RoutingDecision:
        """Classify task using agent (if provided) or description."""
        if agent_id:
            return self.classify_by_agent(agent_id)
        return self.classify_by_description(description)
