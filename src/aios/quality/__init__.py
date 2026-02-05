"""Quality gate module for pre-commit and CI checks.

This module provides the quality gate infrastructure for NEO-AIOS,
including pre-commit hooks, configuration, and check runners.

Example:
    >>> from aios.quality import precommit_gate, GateConfig
    >>> from pathlib import Path
    >>> result = precommit_gate.run_checks([Path("src/module.py")])
    >>> result.passed
    True

    >>> from aios.quality import load_config, QualityGatesConfig
    >>> config = load_config(Path("config/quality-gates.yaml"))
    >>> config.precommit.enabled
    True
"""

from aios.quality.config import CheckResult
from aios.quality.config import CheckStatus
from aios.quality.config import GateConfig
from aios.quality.config import GateResult
from aios.quality.config import default_gate_config
from aios.quality.human_review import Approval
from aios.quality.human_review import ApprovalCheckResult
from aios.quality.human_review import ApprovalRequirement
from aios.quality.human_review import ApprovalStatus
from aios.quality.human_review import ApproverRole
from aios.quality.human_review import HumanReviewGate
from aios.quality.human_review import HumanReviewResult
from aios.quality.human_review import human_review_gate
from aios.quality.loader import ConfigLoader
from aios.quality.loader import ExclusionsConfig
from aios.quality.loader import HumanReviewConfig
from aios.quality.loader import PRAutomationConfig
from aios.quality.loader import PreCommitConfig
from aios.quality.loader import QualityGatesConfig
from aios.quality.loader import get_default_config
from aios.quality.loader import get_loader
from aios.quality.loader import load_config
from aios.quality.loader import load_config_or_default
from aios.quality.loader import to_yaml
from aios.quality.precommit import PreCommitGate
from aios.quality.precommit import precommit_gate
from aios.quality.precommit import run_precommit_hook

__all__ = [
    "Approval",
    "ApprovalCheckResult",
    "ApprovalRequirement",
    "ApprovalStatus",
    "ApproverRole",
    "CheckResult",
    "CheckStatus",
    "ConfigLoader",
    "ExclusionsConfig",
    "GateConfig",
    "GateResult",
    "HumanReviewConfig",
    "HumanReviewGate",
    "HumanReviewResult",
    "PRAutomationConfig",
    "PreCommitConfig",
    "PreCommitGate",
    "QualityGatesConfig",
    "default_gate_config",
    "get_default_config",
    "get_loader",
    "human_review_gate",
    "load_config",
    "load_config_or_default",
    "precommit_gate",
    "run_precommit_hook",
    "to_yaml",
]
