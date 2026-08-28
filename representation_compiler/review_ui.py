"""Small terminal UI for reviewing proposed claims one at a time."""
from __future__ import annotations

from collections.abc import Callable

from .extraction import ClaimProposal, ProposalBatch, ProposalStatus, review

Read = Callable[[str], str]
Write = Callable[[str], None]
OnReview = Callable[[ClaimProposal], None]
OnChange = Callable[[ClaimProposal], None]


def edit(proposal: ClaimProposal, read: Read, write: Write) -> None:
    """Edit a pending proposal. Empty input preserves a field's current value."""
    write("Leave blank to keep the displayed value.")
    for field in ("subject", "predicate", "object", "evidence_excerpt", "confidence", "rationale"):
        current = getattr(proposal, field)
        value = read(f"{field} [{current}]: ").strip()
        if not value:
            continue
        if field == "confidence":
            try:
                value = float(value)
            except ValueError:
                write("Confidence must be a number. Kept the current value.")
                continue
            if not 0 <= value <= 1:
                write("Confidence must be from 0 to 1. Kept the current value.")
                continue
        setattr(proposal, field, value)
    write("Edited proposal remains pending. Review it again before approving.")


def _show(proposal: ClaimProposal, number: int, total: int, write: Write) -> None:
    write(f"\nProposal {number}/{total} — {proposal.id}")
    write(f"Claim: {proposal.subject} | {proposal.predicate} | {proposal.object}")
    write(f"Evidence quote: {proposal.evidence_excerpt}")
    write(f"Confidence: {proposal.confidence:.0%}")
    write(f"Why proposed: {proposal.rationale}")
    write("[a]pprove  [r]eject  [e]dit  [s]kip  [q]uit")


def run_review(batch: ProposalBatch, reviewer: str, read: Read = input, write: Write = print, on_review: OnReview | None = None, on_change: OnChange | None = None) -> ProposalBatch:
    """Review pending proposals; quit leaves all remaining proposals untouched."""
    pending = [item for item in batch.proposals if item.status is ProposalStatus.PENDING]
    for position, proposal in enumerate(pending, 1):
        while proposal.status is ProposalStatus.PENDING:
            _show(proposal, position, len(pending), write)
            decision = read("Decision: ").strip().lower()
            if decision == "a":
                review(batch, proposal.id, ProposalStatus.APPROVED, reviewer)
                if on_review:
                    on_review(proposal)
                write("Approved. It will be validated before it is committed.")
            elif decision == "r":
                review(batch, proposal.id, ProposalStatus.REJECTED, reviewer)
                if on_review:
                    on_review(proposal)
                write("Rejected. It will not be committed.")
            elif decision == "e":
                edit(proposal, read, write)
                if on_change:
                    on_change(proposal)
            elif decision == "s":
                write("Skipped. It remains pending and will not be committed.")
                break
            elif decision == "q":
                write("Review paused. No remaining proposals were changed.")
                return batch
            else:
                write("Use a, r, e, s, or q.")
    return batch
