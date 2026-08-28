import pytest

from representation_compiler.extraction import (
    ClaimProposal,
    ProposalBatch,
    ProposalStatus,
    apply_approved,
    review,
)
from representation_compiler.fixtures import project_alpha


def proposal_batch() -> ProposalBatch:
    return ProposalBatch("meeting", "Project Alpha will ship after API v2 is ready.", [
        ClaimProposal("pr-meeting-1", "project-alpha", "depends_on", "API v2", "API v2 is ready", .9, "Explicit dependency"),
    ])


def test_pending_proposals_cannot_change_truth_model():
    model, batch = project_alpha(), proposal_batch()
    assert apply_approved(model, batch) == []
    assert all(item.id != "as-pr-meeting-1" for item in model.assertions.values())


def test_approval_then_validation_commits_grounded_claim():
    model, batch = project_alpha(), proposal_batch()
    review(batch, "pr-meeting-1", ProposalStatus.APPROVED, "Fran")
    created = apply_approved(model, batch)
    assert created == ["as-pr-meeting-1"]
    assert model.assertions[created[0]].asserted_by == "Fran"


def test_approval_rejects_hallucinated_evidence():
    model, batch = project_alpha(), proposal_batch()
    batch.proposals[0].evidence_excerpt = "not in source"
    review(batch, "pr-meeting-1", ProposalStatus.APPROVED, "Fran")
    with pytest.raises(ValueError, match="exact source excerpt"):
        apply_approved(model, batch)


def test_review_requires_a_real_human_decision():
    with pytest.raises(ValueError, match="approved or rejected"):
        review(proposal_batch(), "pr-meeting-1", ProposalStatus.PENDING, "Fran")
