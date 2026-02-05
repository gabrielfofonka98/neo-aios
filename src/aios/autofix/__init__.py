"""Auto-fix framework for security findings.

This package provides a framework for automatically fixing security issues
detected by validators. It includes:

- Models for fix suggestions and results
- Base class for implementing custom fixers
- Framework for managing and applying fixes
- Rollback support for safe operations

Example:
    >>> from aios.autofix import AutoFixFramework, BaseFixer
    >>> from aios.security.models import SecurityFinding
    >>>
    >>> # Create and configure the framework
    >>> framework = AutoFixFramework()
    >>> framework.register_fixer(MyCustomFixer())
    >>>
    >>> # Fix findings (dry-run by default)
    >>> result = framework.fix_finding(finding)
    >>> print(result.diff.diff_text)
    >>>
    >>> # Apply fix for real
    >>> result = framework.fix_finding(finding, dry_run=False)
"""

from aios.autofix.base import BaseFixer
from aios.autofix.framework import AutoFixFramework
from aios.autofix.models import FileDiff
from aios.autofix.models import FixBatchResult
from aios.autofix.models import FixConfidence
from aios.autofix.models import FixerCapability
from aios.autofix.models import FixResult
from aios.autofix.models import FixStatus
from aios.autofix.models import FixSuggestion
from aios.autofix.reflexion import BoundedReflexion
from aios.autofix.reflexion import ReflexionResult

__all__ = [
    "AutoFixFramework",
    "BaseFixer",
    "BoundedReflexion",
    "FileDiff",
    "FixBatchResult",
    "FixConfidence",
    "FixResult",
    "FixStatus",
    "FixSuggestion",
    "FixerCapability",
    "ReflexionResult",
]
