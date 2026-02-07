"""Cost tracking models for pipeline execution."""

from __future__ import annotations

from pydantic import BaseModel
from pydantic import Field

# Pricing per million tokens (input/output average approximation)
MODEL_PRICING_PER_M_TOKENS: dict[str, float] = {
    "haiku": 1.25,
    "sonnet": 7.50,
    "opus": 37.50,
}


class ModelUsage(BaseModel):
    """Token usage for a specific model tier."""

    model: str
    tokens_used: int = Field(default=0, validation_alias="tokensUsed")
    step_count: int = Field(default=0, validation_alias="stepCount")

    model_config = {"populate_by_name": True}

    @property
    def estimated_cost_usd(self) -> float:
        """Estimated cost in USD."""
        price = MODEL_PRICING_PER_M_TOKENS.get(self.model, 37.50)
        return (self.tokens_used / 1_000_000) * price


class StoryCostReport(BaseModel):
    """Cost report for a complete story execution."""

    story_id: str = Field(validation_alias="storyId")
    total_tokens: int = Field(default=0, validation_alias="totalTokens")
    total_steps: int = Field(default=0, validation_alias="totalSteps")
    usage_by_model: list[ModelUsage] = Field(
        default_factory=list, validation_alias="usageByModel"
    )

    model_config = {"populate_by_name": True}

    @property
    def total_cost_usd(self) -> float:
        """Total estimated cost across all models."""
        return sum(u.estimated_cost_usd for u in self.usage_by_model)

    @property
    def all_opus_cost_usd(self) -> float:
        """What the cost would be if all tokens used opus."""
        price = MODEL_PRICING_PER_M_TOKENS["opus"]
        return (self.total_tokens / 1_000_000) * price

    @property
    def savings_vs_all_opus_usd(self) -> float:
        """How much was saved by using mixed models vs all opus."""
        return self.all_opus_cost_usd - self.total_cost_usd

    @property
    def savings_percentage(self) -> float:
        """Percentage saved vs all-opus execution."""
        if self.all_opus_cost_usd == 0:
            return 0.0
        return (self.savings_vs_all_opus_usd / self.all_opus_cost_usd) * 100

    @classmethod
    def from_step_results(
        cls,
        story_id: str,
        steps: list[tuple[str, int]],
    ) -> StoryCostReport:
        """Build report from list of (model, tokens_used) tuples.

        Args:
            story_id: Story identifier.
            steps: List of (model_name, tokens_used) per step.

        Returns:
            StoryCostReport with aggregated usage.
        """
        model_map: dict[str, ModelUsage] = {}
        total_tokens = 0

        for model, tokens in steps:
            total_tokens += tokens
            if model not in model_map:
                model_map[model] = ModelUsage(model=model)
            usage = model_map[model]
            usage.tokens_used += tokens
            usage.step_count += 1

        return cls(
            story_id=story_id,
            total_tokens=total_tokens,
            total_steps=len(steps),
            usage_by_model=list(model_map.values()),
        )
