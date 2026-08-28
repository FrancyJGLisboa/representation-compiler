"""LLM extraction boundary: models propose; a human approves; validators commit."""
from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from typing import Protocol

from .model import Assertion, CanonicalModel, Evidence, Origin


class ProposalStatus(StrEnum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


@dataclass
class ClaimProposal:
    id: str
    subject: str
    predicate: str
    object: str
    evidence_excerpt: str
    confidence: float
    rationale: str
    status: ProposalStatus = ProposalStatus.PENDING
    reviewer: str | None = None
    reviewed_at: str | None = None


@dataclass
class ProposalBatch:
    source_id: str
    source_text: str
    proposals: list[ClaimProposal] = field(default_factory=list)
    entities: list[dict[str, str]] = field(default_factory=list)


class ExtractionClient(Protocol):
    def extract(self, source_id: str, source_text: str, entities: list[dict[str, str]]) -> ProposalBatch: ...


EXTRACTION_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "claims": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "subject": {"type": "string"}, "predicate": {"type": "string"},
                    "object": {"type": "string"}, "evidence_excerpt": {"type": "string"},
                    "confidence": {"type": "number"}, "rationale": {"type": "string"},
                },
                "required": ["subject", "predicate", "object", "evidence_excerpt", "confidence", "rationale"],
            },
        },
    },
    "required": ["claims"],
}


class OpenAIResponsesExtractor:
    """OpenAI implementation; importing the SDK is deferred until it is actually used."""
    def __init__(self, model: str):
        self.model = model

    def extract(self, source_id: str, source_text: str, entities: list[dict[str, str]]) -> ProposalBatch:
        if not os.environ.get("OPENAI_API_KEY"):
            raise RuntimeError("OPENAI_API_KEY is required to call the OpenAI extractor")
        try:
            from openai import OpenAI
        except ImportError as error:
            raise RuntimeError("Install the optional OpenAI client: python3 -m pip install openai") from error
        allowed = ", ".join(f"{item['id']} ({item['name']})" for item in entities)
        response = OpenAI().responses.create(
            model=self.model,
            store=False,
            instructions=(
                "Extract only explicit, operationally useful claims. Return a claim only if its evidence_excerpt "
                "is an exact, contiguous quote from the supplied source. Use an allowed entity ID as subject. "
                "Do not resolve disagreement or invent missing facts. These are proposals for human review."
            ),
            input=f"Allowed entities: {allowed}\n\nSource ({source_id}):\n{source_text}",
            text={"format": {"type": "json_schema", "name": "claim_proposals", "strict": True, "schema": EXTRACTION_SCHEMA}},
        )
        payload = json.loads(response.output_text)
        return _batch_from_payload(source_id, source_text, payload)


def _batch_from_payload(source_id: str, source_text: str, payload: dict) -> ProposalBatch:
    proposals = []
    for index, item in enumerate(payload.get("claims", []), 1):
        proposals.append(ClaimProposal(
            id=f"pr-{source_id}-{index}", subject=item["subject"], predicate=item["predicate"], object=item["object"],
            evidence_excerpt=item["evidence_excerpt"], confidence=float(item["confidence"]), rationale=item["rationale"],
        ))
    return ProposalBatch(source_id, source_text, proposals)


def batch_from_agent_file(payload: dict) -> ProposalBatch:
    """Accept proposals produced by a host agent subscription, not an API call.

    The host agent is still constrained by the same source-grounding and human-review
    gates used by the API adapter.
    """
    source_id = payload.get("source_id")
    source_text = payload.get("source_text")
    if not isinstance(source_id, str) or not source_id.strip() or not isinstance(source_text, str) or not source_text.strip():
        raise ValueError("proposal file requires non-empty source_id and source_text")
    entities = payload.get("entities", [])
    if not all(isinstance(item, dict) and all(isinstance(item.get(field), str) and item[field].strip() for field in ("id", "name", "type")) for item in entities):
        raise ValueError("entities must contain id, name, and type strings")
    batch = _batch_from_payload(source_id, source_text, {"claims": payload.get("claims", [])})
    batch.entities = entities
    return batch


def review(batch: ProposalBatch, proposal_id: str, decision: ProposalStatus, reviewer: str) -> None:
    if decision not in {ProposalStatus.APPROVED, ProposalStatus.REJECTED}:
        raise ValueError("review decision must be approved or rejected")
    proposal = next((item for item in batch.proposals if item.id == proposal_id), None)
    if proposal is None:
        raise KeyError(f"unknown proposal {proposal_id}")
    proposal.status, proposal.reviewer, proposal.reviewed_at = decision, reviewer, datetime.now(UTC).isoformat()


def apply_approved(model: CanonicalModel, batch: ProposalBatch) -> list[str]:
    """Only approved, source-grounded proposals enter the canonical model."""
    approved = [item for item in batch.proposals if item.status is ProposalStatus.APPROVED]
    # Validate the complete batch before changing the model: no partial commits.
    for proposal in approved:
        if proposal.subject not in model.entities:
            raise ValueError(f"{proposal.id}: unknown subject {proposal.subject}")
        if not 0 <= proposal.confidence <= 1:
            raise ValueError(f"{proposal.id}: confidence must be between 0 and 1")
        if not proposal.evidence_excerpt or proposal.evidence_excerpt not in batch.source_text:
            raise ValueError(f"{proposal.id}: evidence must be an exact source excerpt")
        safe_id = re.sub(r"[^a-z0-9]+", "-", proposal.id.lower()).strip("-")
        evidence_id, assertion_id = f"ev-{safe_id}", f"as-{safe_id}"
        if assertion_id in model.assertions:
            raise ValueError(f"{proposal.id}: already applied")
    created = []
    for proposal in approved:
        safe_id = re.sub(r"[^a-z0-9]+", "-", proposal.id.lower()).strip("-")
        evidence_id, assertion_id = f"ev-{safe_id}", f"as-{safe_id}"
        model.evidence[evidence_id] = Evidence(evidence_id, batch.source_id, proposal.evidence_excerpt, "llm-proposal", proposal.reviewed_at or "")
        model.assertions[assertion_id] = Assertion(
            assertion_id, proposal.subject, proposal.predicate, proposal.object, proposal.reviewed_at or "",
            proposal.reviewer or "human-review", proposal.confidence, "shared", Origin.INFERRED, (evidence_id,)
        )
        created.append(assertion_id)
    model.validate()
    return created
