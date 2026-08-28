"""Host-model protocol for generate → critique → refine representation discovery."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from .discovery import RepresentationCandidate, discover
from .model import CanonicalModel


class RepresentationJudge(Protocol):
    def generate(self, model: CanonicalModel, objective: str, seeds: list[RepresentationCandidate]) -> list[RepresentationCandidate]: ...
    def critique(self, model: CanonicalModel, objective: str, candidates: list[RepresentationCandidate]) -> dict[str, str]: ...


@dataclass(frozen=True)
class DiscoveryRun:
    candidates: list[RepresentationCandidate]
    critiques: dict[str, str]
    rounds: int


def run(model: CanonicalModel, objective: str, judge: RepresentationJudge | None = None, rounds: int = 2) -> DiscoveryRun:
    candidates = discover(model, objective, limit=6)
    critiques: dict[str, str] = {}
    if judge is None:
        return DiscoveryRun(candidates, critiques, 0)
    for _ in range(rounds):
        proposed = judge.generate(model, objective, candidates)
        critiques.update(judge.critique(model, objective, proposed))
        candidates = sorted(proposed, key=lambda item: (-item.score, item.id))[:6]
    return DiscoveryRun(candidates, critiques, rounds)
