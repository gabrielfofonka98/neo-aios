"""Scope enforcement module.

Provides runtime enforcement of agent scope rules, blocking actions
that are outside an agent's authorized permissions.
"""

from aios.scope.actions import ActionMapper
from aios.scope.actions import action_mapper
from aios.scope.enforcer import ActionResult
from aios.scope.enforcer import ScopeCheckResult
from aios.scope.enforcer import ScopeEnforcer
from aios.scope.enforcer import scope_enforcer

__all__ = [
    "ActionMapper",
    "ActionResult",
    "ScopeCheckResult",
    "ScopeEnforcer",
    "action_mapper",
    "scope_enforcer",
]
