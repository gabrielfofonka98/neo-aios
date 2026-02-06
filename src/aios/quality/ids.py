"""IDS Engine — REUSE > ADAPT > CREATE."""

from __future__ import annotations

import json
from difflib import SequenceMatcher
from pathlib import Path

from aios.quality.ids_models import IDSAction
from aios.quality.ids_models import IDSDecision
from aios.quality.ids_models import IDSMatch
from aios.quality.ids_models import IDSStats

STATS_FILE = Path(".aios/ids-stats.json")

# Similarity thresholds
REUSE_THRESHOLD = 0.8  # >= 80% = REUSE
ADAPT_THRESHOLD = 0.5  # >= 50% = ADAPT


class IDSEngine:
    """Incremental Development System — enforces REUSE > ADAPT > CREATE."""

    def __init__(self, search_paths: list[Path] | None = None) -> None:
        self._search_paths = search_paths or [
            Path("src"),
            Path("agents"),
            Path(".claude/skills"),
        ]

    def check(self, target: str) -> IDSDecision:
        """Analyze a path/name and recommend REUSE, ADAPT, or CREATE."""
        target_path = Path(target)

        matches: list[IDSMatch] = []
        self._collect_filename_matches(target_path, matches)
        self._collect_module_matches(target, matches)

        # Sort by similarity descending
        matches.sort(key=lambda m: m.similarity, reverse=True)

        # Determine action
        action, reason = self._determine_action(matches)

        decision = IDSDecision(
            action=action,
            target_path=target,
            matches=matches[:5],  # Top 5
            reason=reason,
        )

        # Track stats
        self._record_stats(action)

        return decision

    def _collect_filename_matches(self, target_path: Path, matches: list[IDSMatch]) -> None:
        """Phase 1: Collect matches based on filename similarity."""
        target_name = target_path.stem
        target_suffix = target_path.suffix

        for search_path in self._search_paths:
            if not search_path.exists():
                continue
            for existing in search_path.rglob("*"):
                if not existing.is_file():
                    continue
                if existing.suffix != target_suffix and target_suffix:
                    continue
                sim = self._name_similarity(target_name, existing.stem)
                if sim >= ADAPT_THRESHOLD:
                    matches.append(
                        IDSMatch(
                            path=str(existing),
                            similarity=sim,
                            match_type="filename",
                            reason=f"Name similarity: {sim:.0%}",
                        )
                    )

    def _collect_module_matches(self, target: str, matches: list[IDSMatch]) -> None:
        """Phase 2: Collect matches based on module path similarity."""
        for search_path in self._search_paths:
            if not search_path.exists():
                continue
            for existing in search_path.rglob("*.py"):
                module_sim = self._module_similarity(target, str(existing))
                if module_sim >= ADAPT_THRESHOLD:
                    existing_paths = {m.path for m in matches}
                    if str(existing) not in existing_paths:
                        matches.append(
                            IDSMatch(
                                path=str(existing),
                                similarity=module_sim,
                                match_type="module_path",
                                reason=f"Module path similarity: {module_sim:.0%}",
                            )
                        )

    @staticmethod
    def _determine_action(matches: list[IDSMatch]) -> tuple[IDSAction, str]:
        """Determine the IDS action based on best match similarity."""
        if matches and matches[0].similarity >= REUSE_THRESHOLD:
            action = IDSAction.REUSE
            reason = f"High similarity ({matches[0].similarity:.0%}) with {matches[0].path}"
        elif matches and matches[0].similarity >= ADAPT_THRESHOLD:
            action = IDSAction.ADAPT
            reason = f"Moderate similarity ({matches[0].similarity:.0%}) with {matches[0].path}"
        else:
            action = IDSAction.CREATE
            reason = "No similar files found"
        return action, reason

    def get_stats(self) -> IDSStats:
        """Load IDS stats from persistent storage."""
        if not STATS_FILE.exists():
            return IDSStats()
        try:
            data = json.loads(STATS_FILE.read_text())
            return IDSStats.model_validate(data)
        except (json.JSONDecodeError, OSError):
            return IDSStats()

    def _record_stats(self, action: IDSAction) -> None:
        """Record action to persistent stats."""
        stats = self.get_stats()
        stats.record(action)
        try:
            STATS_FILE.parent.mkdir(parents=True, exist_ok=True)
            STATS_FILE.write_text(stats.model_dump_json(indent=2))
        except OSError:
            pass  # Non-critical

    @staticmethod
    def _name_similarity(a: str, b: str) -> float:
        """Compare file names using SequenceMatcher."""
        return SequenceMatcher(None, a.lower(), b.lower()).ratio()

    @staticmethod
    def _module_similarity(a: str, b: str) -> float:
        """Compare module paths."""
        parts_a = Path(a).parts
        parts_b = Path(b).parts
        if not parts_a or not parts_b:
            return 0.0
        common = sum(1 for pa, pb in zip(parts_a, parts_b, strict=False) if pa == pb)
        return common / max(len(parts_a), len(parts_b))
