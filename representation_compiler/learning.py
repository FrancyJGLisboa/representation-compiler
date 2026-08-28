"""Learning loop: representation preference → explain-back → gap → next view."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from uuid import uuid4

from .discovery import RepresentationCandidate, discover
from .model import CanonicalModel


@dataclass(frozen=True)
class Challenge:
    prompt: str
    expected_terms: tuple[str, ...]


@dataclass(frozen=True)
class ExplanationAssessment:
    score: float
    missing_terms: tuple[str, ...]
    next_representation_id: str


def start_candidates(model: CanonicalModel, goal: str) -> list[RepresentationCandidate]:
    return discover(model, goal, limit=5)


def make_challenge(model: CanonicalModel) -> Challenge:
    claim = next(iter(model.assertions.values()), None)
    if not claim:
        return Challenge("Explain the most important relationship in your own words.", ())
    entity = model.entities[claim.subject].name
    terms = tuple(part.lower() for part in (entity, claim.predicate.replace("_", " "), claim.object) if part)
    return Challenge(f"In your own words: how does {entity} relate to {claim.object}, and why does that matter?", terms)


def assess_explanation(answer: str, challenge: Challenge, candidates: list[RepresentationCandidate]) -> ExplanationAssessment:
    words = answer.lower()
    missing = tuple(term for term in challenge.expected_terms if term not in words)
    score = round((len(challenge.expected_terms) - len(missing)) / max(1, len(challenge.expected_terms)), 2)
    if any("depend" in item for item in missing):
        preferred = "dependency-network"
    elif any("state" in item for item in missing):
        preferred = "state-machine"
    else:
        preferred = "perspective-model" if score < .67 else candidates[0].id
    available = {item.id for item in candidates}
    return ExplanationAssessment(score, missing, preferred if preferred in available else candidates[0].id)
