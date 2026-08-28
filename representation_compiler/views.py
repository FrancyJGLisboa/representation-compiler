from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from .model import Assertion, CanonicalModel
from .representation_catalog import CATALOG


@dataclass(frozen=True)
class RepresentationSpec:
    id: str
    name: str
    purpose: str
    columns: tuple[str, ...]
    keywords: tuple[str, ...]


LIBRARY = tuple(RepresentationSpec(item.visual_id, item.name, item.purpose, item.columns, item.keywords) for item in CATALOG)


@dataclass(frozen=True)
class Candidate:
    spec: RepresentationSpec
    score: float
    components: dict[str, float]
    rationale: tuple[str, ...]


def _contradictions(model: CanonicalModel) -> int:
    return sum(len(claim.relations.get("contradicts", ())) for claim in model.assertions.values())


def search(model: CanonicalModel, question: str, top_k: int = 3, weights: dict[str, float] | None = None) -> list[Candidate]:
    model.validate()
    q = question.lower()
    weights = {"answerability": 1, "traceability": 1, "applicability": 1, "complexity": 1, **(weights or {})}
    provenance = sum(bool(a.evidence_ids) for a in model.assertions.values()) / max(1, len(model.assertions))
    conflict_count = _contradictions(model)
    candidates = []
    for spec in LIBRARY:
        hits = sum(word in q for word in spec.keywords)
        applicability = min(1.0, hits / 2)
        if spec.id == "contradiction-matrix" and conflict_count:
            applicability = max(applicability, 0.35)
        if spec.id == "timeline" and any(a.valid_from or a.asserted_at for a in model.assertions.values()):
            applicability = max(applicability, 0.25)
        complexity = len(spec.columns) / 5
        answerability = min(1.0, 0.25 + applicability + (0.15 if spec.id in {"dependency-map", "timeline", "contradiction-matrix"} else 0))
        components = {"answerability": answerability, "traceability": provenance, "applicability": applicability, "complexity": complexity}
        score = (weights["answerability"] * answerability + weights["traceability"] * provenance + weights["applicability"] * applicability - weights["complexity"] * complexity)
        rationale = [f"keyword match: {hits}", f"provenance coverage: {provenance:.0%}"]
        if spec.id == "contradiction-matrix": rationale.append(f"explicit contradictions: {conflict_count}")
        candidates.append(Candidate(spec, round(score, 3), components, tuple(rationale)))
    return sorted(candidates, key=lambda item: (-item.score, item.spec.id))[:top_k]


def rows_for(model: CanonicalModel, candidate: Candidate) -> list[dict[str, str]]:
    rows = []
    for claim in model.assertions.values():
        evidence = "; ".join(model.evidence[e].locator for e in claim.evidence_ids)
        rows.append({"subject": model.entities.get(claim.subject, model.events.get(claim.subject)).name, "claim": f"{claim.predicate}: {claim.object}", "perspective": model.perspectives[claim.perspective_id].name, "confidence": str(claim.confidence), "evidence": evidence, "time": claim.valid_from or claim.asserted_at, "origin": claim.origin, "status": claim.status})
    return rows
