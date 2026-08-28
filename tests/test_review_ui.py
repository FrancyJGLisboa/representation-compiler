from representation_compiler.extraction import ClaimProposal, ProposalBatch, ProposalStatus, apply_approved
from representation_compiler.fixtures import project_alpha
from representation_compiler.review_ui import run_review


def batch() -> ProposalBatch:
    return ProposalBatch("note", "Alpha depends on API v2. Alpha has a September launch.", [
        ClaimProposal("pr-note-1", "project-alpha", "depends_on", "API v2", "Alpha depends on API v2.", .8, "stated"),
        ClaimProposal("pr-note-2", "project-alpha", "launch_date", "September", "Alpha has a September launch.", .8, "stated"),
    ])


def scripted(*answers):
    answers = iter(answers)
    return lambda _: next(answers)


def test_review_approves_edits_and_rejects_one_at_a_time():
    proposals = batch()
    run_review(proposals, "Fran", read=scripted("e", "", "", "2026-09-15", "", "", "", "a", "r"), write=lambda _: None)
    first, second = proposals.proposals
    assert first.status is ProposalStatus.APPROVED
    assert first.object == "2026-09-15"
    assert second.status is ProposalStatus.REJECTED


def test_quit_leaves_remaining_claim_pending():
    proposals = batch()
    run_review(proposals, "Fran", read=scripted("q"), write=lambda _: None)
    assert all(item.status is ProposalStatus.PENDING for item in proposals.proposals)


def test_invalid_batch_does_not_partially_commit():
    proposals = batch()
    for proposal in proposals.proposals:
        proposal.status = ProposalStatus.APPROVED
    proposals.proposals[1].evidence_excerpt = "invented"
    model = project_alpha()
    before = len(model.assertions)
    try:
        apply_approved(model, proposals)
    except ValueError:
        pass
    assert len(model.assertions) == before
