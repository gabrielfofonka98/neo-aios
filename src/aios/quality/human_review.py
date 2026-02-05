"""Human review layer for quality gates.

This module provides the HumanReviewGate class that enforces human review
requirements for code changes, including Tech Lead sign-off, Manager approval
for sensitive paths, and multi-approver requirements for large changes.

Example:
    >>> from pathlib import Path
    >>> from aios.quality.human_review import HumanReviewGate, ApproverRole
    >>>
    >>> gate = HumanReviewGate()
    >>> files = [Path("src/aios/security/validators.py")]
    >>> result = gate.requires_approval(files)
    >>> result.requires_human_review
    True
"""

from dataclasses import dataclass
from dataclasses import field
from datetime import UTC
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Final


class ApproverRole(Enum):
    """Role of an approver in the review process.

    Attributes:
        TECH_LEAD: Technical lead, required for all PRs.
        MANAGER: Manager, required for sensitive paths.
        ARCHITECT: Architect, required for architecture changes.
        SECURITY_LEAD: Security lead, required for security changes.
    """

    TECH_LEAD = "tech_lead"
    MANAGER = "manager"
    ARCHITECT = "architect"
    SECURITY_LEAD = "security_lead"


class ApprovalStatus(Enum):
    """Status of an approval.

    Attributes:
        PENDING: Approval not yet given.
        APPROVED: Approval granted.
        REJECTED: Approval denied.
        CHANGES_REQUESTED: Approver requested changes.
    """

    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    CHANGES_REQUESTED = "changes_requested"


@dataclass(frozen=True)
class Approval:
    """Record of an approval given by a reviewer.

    Attributes:
        approver: Username or ID of the approver.
        role: The ApproverRole of the approver.
        status: Current approval status.
        pr_number: PR number this approval is for.
        timestamp: When the approval was recorded.
        comment: Optional comment from the approver.
    """

    approver: str
    role: ApproverRole
    status: ApprovalStatus
    pr_number: int
    timestamp: datetime
    comment: str | None = None


@dataclass(frozen=True)
class ApprovalRequirement:
    """A requirement for approval.

    Attributes:
        role: The role required to approve.
        reason: Why this approval is required.
        paths: List of paths that triggered this requirement.
        min_approvers: Minimum number of approvers with this role.
    """

    role: ApproverRole
    reason: str
    paths: tuple[str, ...]
    min_approvers: int = 1


@dataclass
class HumanReviewResult:
    """Result of human review gate check.

    Attributes:
        requires_human_review: Whether human review is required.
        requirements: List of approval requirements.
        total_lines_changed: Total lines changed in the PR.
        sensitive_paths_found: List of sensitive paths found.
        reasons: List of reasons why review is required.
    """

    requires_human_review: bool
    requirements: list[ApprovalRequirement] = field(default_factory=list)
    total_lines_changed: int = 0
    sensitive_paths_found: list[str] = field(default_factory=list)
    reasons: list[str] = field(default_factory=list)


@dataclass
class ApprovalCheckResult:
    """Result of checking if a PR has sufficient approvals.

    Attributes:
        is_approved: Whether all requirements are met.
        approvals: List of approvals received.
        missing_requirements: Requirements not yet fulfilled.
        met_requirements: Requirements that have been fulfilled.
    """

    is_approved: bool
    approvals: list[Approval] = field(default_factory=list)
    missing_requirements: list[ApprovalRequirement] = field(default_factory=list)
    met_requirements: list[ApprovalRequirement] = field(default_factory=list)


class HumanReviewGate:
    """Gate that enforces human review requirements.

    This class determines what human approvals are needed for a set of
    changed files based on:
    1. All PRs require Tech Lead sign-off
    2. Sensitive paths require Manager approval
    3. Large changes (>500 lines) require 2 approvers

    Attributes:
        SENSITIVE_PATH_PATTERNS: Patterns for paths requiring manager approval.
        ARCHITECTURE_PATH_PATTERNS: Patterns for paths requiring architect review.
        SECURITY_PATH_PATTERNS: Patterns for paths requiring security lead review.
        LARGE_CHANGE_THRESHOLD: Number of lines that triggers 2-approver requirement.
    """

    SENSITIVE_PATH_PATTERNS: Final[tuple[str, ...]] = (
        "config/",
        ".env",
        "credentials",
        "pyproject.toml",
        "setup.py",
        "setup.cfg",
        "requirements.txt",
        "poetry.lock",
        "uv.lock",
    )

    ARCHITECTURE_PATH_PATTERNS: Final[tuple[str, ...]] = (
        "src/aios/agents/",
        "src/aios/core/",
        ".aios-core/",
        "agents/",
    )

    SECURITY_PATH_PATTERNS: Final[tuple[str, ...]] = (
        "src/aios/security/",
        "security/",
        "auth/",
        "authentication/",
        "authorization/",
    )

    LARGE_CHANGE_THRESHOLD: Final[int] = 500

    def __init__(self) -> None:
        """Initialize the HumanReviewGate with empty approval storage."""
        self._approvals: dict[int, list[Approval]] = {}

    def requires_approval(
        self,
        files: list[Path],
        lines_changed: int = 0,
    ) -> HumanReviewResult:
        """Check if the given files require human approval.

        Args:
            files: List of file paths that have been changed.
            lines_changed: Total number of lines changed (optional).

        Returns:
            HumanReviewResult with details about required approvals.
        """
        requirements: list[ApprovalRequirement] = []
        sensitive_paths: list[str] = []
        reasons: list[str] = []

        # Rule 1: Tech Lead sign-off always required
        requirements.append(
            ApprovalRequirement(
                role=ApproverRole.TECH_LEAD,
                reason="Tech Lead sign-off required for all PRs",
                paths=tuple(str(f) for f in files),
                min_approvers=1,
            )
        )
        reasons.append("Tech Lead sign-off required for all PRs")

        # Rule 2: Check for sensitive paths -> Manager approval
        manager_paths = self._find_matching_paths(
            files, self.SENSITIVE_PATH_PATTERNS
        )
        if manager_paths:
            sensitive_paths.extend(manager_paths)
            requirements.append(
                ApprovalRequirement(
                    role=ApproverRole.MANAGER,
                    reason="Manager approval required for sensitive paths",
                    paths=tuple(manager_paths),
                    min_approvers=1,
                )
            )
            reasons.append(
                f"Manager approval required: sensitive paths modified ({', '.join(manager_paths[:3])})"
            )

        # Rule 3: Check for architecture paths -> Architect review
        arch_paths = self._find_matching_paths(
            files, self.ARCHITECTURE_PATH_PATTERNS
        )
        if arch_paths:
            requirements.append(
                ApprovalRequirement(
                    role=ApproverRole.ARCHITECT,
                    reason="Architect review required for architecture changes",
                    paths=tuple(arch_paths),
                    min_approvers=1,
                )
            )
            reasons.append(
                f"Architect review required: architecture paths modified ({', '.join(arch_paths[:3])})"
            )

        # Rule 4: Check for security paths -> Security Lead review
        security_paths = self._find_matching_paths(
            files, self.SECURITY_PATH_PATTERNS
        )
        if security_paths:
            sensitive_paths.extend(security_paths)
            requirements.append(
                ApprovalRequirement(
                    role=ApproverRole.SECURITY_LEAD,
                    reason="Security Lead review required for security changes",
                    paths=tuple(security_paths),
                    min_approvers=1,
                )
            )
            reasons.append(
                f"Security Lead review required: security paths modified ({', '.join(security_paths[:3])})"
            )

        # Rule 5: Large changes require 2 approvers
        if lines_changed > self.LARGE_CHANGE_THRESHOLD:
            # Upgrade Tech Lead requirement to 2 approvers
            requirements[0] = ApprovalRequirement(
                role=ApproverRole.TECH_LEAD,
                reason=(
                    f"2 Tech Lead approvers required for large changes "
                    f"(>{self.LARGE_CHANGE_THRESHOLD} lines)"
                ),
                paths=tuple(str(f) for f in files),
                min_approvers=2,
            )
            reasons.append(
                f"2 approvers required: {lines_changed} lines changed "
                f"(threshold: {self.LARGE_CHANGE_THRESHOLD})"
            )

        return HumanReviewResult(
            requires_human_review=True,  # Always true as Tech Lead is always required
            requirements=requirements,
            total_lines_changed=lines_changed,
            sensitive_paths_found=sensitive_paths,
            reasons=reasons,
        )

    def get_required_approvers(
        self,
        files: list[Path],
        lines_changed: int = 0,
    ) -> list[ApproverRole]:
        """Get list of required approver roles for the given files.

        Args:
            files: List of file paths that have been changed.
            lines_changed: Total number of lines changed (optional).

        Returns:
            List of ApproverRole values representing required reviewers.
        """
        result = self.requires_approval(files, lines_changed)
        roles: list[ApproverRole] = []

        for req in result.requirements:
            # Add role multiple times if min_approvers > 1
            for _ in range(req.min_approvers):
                roles.append(req.role)

        return roles

    def record_approval(
        self,
        approver: str,
        role: ApproverRole,
        pr_number: int,
        status: ApprovalStatus = ApprovalStatus.APPROVED,
        comment: str | None = None,
    ) -> Approval:
        """Record an approval for a PR.

        Args:
            approver: Username or ID of the approver.
            role: The ApproverRole of the approver.
            pr_number: PR number being approved.
            status: Approval status (default: APPROVED).
            comment: Optional comment from the approver.

        Returns:
            The Approval record created.
        """
        approval = Approval(
            approver=approver,
            role=role,
            status=status,
            pr_number=pr_number,
            timestamp=datetime.now(UTC),
            comment=comment,
        )

        if pr_number not in self._approvals:
            self._approvals[pr_number] = []

        self._approvals[pr_number].append(approval)
        return approval

    def check_approvals(
        self,
        pr_number: int,
        files: list[Path],
        lines_changed: int = 0,
    ) -> ApprovalCheckResult:
        """Check if a PR has sufficient approvals.

        Args:
            pr_number: PR number to check.
            files: List of file paths changed in the PR.
            lines_changed: Total number of lines changed.

        Returns:
            ApprovalCheckResult with details about approval status.
        """
        review_result = self.requires_approval(files, lines_changed)
        approvals = self._approvals.get(pr_number, [])

        # Only count approved approvals
        valid_approvals = [
            a for a in approvals if a.status == ApprovalStatus.APPROVED
        ]

        met_requirements: list[ApprovalRequirement] = []
        missing_requirements: list[ApprovalRequirement] = []

        for requirement in review_result.requirements:
            # Count approvals matching this role
            matching_approvals = [
                a for a in valid_approvals if a.role == requirement.role
            ]

            if len(matching_approvals) >= requirement.min_approvers:
                met_requirements.append(requirement)
            else:
                missing_requirements.append(requirement)

        return ApprovalCheckResult(
            is_approved=len(missing_requirements) == 0,
            approvals=approvals,
            missing_requirements=missing_requirements,
            met_requirements=met_requirements,
        )

    def get_approvals(self, pr_number: int) -> list[Approval]:
        """Get all approvals for a PR.

        Args:
            pr_number: PR number to get approvals for.

        Returns:
            List of Approval records for the PR.
        """
        return self._approvals.get(pr_number, []).copy()

    def clear_approvals(self, pr_number: int) -> None:
        """Clear all approvals for a PR.

        Args:
            pr_number: PR number to clear approvals for.
        """
        if pr_number in self._approvals:
            del self._approvals[pr_number]

    def _find_matching_paths(
        self,
        files: list[Path],
        patterns: tuple[str, ...],
    ) -> list[str]:
        """Find files matching any of the given patterns.

        Args:
            files: List of file paths to check.
            patterns: Tuple of path patterns to match against.

        Returns:
            List of file paths (as strings) that match any pattern.
        """
        matching: list[str] = []
        for file_path in files:
            path_str = str(file_path)
            for pattern in patterns:
                if pattern in path_str:
                    matching.append(path_str)
                    break
        return matching


# Global instance for convenience
human_review_gate = HumanReviewGate()
