"""Representation discovery: score catalogued structural models, not cosmetic variants."""
from __future__ import annotations

from dataclasses import asdict, dataclass

from .model import CanonicalModel
from .representation_catalog import CATALOG


@dataclass(frozen=True)
class RepresentationCandidate:
    id: str; family: str; definition: str; primitive_change: str; mapping: str
    preserved: tuple[str, ...]; discarded: tuple[str, ...]; makes_easier: tuple[str, ...]
    falsification_test: str; components: dict[str, float]; score: float

    def to_dict(self) -> dict:
        return asdict(self)


def _fit(identifier: str, model: CanonicalModel, temporal: float, contradictions: int) -> float:
    if identifier == "event-trajectory": return temporal
    if identifier == "perspective-model": return min(1.0, .35 + contradictions / 2)
    if identifier == "dependency-network": return min(1.0, .35 + sum(a.predicate in {"depends_on", "blocked_by"} for a in model.assertions.values()) / 2)
    if identifier == "state-machine": return min(1.0, .35 + sum(a.predicate in {"health", "status", "state"} for a in model.assertions.values()) / 2)
    return .45 if identifier == "causal-hypothesis" and len(model.assertions) > 2 else (.2 if identifier == "causal-hypothesis" else .55 if identifier == "decision-ledger" else .45)


def discover(model: CanonicalModel, objective: str, limit: int = 5) -> list[RepresentationCandidate]:
    """Return structurally distinct catalog entries, each with a falsification test."""
    model.validate()
    text, count = objective.lower(), max(1, len(model.assertions))
    provenance = sum(bool(item.evidence_ids) for item in model.assertions.values()) / count
    contradictions = sum(len(item.relations.get("contradicts", ())) for item in model.assertions.values())
    temporal = sum(bool(item.valid_from or item.asserted_at) for item in model.assertions.values()) / count
    results = []
    for definition in CATALOG:
        keyword_fit, structural_fit = min(1.0, sum(term in text for term in definition.keywords) / 2), _fit(definition.id, model, temporal, contradictions)
        answerability, compression = min(1.0, .2 + keyword_fit + structural_fit / 2), min(1.0, .35 + count / 16)
        cognitive_cost = .35 if definition.id in {"event-trajectory", "decision-ledger"} else .55
        utility = min(1.0, (answerability + provenance + structural_fit + compression - cognitive_cost) / 3)
        components = {"understanding_utility": round(utility, 3), "answerability": round(answerability, 3), "provenance": round(provenance, 3), "structural_fit": round(structural_fit, 3), "compression": round(compression, 3), "cognitive_cost": cognitive_cost}
        score = round(utility + answerability + provenance + structural_fit + compression - cognitive_cost, 3)
        results.append(RepresentationCandidate(definition.id, definition.name, definition.definition, definition.primitive_change, definition.mapping, definition.preserved, definition.discarded, definition.makes_easier, definition.falsification_test, components, score))
    return sorted(results, key=lambda candidate: (-candidate.score, candidate.id))[:limit]
