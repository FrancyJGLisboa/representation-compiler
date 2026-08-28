"""Single source of truth for structural representations and their visual projections."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RepresentationDefinition:
    id: str
    visual_id: str
    name: str
    purpose: str
    columns: tuple[str, ...]
    keywords: tuple[str, ...]
    definition: str
    primitive_change: str
    mapping: str
    preserved: tuple[str, ...]
    discarded: tuple[str, ...]
    makes_easier: tuple[str, ...]
    falsification_test: str


CATALOG = (
    RepresentationDefinition("event-trajectory", "timeline", "Timeline", "What changed over time", ("time", "subject", "claim", "evidence"), ("changed", "time", "when", "history", "over time"), "Represent reality as dated state changes rather than a document sequence.", "Events and validity intervals", "Assertions → ordered changes", ("time", "supersession", "sequence"), ("cross-team topology",), ("what changed", "when did this become true"), "Remove dates and ask a reviewer to reconstruct the sequence. If accuracy is unchanged, the timeline adds no value."),
    RepresentationDefinition("dependency-network", "dependency-map", "Dependency Map", "Blockers and dependencies", ("subject", "dependency", "impact", "evidence"), ("late", "blocked", "dependency", "why", "unblock"), "Represent the situation as prerequisites and downstream consequences.", "Nodes and directed dependency edges", "dependency assertions → graph edges", ("blockers", "fan-in", "downstream impact"), ("fine-grained chronology",), ("what blocks progress", "what to unblock first"), "Delete the highest-centrality dependency. If the recommended action does not change, centrality is not decision-relevant."),
    RepresentationDefinition("perspective-model", "contradiction-matrix", "Contradiction Matrix", "Where perspectives disagree", ("subject", "claim", "perspective", "confidence", "evidence"), ("disagree", "conflict", "contradict", "different"), "Represent claims as perspective-bound assertions that may coexist.", "Perspective, claim, contradiction relation", "assertions → perspective lanes", ("disagreement", "confidence", "provenance"), ("false consensus",), ("where teams disagree", "which claim needs resolution"), "Hide perspective labels. If readers still identify the disputed claim reliably, perspective separation is unnecessary."),
    RepresentationDefinition("state-machine", "state-transition", "State Transition", "How the system changes state", ("subject", "state", "trigger", "evidence"), ("state", "next", "status", "risk"), "Represent work as states and guarded transitions, not a static health label.", "State, transition, trigger", "status assertions → state transitions", ("current state", "allowed next states", "transition triggers"), ("incidental wording",), ("what changed state", "what must happen next"), "Ask whether every transition has evidence and a trigger. If not, treat the state machine as a hypothesis, not a fact."),
    RepresentationDefinition("causal-hypothesis", "causal-map", "Causal Map", "Why something happened", ("cause", "effect", "mechanism", "evidence"), ("cause", "why", "impact", "because"), "Represent proposed causes separately from observations and test their links.", "Cause, effect, mechanism, confounder", "claims → causal edges with confidence", ("mechanism", "intervention points", "uncertainty"), ("correlation mistaken for cause",), ("why it happened", "what intervention could work"), "For each causal edge, name an observation that would falsify it. Unfalsifiable links must be labelled assumptions."),
    RepresentationDefinition("decision-ledger", "decision-ledger", "Decision Ledger", "Decisions, owners, and status", ("subject", "decision", "owner", "status", "evidence"), ("decision", "decide", "executive", "attention", "action", "should"), "Represent the situation as decisions, alternatives, owners, and evidence.", "Decision, option, owner, consequence", "claims → decision records", ("accountability", "open choices", "rationale"), ("narrative detail unrelated to choice",), ("what should we decide", "who owns the next action"), "Remove the proposed owner or consequence. If action remains equally clear, the ledger is not adding operational value."),
    RepresentationDefinition("claim-evidence", "claim-evidence", "Claim / Evidence Table", "Traceable factual review", ("subject", "claim", "origin", "confidence", "evidence"), ("evidence", "prove", "explain"), "Represent the subject as claims and the evidence supporting or contradicting them.", "Claim, evidence, confidence", "assertions → evidence matrix", ("traceability", "uncertainty"), ("spatial or temporal structure",), ("what supports this", "what can I verify"), "Hide source locators. If a reviewer can still audit important claims, provenance is not carrying useful information."),
)


def by_visual_id(visual_id: str) -> RepresentationDefinition | None:
    return next((item for item in CATALOG if item.visual_id == visual_id), None)
