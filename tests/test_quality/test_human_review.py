"""Tests for human review gate functionality."""

from pathlib import Path

import pytest

from aios.quality.human_review import Approval
from aios.quality.human_review import ApprovalCheckResult
from aios.quality.human_review import ApprovalRequirement
from aios.quality.human_review import ApprovalStatus
from aios.quality.human_review import ApproverRole
from aios.quality.human_review import HumanReviewGate
from aios.quality.human_review import HumanReviewResult


class TestApproverRole:
    """Tests for ApproverRole enum."""

    def test_all_roles_exist(self) -> None:
        """All expected approver roles should be defined."""
        assert ApproverRole.TECH_LEAD.value == "tech_lead"
        assert ApproverRole.MANAGER.value == "manager"
        assert ApproverRole.ARCHITECT.value == "architect"
        assert ApproverRole.SECURITY_LEAD.value == "security_lead"


class TestApprovalStatus:
    """Tests for ApprovalStatus enum."""

    def test_all_statuses_exist(self) -> None:
        """All expected approval statuses should be defined."""
        assert ApprovalStatus.PENDING.value == "pending"
        assert ApprovalStatus.APPROVED.value == "approved"
        assert ApprovalStatus.REJECTED.value == "rejected"
        assert ApprovalStatus.CHANGES_REQUESTED.value == "changes_requested"


class TestApproval:
    """Tests for Approval dataclass."""

    def test_approval_creation(self) -> None:
        """Approval should be created with all required fields."""
        from datetime import UTC
        from datetime import datetime

        approval = Approval(
            approver="john.doe",
            role=ApproverRole.TECH_LEAD,
            status=ApprovalStatus.APPROVED,
            pr_number=123,
            timestamp=datetime(2026, 2, 5, 12, 0, 0, tzinfo=UTC),
            comment="LGTM",
        )

        assert approval.approver == "john.doe"
        assert approval.role == ApproverRole.TECH_LEAD
        assert approval.status == ApprovalStatus.APPROVED
        assert approval.pr_number == 123
        assert approval.comment == "LGTM"

    def test_approval_is_frozen(self) -> None:
        """Approval should be immutable."""
        from datetime import UTC
        from datetime import datetime

        approval = Approval(
            approver="john.doe",
            role=ApproverRole.TECH_LEAD,
            status=ApprovalStatus.APPROVED,
            pr_number=123,
            timestamp=datetime.now(UTC),
        )

        with pytest.raises(AttributeError):
            approval.approver = "jane.doe"  # type: ignore[misc]


class TestApprovalRequirement:
    """Tests for ApprovalRequirement dataclass."""

    def test_requirement_creation(self) -> None:
        """ApprovalRequirement should be created with all fields."""
        req = ApprovalRequirement(
            role=ApproverRole.MANAGER,
            reason="Manager approval for sensitive paths",
            paths=("config/settings.yaml",),
            min_approvers=1,
        )

        assert req.role == ApproverRole.MANAGER
        assert req.reason == "Manager approval for sensitive paths"
        assert "config/settings.yaml" in req.paths
        assert req.min_approvers == 1

    def test_requirement_default_min_approvers(self) -> None:
        """ApprovalRequirement should default to 1 approver."""
        req = ApprovalRequirement(
            role=ApproverRole.TECH_LEAD,
            reason="Tech lead required",
            paths=("src/main.py",),
        )

        assert req.min_approvers == 1


class TestHumanReviewGate:
    """Tests for HumanReviewGate class."""

    @pytest.fixture
    def gate(self) -> HumanReviewGate:
        """Create a fresh HumanReviewGate for each test."""
        return HumanReviewGate()

    # -------------------------------------------------------------------------
    # requires_approval tests
    # -------------------------------------------------------------------------

    def test_requires_approval_always_true(self, gate: HumanReviewGate) -> None:
        """Any PR should require human review (Tech Lead always required)."""
        files = [Path("src/utils.py")]
        result = gate.requires_approval(files)

        assert result.requires_human_review is True
        assert len(result.requirements) >= 1

    def test_tech_lead_always_required(self, gate: HumanReviewGate) -> None:
        """Tech Lead approval should always be required."""
        files = [Path("src/simple_file.py")]
        result = gate.requires_approval(files)

        tech_lead_reqs = [
            r for r in result.requirements if r.role == ApproverRole.TECH_LEAD
        ]
        assert len(tech_lead_reqs) == 1
        assert "Tech Lead" in tech_lead_reqs[0].reason

    def test_sensitive_paths_require_manager(self, gate: HumanReviewGate) -> None:
        """Sensitive paths should require Manager approval."""
        sensitive_files = [
            Path("config/database.yaml"),
            Path(".env.production"),
            Path("credentials.json"),
        ]

        for file_path in sensitive_files:
            result = gate.requires_approval([file_path])
            manager_reqs = [
                r for r in result.requirements if r.role == ApproverRole.MANAGER
            ]
            assert len(manager_reqs) == 1, f"Manager should be required for {file_path}"
            assert str(file_path) in result.sensitive_paths_found

    def test_pyproject_requires_manager(self, gate: HumanReviewGate) -> None:
        """pyproject.toml should require Manager approval."""
        files = [Path("pyproject.toml")]
        result = gate.requires_approval(files)

        manager_reqs = [
            r for r in result.requirements if r.role == ApproverRole.MANAGER
        ]
        assert len(manager_reqs) == 1

    def test_security_paths_require_security_lead(
        self, gate: HumanReviewGate
    ) -> None:
        """Security paths should require Security Lead review."""
        security_files = [
            Path("src/aios/security/validators.py"),
            Path("auth/handlers.py"),
        ]

        for file_path in security_files:
            result = gate.requires_approval([file_path])
            security_reqs = [
                r
                for r in result.requirements
                if r.role == ApproverRole.SECURITY_LEAD
            ]
            assert (
                len(security_reqs) == 1
            ), f"Security Lead should be required for {file_path}"

    def test_architecture_paths_require_architect(
        self, gate: HumanReviewGate
    ) -> None:
        """Architecture paths should require Architect review."""
        arch_files = [
            Path("src/aios/agents/models.py"),
            Path("src/aios/core/engine.py"),
        ]

        for file_path in arch_files:
            result = gate.requires_approval([file_path])
            arch_reqs = [
                r for r in result.requirements if r.role == ApproverRole.ARCHITECT
            ]
            assert (
                len(arch_reqs) == 1
            ), f"Architect should be required for {file_path}"

    def test_large_changes_require_two_approvers(
        self, gate: HumanReviewGate
    ) -> None:
        """Changes over 500 lines should require 2 Tech Lead approvers."""
        files = [Path("src/big_refactor.py")]
        result = gate.requires_approval(files, lines_changed=600)

        tech_lead_reqs = [
            r for r in result.requirements if r.role == ApproverRole.TECH_LEAD
        ]
        assert len(tech_lead_reqs) == 1
        assert tech_lead_reqs[0].min_approvers == 2
        assert "500 lines" in tech_lead_reqs[0].reason

    def test_exactly_threshold_not_large(self, gate: HumanReviewGate) -> None:
        """Exactly 500 lines should NOT trigger 2-approver requirement."""
        files = [Path("src/file.py")]
        result = gate.requires_approval(files, lines_changed=500)

        tech_lead_reqs = [
            r for r in result.requirements if r.role == ApproverRole.TECH_LEAD
        ]
        assert tech_lead_reqs[0].min_approvers == 1

    def test_multiple_requirements_combined(self, gate: HumanReviewGate) -> None:
        """A PR can have multiple types of requirements."""
        files = [
            Path("config/settings.yaml"),  # Manager
            Path("src/aios/security/auth.py"),  # Security Lead + Sensitive
            Path("src/aios/agents/core.py"),  # Architect
        ]

        result = gate.requires_approval(files, lines_changed=600)

        roles_required = {r.role for r in result.requirements}
        assert ApproverRole.TECH_LEAD in roles_required
        assert ApproverRole.MANAGER in roles_required
        assert ApproverRole.SECURITY_LEAD in roles_required
        assert ApproverRole.ARCHITECT in roles_required

    def test_reasons_populated(self, gate: HumanReviewGate) -> None:
        """Result should contain human-readable reasons."""
        files = [Path("config/db.yaml")]
        result = gate.requires_approval(files)

        assert len(result.reasons) >= 2  # Tech Lead + Manager
        assert any("Tech Lead" in r for r in result.reasons)
        assert any("Manager" in r for r in result.reasons)

    # -------------------------------------------------------------------------
    # get_required_approvers tests
    # -------------------------------------------------------------------------

    def test_get_required_approvers_basic(self, gate: HumanReviewGate) -> None:
        """Should return list of required approver roles."""
        files = [Path("src/utils.py")]
        roles = gate.get_required_approvers(files)

        assert ApproverRole.TECH_LEAD in roles

    def test_get_required_approvers_includes_duplicates(
        self, gate: HumanReviewGate
    ) -> None:
        """Large changes should include Tech Lead twice."""
        files = [Path("src/big_file.py")]
        roles = gate.get_required_approvers(files, lines_changed=600)

        tech_lead_count = roles.count(ApproverRole.TECH_LEAD)
        assert tech_lead_count == 2

    # -------------------------------------------------------------------------
    # record_approval tests
    # -------------------------------------------------------------------------

    def test_record_approval_basic(self, gate: HumanReviewGate) -> None:
        """Should record an approval and return it."""
        approval = gate.record_approval(
            approver="alice",
            role=ApproverRole.TECH_LEAD,
            pr_number=42,
        )

        assert approval.approver == "alice"
        assert approval.role == ApproverRole.TECH_LEAD
        assert approval.pr_number == 42
        assert approval.status == ApprovalStatus.APPROVED

    def test_record_approval_with_comment(self, gate: HumanReviewGate) -> None:
        """Should record approval with optional comment."""
        approval = gate.record_approval(
            approver="bob",
            role=ApproverRole.MANAGER,
            pr_number=42,
            comment="Approved with reservations",
        )

        assert approval.comment == "Approved with reservations"

    def test_record_approval_with_status(self, gate: HumanReviewGate) -> None:
        """Should record approval with custom status."""
        approval = gate.record_approval(
            approver="carol",
            role=ApproverRole.TECH_LEAD,
            pr_number=42,
            status=ApprovalStatus.CHANGES_REQUESTED,
        )

        assert approval.status == ApprovalStatus.CHANGES_REQUESTED

    def test_record_multiple_approvals(self, gate: HumanReviewGate) -> None:
        """Should store multiple approvals for same PR."""
        gate.record_approval("alice", ApproverRole.TECH_LEAD, 42)
        gate.record_approval("bob", ApproverRole.MANAGER, 42)

        approvals = gate.get_approvals(42)
        assert len(approvals) == 2

    # -------------------------------------------------------------------------
    # check_approvals tests
    # -------------------------------------------------------------------------

    def test_check_approvals_no_approvals(self, gate: HumanReviewGate) -> None:
        """PR without approvals should not be approved."""
        files = [Path("src/file.py")]
        result = gate.check_approvals(pr_number=42, files=files)

        assert result.is_approved is False
        assert len(result.missing_requirements) >= 1

    def test_check_approvals_with_tech_lead(self, gate: HumanReviewGate) -> None:
        """PR with Tech Lead approval should be approved for simple files."""
        gate.record_approval("alice", ApproverRole.TECH_LEAD, 42)

        files = [Path("src/simple.py")]
        result = gate.check_approvals(pr_number=42, files=files)

        assert result.is_approved is True
        assert len(result.missing_requirements) == 0

    def test_check_approvals_missing_manager(self, gate: HumanReviewGate) -> None:
        """PR with sensitive paths needs Manager approval too."""
        gate.record_approval("alice", ApproverRole.TECH_LEAD, 42)

        files = [Path("config/settings.yaml")]
        result = gate.check_approvals(pr_number=42, files=files)

        assert result.is_approved is False
        missing_roles = {r.role for r in result.missing_requirements}
        assert ApproverRole.MANAGER in missing_roles

    def test_check_approvals_all_requirements_met(
        self, gate: HumanReviewGate
    ) -> None:
        """PR with all required approvals should be approved."""
        gate.record_approval("alice", ApproverRole.TECH_LEAD, 42)
        gate.record_approval("bob", ApproverRole.MANAGER, 42)
        gate.record_approval("carol", ApproverRole.SECURITY_LEAD, 42)

        files = [
            Path("config/db.yaml"),
            Path("src/aios/security/auth.py"),
        ]
        result = gate.check_approvals(pr_number=42, files=files)

        assert result.is_approved is True

    def test_check_approvals_rejected_not_counted(
        self, gate: HumanReviewGate
    ) -> None:
        """Rejected approvals should not count toward requirements."""
        gate.record_approval(
            "alice",
            ApproverRole.TECH_LEAD,
            42,
            status=ApprovalStatus.REJECTED,
        )

        files = [Path("src/file.py")]
        result = gate.check_approvals(pr_number=42, files=files)

        assert result.is_approved is False

    def test_check_approvals_changes_requested_not_counted(
        self, gate: HumanReviewGate
    ) -> None:
        """Changes requested should not count as approval."""
        gate.record_approval(
            "alice",
            ApproverRole.TECH_LEAD,
            42,
            status=ApprovalStatus.CHANGES_REQUESTED,
        )

        files = [Path("src/file.py")]
        result = gate.check_approvals(pr_number=42, files=files)

        assert result.is_approved is False

    def test_check_approvals_large_change_needs_two(
        self, gate: HumanReviewGate
    ) -> None:
        """Large changes need 2 Tech Lead approvals."""
        gate.record_approval("alice", ApproverRole.TECH_LEAD, 42)

        files = [Path("src/big.py")]
        result = gate.check_approvals(pr_number=42, files=files, lines_changed=600)

        assert result.is_approved is False
        missing = [
            r for r in result.missing_requirements if r.role == ApproverRole.TECH_LEAD
        ]
        assert len(missing) == 1

    def test_check_approvals_large_change_with_two_tech_leads(
        self, gate: HumanReviewGate
    ) -> None:
        """Large changes pass with 2 Tech Lead approvals."""
        gate.record_approval("alice", ApproverRole.TECH_LEAD, 42)
        gate.record_approval("bob", ApproverRole.TECH_LEAD, 42)

        files = [Path("src/big.py")]
        result = gate.check_approvals(pr_number=42, files=files, lines_changed=600)

        assert result.is_approved is True

    # -------------------------------------------------------------------------
    # get_approvals tests
    # -------------------------------------------------------------------------

    def test_get_approvals_empty(self, gate: HumanReviewGate) -> None:
        """Should return empty list for PR without approvals."""
        approvals = gate.get_approvals(99)
        assert approvals == []

    def test_get_approvals_returns_copy(self, gate: HumanReviewGate) -> None:
        """Should return a copy, not the internal list."""
        gate.record_approval("alice", ApproverRole.TECH_LEAD, 42)
        approvals = gate.get_approvals(42)
        approvals.clear()

        # Original should still have the approval
        assert len(gate.get_approvals(42)) == 1

    # -------------------------------------------------------------------------
    # clear_approvals tests
    # -------------------------------------------------------------------------

    def test_clear_approvals(self, gate: HumanReviewGate) -> None:
        """Should remove all approvals for a PR."""
        gate.record_approval("alice", ApproverRole.TECH_LEAD, 42)
        gate.record_approval("bob", ApproverRole.MANAGER, 42)

        gate.clear_approvals(42)

        assert gate.get_approvals(42) == []

    def test_clear_approvals_nonexistent_pr(self, gate: HumanReviewGate) -> None:
        """Should not raise error for PR without approvals."""
        gate.clear_approvals(999)  # Should not raise


class TestHumanReviewResult:
    """Tests for HumanReviewResult dataclass."""

    def test_result_creation(self) -> None:
        """HumanReviewResult should be created with all fields."""
        result = HumanReviewResult(
            requires_human_review=True,
            requirements=[
                ApprovalRequirement(
                    role=ApproverRole.TECH_LEAD,
                    reason="Required",
                    paths=("src/file.py",),
                )
            ],
            total_lines_changed=100,
            sensitive_paths_found=["config/db.yaml"],
            reasons=["Tech Lead required"],
        )

        assert result.requires_human_review is True
        assert len(result.requirements) == 1
        assert result.total_lines_changed == 100


class TestApprovalCheckResult:
    """Tests for ApprovalCheckResult dataclass."""

    def test_result_creation(self) -> None:
        """ApprovalCheckResult should be created with all fields."""
        result = ApprovalCheckResult(
            is_approved=True,
            approvals=[],
            missing_requirements=[],
            met_requirements=[],
        )

        assert result.is_approved is True
        assert result.approvals == []


class TestGlobalInstance:
    """Tests for the global human_review_gate instance."""

    def test_global_instance_exists(self) -> None:
        """Global instance should be importable."""
        from aios.quality.human_review import human_review_gate

        assert isinstance(human_review_gate, HumanReviewGate)
