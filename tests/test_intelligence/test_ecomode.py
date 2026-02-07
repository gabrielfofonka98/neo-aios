"""Tests for EcomodeRouter."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from pathlib import Path
import yaml

from aios.intelligence.ecomode import EcomodeConfig
from aios.intelligence.ecomode import EcomodeKeywords
from aios.intelligence.ecomode import EcomodeModelRouting
from aios.intelligence.ecomode import EcomodeRouter

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def enabled_config() -> EcomodeConfig:
    """Ecomode config that is enabled with the standard routing rules."""
    return EcomodeConfig(
        enabled=True,
        model_routing=EcomodeModelRouting(
            always_haiku=[
                "clear-agent",
                "handoff",
                "test",
                "sync",
                "push",
                "commit",
                "fixer",
                "sec-agents",
            ],
            downgrade_to_sonnet=[
                "pm",
                "po",
                "sm",
                "doc",
                "sre",
                "ux",
                "marketing",
                "landing",
            ],
            always_opus=[
                "architect",
                "qa",
                "spec",
                "ralph",
                "dev-critical",
                "data-engineer",
            ],
        ),
        keywords=EcomodeKeywords(
            activate=["@eco", "ecomode", "modo econômico", "save tokens"],
            deactivate=["@full", "fullmode", "modo completo", "full power"],
        ),
    )


@pytest.fixture
def disabled_config() -> EcomodeConfig:
    """Ecomode config that is disabled but still has keywords configured."""
    return EcomodeConfig(
        enabled=False,
        keywords=EcomodeKeywords(
            activate=["@eco", "ecomode", "modo econômico", "save tokens"],
            deactivate=["@full", "fullmode", "modo completo", "full power"],
        ),
    )


@pytest.fixture
def enabled_router(enabled_config: EcomodeConfig) -> EcomodeRouter:
    return EcomodeRouter(config=enabled_config)


@pytest.fixture
def disabled_router(disabled_config: EcomodeConfig) -> EcomodeRouter:
    return EcomodeRouter(config=disabled_config)


# ---------------------------------------------------------------------------
# Tests: resolve_model — ecomode enabled
# ---------------------------------------------------------------------------


class TestResolveModelEnabled:
    """When ecomode is enabled, agents are routed to the correct tier."""

    def test_haiku_for_clear_agent(self, enabled_router: EcomodeRouter) -> None:
        assert enabled_router.resolve_model("clear-agent") == "haiku"

    def test_haiku_for_handoff(self, enabled_router: EcomodeRouter) -> None:
        assert enabled_router.resolve_model("handoff") == "haiku"

    def test_haiku_for_fixer(self, enabled_router: EcomodeRouter) -> None:
        assert enabled_router.resolve_model("fixer") == "haiku"

    def test_haiku_for_sec_agents(self, enabled_router: EcomodeRouter) -> None:
        assert enabled_router.resolve_model("sec-agents") == "haiku"

    def test_sonnet_for_pm(self, enabled_router: EcomodeRouter) -> None:
        assert enabled_router.resolve_model("pm") == "sonnet"

    def test_sonnet_for_doc(self, enabled_router: EcomodeRouter) -> None:
        assert enabled_router.resolve_model("doc") == "sonnet"

    def test_sonnet_for_ux(self, enabled_router: EcomodeRouter) -> None:
        assert enabled_router.resolve_model("ux") == "sonnet"

    def test_opus_for_architect(self, enabled_router: EcomodeRouter) -> None:
        assert enabled_router.resolve_model("architect") == "opus"

    def test_opus_for_qa(self, enabled_router: EcomodeRouter) -> None:
        assert enabled_router.resolve_model("qa") == "opus"

    def test_opus_for_spec(self, enabled_router: EcomodeRouter) -> None:
        assert enabled_router.resolve_model("spec") == "opus"

    def test_opus_for_ralph(self, enabled_router: EcomodeRouter) -> None:
        assert enabled_router.resolve_model("ralph") == "opus"

    def test_unknown_agent_returns_none(self, enabled_router: EcomodeRouter) -> None:
        """Agents not explicitly listed fall through to None (normal router)."""
        assert enabled_router.resolve_model("unknown-agent") is None

    def test_agent_name_is_normalized(self, enabled_router: EcomodeRouter) -> None:
        """Leading/trailing whitespace and case are normalized."""
        assert enabled_router.resolve_model("  PM  ") == "sonnet"
        assert enabled_router.resolve_model("ARCHITECT") == "opus"
        assert enabled_router.resolve_model(" Clear-Agent ") == "haiku"


# ---------------------------------------------------------------------------
# Tests: resolve_model — ecomode disabled
# ---------------------------------------------------------------------------


class TestResolveModelDisabled:
    """When ecomode is disabled, all agents return None."""

    def test_disabled_returns_none_for_haiku_agent(
        self, disabled_router: EcomodeRouter
    ) -> None:
        assert disabled_router.resolve_model("clear-agent") is None

    def test_disabled_returns_none_for_sonnet_agent(
        self, disabled_router: EcomodeRouter
    ) -> None:
        assert disabled_router.resolve_model("pm") is None

    def test_disabled_returns_none_for_opus_agent(
        self, disabled_router: EcomodeRouter
    ) -> None:
        assert disabled_router.resolve_model("architect") is None

    def test_disabled_returns_none_for_unknown(
        self, disabled_router: EcomodeRouter
    ) -> None:
        assert disabled_router.resolve_model("unknown") is None


# ---------------------------------------------------------------------------
# Tests: keyword detection
# ---------------------------------------------------------------------------


class TestKeywordDetection:
    def test_activate_keyword_eco(self, enabled_router: EcomodeRouter) -> None:
        assert enabled_router.detect_keyword("please @eco") is True

    def test_activate_keyword_ecomode(self, enabled_router: EcomodeRouter) -> None:
        assert enabled_router.detect_keyword("turn on ecomode now") is True

    def test_activate_keyword_portuguese(self, enabled_router: EcomodeRouter) -> None:
        assert enabled_router.detect_keyword("ativa o modo econômico") is True

    def test_deactivate_keyword_full(self, enabled_router: EcomodeRouter) -> None:
        assert enabled_router.detect_keyword("go @full") is False

    def test_deactivate_keyword_fullmode(self, enabled_router: EcomodeRouter) -> None:
        assert enabled_router.detect_keyword("switch to fullmode") is False

    def test_deactivate_keyword_portuguese(self, enabled_router: EcomodeRouter) -> None:
        assert enabled_router.detect_keyword("volta pro modo completo") is False

    def test_no_keyword_returns_none(self, enabled_router: EcomodeRouter) -> None:
        assert enabled_router.detect_keyword("just a regular message") is None


# ---------------------------------------------------------------------------
# Tests: apply_keyword (toggle ecomode on/off)
# ---------------------------------------------------------------------------


class TestApplyKeyword:
    def test_eco_keyword_enables(self, disabled_router: EcomodeRouter) -> None:
        """Disabled router gets enabled by an activate keyword."""
        assert not disabled_router.enabled
        result = disabled_router.apply_keyword("activate ecomode please")
        assert result is True
        assert disabled_router.enabled

    def test_full_keyword_disables(self, enabled_router: EcomodeRouter) -> None:
        """Enabled router gets disabled by a deactivate keyword."""
        assert enabled_router.enabled
        result = enabled_router.apply_keyword("switch to full power")
        assert result is False
        assert not enabled_router.enabled

    def test_no_keyword_keeps_state(self, enabled_router: EcomodeRouter) -> None:
        """No keyword detected — state stays the same."""
        assert enabled_router.enabled
        result = enabled_router.apply_keyword("random text here")
        assert result is True
        assert enabled_router.enabled


# ---------------------------------------------------------------------------
# Tests: YAML loading
# ---------------------------------------------------------------------------


class TestYamlLoading:
    def test_load_from_yaml(self, tmp_path: Path) -> None:
        """Load a valid ecomode.yaml and verify config is parsed."""
        yaml_content: dict[str, object] = {
            "ecomode": {
                "enabled": True,
                "model_routing": {
                    "always_haiku": ["clear-agent", "test"],
                    "downgrade_to_sonnet": ["pm"],
                    "always_opus": ["architect"],
                },
                "keywords": {
                    "activate": ["@eco"],
                    "deactivate": ["@full"],
                },
            }
        }
        config_file = tmp_path / "ecomode.yaml"
        config_file.write_text(yaml.dump(yaml_content), encoding="utf-8")

        router = EcomodeRouter.from_yaml(config_file)
        assert router.enabled is True
        assert router.resolve_model("clear-agent") == "haiku"
        assert router.resolve_model("pm") == "sonnet"
        assert router.resolve_model("architect") == "opus"

    def test_load_missing_file_raises(self, tmp_path: Path) -> None:
        """Attempting to load a non-existent file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            EcomodeRouter.from_yaml(tmp_path / "does-not-exist.yaml")

    def test_load_yaml_disabled_by_default(self, tmp_path: Path) -> None:
        """A minimal YAML with just the 'ecomode' key defaults to disabled."""
        config_file = tmp_path / "ecomode.yaml"
        config_file.write_text(yaml.dump({"ecomode": {}}), encoding="utf-8")

        router = EcomodeRouter.from_yaml(config_file)
        assert router.enabled is False
        assert router.resolve_model("pm") is None


# ---------------------------------------------------------------------------
# Tests: default construction
# ---------------------------------------------------------------------------


class TestDefaultConstruction:
    def test_default_config_is_disabled(self) -> None:
        router = EcomodeRouter()
        assert router.enabled is False
        assert router.resolve_model("anything") is None

    def test_config_property(self, enabled_config: EcomodeConfig) -> None:
        router = EcomodeRouter(config=enabled_config)
        assert router.config is enabled_config
        assert router.config.enabled is True


# ---------------------------------------------------------------------------
# Tests: task_type parameter (reserved, currently unused)
# ---------------------------------------------------------------------------


class TestTaskTypeParameter:
    def test_task_type_does_not_affect_routing(
        self, enabled_router: EcomodeRouter
    ) -> None:
        """task_type is accepted but currently ignored."""
        assert enabled_router.resolve_model("pm", task_type="documentation") == "sonnet"
        assert enabled_router.resolve_model("pm", task_type="critical") == "sonnet"
        assert enabled_router.resolve_model("pm", task_type=None) == "sonnet"
