"""Ecomode router — cost-optimized model routing from ecomode.yaml config."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel
from pydantic import Field

# ---------------------------------------------------------------------------
# Pydantic models for ecomode.yaml
# ---------------------------------------------------------------------------


class EcomodeModelRouting(BaseModel):
    """Model routing tiers for ecomode."""

    always_haiku: list[str] = Field(default_factory=list)
    downgrade_to_sonnet: list[str] = Field(default_factory=list)
    always_opus: list[str] = Field(default_factory=list)


class EcomodeBehaviors(BaseModel):
    """Behavioral optimizations when ecomode is active."""

    reduce_preamble: bool = True
    skip_options_simple: bool = True
    compress_output: bool = True
    limit_tool_calls: int = 5
    skip_confirmation_simple: bool = True
    terse_error_messages: bool = True


class EcomodeQualityGates(BaseModel):
    """Quality gate settings — ecomode never bypasses these."""

    maintain_layer_1: bool = True
    maintain_layer_2: bool = True
    maintain_layer_3: bool = True


class EcomodeKeywords(BaseModel):
    """Keywords to toggle ecomode on/off mid-session."""

    activate: list[str] = Field(default_factory=list)
    deactivate: list[str] = Field(default_factory=list)


class EcomodeContextLimits(BaseModel):
    """Optional context window limits."""

    enabled: bool = False
    max_context_tokens: int = 200_000
    aggressive_truncation: bool = False


class EcomodeTracking(BaseModel):
    """Usage tracking settings."""

    enabled: bool = True
    output_path: str = ".aios/ecomode-stats.json"
    metrics: list[str] = Field(default_factory=list)


class EcomodeConfig(BaseModel):
    """Top-level ecomode configuration."""

    enabled: bool = False
    model_routing: EcomodeModelRouting = Field(default_factory=EcomodeModelRouting)
    behaviors: EcomodeBehaviors = Field(default_factory=EcomodeBehaviors)
    quality_gates: EcomodeQualityGates = Field(default_factory=EcomodeQualityGates)
    keywords: EcomodeKeywords = Field(default_factory=EcomodeKeywords)
    context_limits: EcomodeContextLimits = Field(default_factory=EcomodeContextLimits)
    tracking: EcomodeTracking = Field(default_factory=EcomodeTracking)


# ---------------------------------------------------------------------------
# EcomodeRouter
# ---------------------------------------------------------------------------


class EcomodeRouter:
    """Cost-optimized model router driven by ecomode.yaml.

    When ecomode is enabled, routes agents to cheaper models where safe.
    When disabled, returns ``None`` so the normal TaskRouter takes over.
    """

    def __init__(self, config: EcomodeConfig | None = None) -> None:
        self._config = config or EcomodeConfig()

    # -- Factory ----------------------------------------------------------

    @classmethod
    def from_yaml(cls, path: str | Path) -> EcomodeRouter:
        """Load an ``EcomodeRouter`` from a YAML file.

        Parameters
        ----------
        path:
            Path to the ``ecomode.yaml`` configuration file.

        Returns
        -------
        EcomodeRouter
            A router configured according to the YAML file.

        Raises
        ------
        FileNotFoundError
            If the YAML file does not exist.
        """
        yaml_path = Path(path)
        if not yaml_path.exists():
            raise FileNotFoundError(f"Ecomode config not found: {yaml_path}")

        raw: dict[str, Any] = yaml.safe_load(yaml_path.read_text(encoding="utf-8")) or {}
        ecomode_data: dict[str, Any] = raw.get("ecomode", raw)
        config = EcomodeConfig.model_validate(ecomode_data)
        return cls(config=config)

    # -- Public API -------------------------------------------------------

    @property
    def config(self) -> EcomodeConfig:
        """Return the current ecomode configuration."""
        return self._config

    @property
    def enabled(self) -> bool:
        """Whether ecomode is currently active."""
        return self._config.enabled

    @enabled.setter
    def enabled(self, value: bool) -> None:
        """Toggle ecomode on or off at runtime."""
        self._config.enabled = value

    def resolve_model(
        self,
        agent_name: str,
        task_type: str | None = None,  # noqa: ARG002
    ) -> str | None:
        """Resolve which model an agent should use under ecomode.

        Parameters
        ----------
        agent_name:
            The agent identifier (e.g. ``"clear-agent"``, ``"pm"``, ``"architect"``).
        task_type:
            Optional task type hint (reserved for future use).

        Returns
        -------
        str | None
            ``"haiku"``, ``"sonnet"`` or ``"opus"`` when ecomode is active.
            ``None`` when ecomode is disabled (caller should fall back to
            the normal router).
        """
        if not self._config.enabled:
            return None

        normalized = agent_name.lower().strip()
        routing = self._config.model_routing

        if normalized in routing.always_haiku:
            return "haiku"

        if normalized in routing.downgrade_to_sonnet:
            return "sonnet"

        if normalized in routing.always_opus:
            return "opus"

        # Agent not explicitly listed — return None so normal router decides.
        return None

    def detect_keyword(self, text: str) -> bool | None:
        """Detect activation / deactivation keywords in user text.

        Parameters
        ----------
        text:
            The raw user message to scan.

        Returns
        -------
        bool | None
            ``True`` if an *activate* keyword was found,
            ``False`` if a *deactivate* keyword was found,
            ``None`` if no keyword matched.
        """
        lower = text.lower()
        keywords = self._config.keywords

        for kw in keywords.activate:
            if kw.lower() in lower:
                return True

        for kw in keywords.deactivate:
            if kw.lower() in lower:
                return False

        return None

    def apply_keyword(self, text: str) -> bool:
        """Scan *text* for keywords and toggle ecomode accordingly.

        Parameters
        ----------
        text:
            The raw user message to scan.

        Returns
        -------
        bool
            The ecomode state **after** applying any detected keyword.
        """
        detection = self.detect_keyword(text)
        if detection is not None:
            self.enabled = detection
        return self.enabled
