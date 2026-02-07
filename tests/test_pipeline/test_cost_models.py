"""Tests for cost tracking models."""

from aios.pipeline.cost_models import MODEL_PRICING_PER_M_TOKENS
from aios.pipeline.cost_models import ModelUsage
from aios.pipeline.cost_models import StoryCostReport


class TestModelUsage:
    def test_create_minimal(self) -> None:
        usage = ModelUsage(model="haiku")
        assert usage.tokens_used == 0
        assert usage.step_count == 0

    def test_estimated_cost_haiku(self) -> None:
        usage = ModelUsage(model="haiku", tokens_used=1_000_000)
        assert usage.estimated_cost_usd == MODEL_PRICING_PER_M_TOKENS["haiku"]

    def test_estimated_cost_opus(self) -> None:
        usage = ModelUsage(model="opus", tokens_used=1_000_000)
        assert usage.estimated_cost_usd == MODEL_PRICING_PER_M_TOKENS["opus"]

    def test_estimated_cost_zero_tokens(self) -> None:
        usage = ModelUsage(model="sonnet", tokens_used=0)
        assert usage.estimated_cost_usd == 0.0

    def test_estimated_cost_partial(self) -> None:
        usage = ModelUsage(model="haiku", tokens_used=500_000)
        expected = MODEL_PRICING_PER_M_TOKENS["haiku"] * 0.5
        assert abs(usage.estimated_cost_usd - expected) < 0.001


class TestStoryCostReport:
    def test_create_empty(self) -> None:
        report = StoryCostReport(story_id="s1")
        assert report.total_cost_usd == 0.0
        assert report.all_opus_cost_usd == 0.0
        assert report.savings_vs_all_opus_usd == 0.0
        assert report.savings_percentage == 0.0

    def test_from_step_results(self) -> None:
        steps = [
            ("haiku", 8000),
            ("sonnet", 12000),
            ("opus", 25000),
            ("haiku", 5000),
            ("opus", 20000),
        ]
        report = StoryCostReport.from_step_results("story-1", steps)

        assert report.total_tokens == 70000
        assert report.total_steps == 5
        assert len(report.usage_by_model) == 3

    def test_savings_vs_all_opus(self) -> None:
        steps = [
            ("haiku", 18000),
            ("sonnet", 27000),
            ("opus", 70000),
        ]
        report = StoryCostReport.from_step_results("story-1", steps)

        assert report.total_cost_usd < report.all_opus_cost_usd
        assert report.savings_vs_all_opus_usd > 0
        assert report.savings_percentage > 0

    def test_all_opus_no_savings(self) -> None:
        steps = [
            ("opus", 25000),
            ("opus", 25000),
            ("opus", 20000),
        ]
        report = StoryCostReport.from_step_results("story-1", steps)

        assert abs(report.savings_vs_all_opus_usd) < 0.001
        assert abs(report.savings_percentage) < 0.01

    def test_mixed_model_savings_percentage(self) -> None:
        steps = [
            ("haiku", 8000),
            ("haiku", 5000),
            ("haiku", 5000),
            ("sonnet", 12000),
            ("sonnet", 15000),
            ("opus", 25000),
            ("opus", 25000),
            ("opus", 20000),
        ]
        report = StoryCostReport.from_step_results("story-1", steps)

        assert report.savings_percentage > 30.0
        assert report.savings_percentage < 60.0

    def test_usage_by_model_aggregation(self) -> None:
        steps = [
            ("haiku", 5000),
            ("haiku", 3000),
            ("opus", 10000),
        ]
        report = StoryCostReport.from_step_results("story-1", steps)

        haiku_usage = next(
            (u for u in report.usage_by_model if u.model == "haiku"), None
        )
        assert haiku_usage is not None
        assert haiku_usage.tokens_used == 8000
        assert haiku_usage.step_count == 2

        opus_usage = next(
            (u for u in report.usage_by_model if u.model == "opus"), None
        )
        assert opus_usage is not None
        assert opus_usage.tokens_used == 10000
        assert opus_usage.step_count == 1
