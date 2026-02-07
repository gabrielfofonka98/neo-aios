"""Tests for TaskRouter."""

from aios.intelligence.models import RoutingDecision
from aios.intelligence.models import TaskComplexity
from aios.intelligence.router import TaskRouter


class TestTaskRouter:
    def setup_method(self) -> None:
        self.router = TaskRouter()

    def test_classify_by_agent_dev(self) -> None:
        result = self.router.classify_by_agent("dev")
        assert result.complexity == TaskComplexity.HIGH
        assert result.model == "opus"

    def test_classify_by_agent_qa(self) -> None:
        result = self.router.classify_by_agent("qa")
        assert result.complexity == TaskComplexity.MAX
        assert result.model == "opus"

    def test_classify_by_agent_fixer(self) -> None:
        result = self.router.classify_by_agent("fixer")
        assert result.complexity == TaskComplexity.LOW
        assert result.model == "haiku"

    def test_classify_by_agent_pm(self) -> None:
        result = self.router.classify_by_agent("pm")
        assert result.complexity == TaskComplexity.MEDIUM
        assert result.model == "sonnet"

    def test_classify_by_agent_unknown(self) -> None:
        result = self.router.classify_by_agent("unknown")
        assert result.complexity == TaskComplexity.HIGH  # default

    def test_classify_by_description_security(self) -> None:
        result = self.router.classify_by_description("Run security audit on src/")
        assert result.complexity == TaskComplexity.MAX

    def test_classify_by_description_fix(self) -> None:
        result = self.router.classify_by_description("fix typo in the header")
        assert result.complexity == TaskComplexity.LOW

    def test_classify_by_description_implement(self) -> None:
        result = self.router.classify_by_description("implement new API endpoint")
        assert result.complexity == TaskComplexity.HIGH

    def test_classify_by_description_no_match(self) -> None:
        result = self.router.classify_by_description("xyzzy foobar")
        assert result.complexity == TaskComplexity.HIGH  # default
        assert result.confidence == 0.5

    def test_classify_with_agent(self) -> None:
        result = self.router.classify("some description", agent_id="qa")
        assert result.complexity == TaskComplexity.MAX
        assert result.agent_id == "qa"

    def test_classify_without_agent(self) -> None:
        result = self.router.classify("implement feature")
        assert result.agent_id is None


class TestClassifyByStep:
    def setup_method(self) -> None:
        self.router = TaskRouter()

    def test_explicit_step_model_haiku(self) -> None:
        result = self.router.classify_by_step("run-tests", step_model="haiku")
        assert result.model == "haiku"
        assert result.complexity == TaskComplexity.LOW
        assert result.confidence == 1.0

    def test_explicit_step_model_opus(self) -> None:
        result = self.router.classify_by_step("code-review", step_model="opus")
        assert result.model == "opus"
        assert result.complexity == TaskComplexity.HIGH
        assert result.confidence == 1.0

    def test_explicit_step_model_sonnet(self) -> None:
        result = self.router.classify_by_step("analyze", step_model="sonnet")
        assert result.model == "sonnet"
        assert result.complexity == TaskComplexity.MEDIUM

    def test_fallback_to_agent(self) -> None:
        result = self.router.classify_by_step("step-1", agent_id="qa")
        assert result.complexity == TaskComplexity.MAX
        assert result.model == "opus"

    def test_step_model_overrides_agent(self) -> None:
        result = self.router.classify_by_step(
            "run-tests", step_model="haiku", agent_id="qa"
        )
        assert result.model == "haiku"
        assert result.complexity == TaskComplexity.LOW

    def test_no_model_no_agent_defaults_high(self) -> None:
        result = self.router.classify_by_step("unknown-step")
        assert result.complexity == TaskComplexity.HIGH
        assert result.model == "opus"
        assert result.confidence == 0.5

    def test_agent_id_included_in_result(self) -> None:
        result = self.router.classify_by_step(
            "step-1", step_model="sonnet", agent_id="dev"
        )
        assert result.agent_id == "dev"


class TestModelToComplexity:
    def test_haiku_maps_to_low(self) -> None:
        assert TaskRouter._model_to_complexity("haiku") == TaskComplexity.LOW

    def test_sonnet_maps_to_medium(self) -> None:
        assert TaskRouter._model_to_complexity("sonnet") == TaskComplexity.MEDIUM

    def test_opus_maps_to_high(self) -> None:
        assert TaskRouter._model_to_complexity("opus") == TaskComplexity.HIGH

    def test_unknown_model_defaults_to_high(self) -> None:
        assert TaskRouter._model_to_complexity("unknown") == TaskComplexity.HIGH


class TestRoutingDecision:
    def test_model_tier_display(self) -> None:
        decision = RoutingDecision(
            complexity=TaskComplexity.HIGH,
            model="opus",
        )
        assert "Opus" in decision.model_tier

    def test_default_confidence(self) -> None:
        decision = RoutingDecision(
            complexity=TaskComplexity.LOW,
            model="haiku",
        )
        assert decision.confidence == 1.0
