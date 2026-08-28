from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime
from enum import StrEnum
from typing import Any


class Origin(StrEnum):
    OBSERVED = "observed"
    INFERRED = "inferred"
    CALCULATED = "calculated"
    HUMAN_ENTERED = "human_entered"


class AssertionStatus(StrEnum):
    ACTIVE = "active"
    SUPERSEDED = "superseded"
    RETRACTED = "retracted"


@dataclass(frozen=True)
class Entity:
    id: str
    name: str
    type: str


@dataclass(frozen=True)
class Event:
    id: str
    name: str
    occurred_at: str


@dataclass(frozen=True)
class Evidence:
    id: str
    source_id: str
    excerpt: str
    locator: str = ""
    captured_at: str = ""


@dataclass(frozen=True)
class Perspective:
    id: str
    name: str
    holder: str = ""


@dataclass(frozen=True)
class Assertion:
    id: str
    subject: str
    predicate: str
    object: str
    asserted_at: str
    asserted_by: str
    confidence: float
    perspective_id: str
    origin: Origin
    evidence_ids: tuple[str, ...] = ()
    valid_from: str | None = None
    valid_to: str | None = None
    status: AssertionStatus = AssertionStatus.ACTIVE
    relations: dict[str, tuple[str, ...]] = field(default_factory=dict)

    def applies_at(self, moment: str) -> bool:
        return (not self.valid_from or self.valid_from <= moment) and (not self.valid_to or moment < self.valid_to)


@dataclass
class CanonicalModel:
    schema_version: str = "0.1"
    entities: dict[str, Entity] = field(default_factory=dict)
    events: dict[str, Event] = field(default_factory=dict)
    evidence: dict[str, Evidence] = field(default_factory=dict)
    perspectives: dict[str, Perspective] = field(default_factory=dict)
    assertions: dict[str, Assertion] = field(default_factory=dict)

    def validate(self) -> None:
        ids = set(self.entities) | set(self.events)
        for claim in self.assertions.values():
            if not 0 <= claim.confidence <= 1:
                raise ValueError(f"{claim.id}: confidence must be between 0 and 1")
            if claim.subject not in ids:
                raise ValueError(f"{claim.id}: unknown subject {claim.subject}")
            if claim.perspective_id not in self.perspectives:
                raise ValueError(f"{claim.id}: unknown perspective")
            if claim.origin != Origin.HUMAN_ENTERED and not claim.evidence_ids:
                raise ValueError(f"{claim.id}: provenance is required")
            for evidence_id in claim.evidence_ids:
                if evidence_id not in self.evidence:
                    raise ValueError(f"{claim.id}: dangling evidence {evidence_id}")
            for relation, targets in claim.relations.items():
                if relation not in {"supports", "contradicts", "supersedes", "derived_from"}:
                    raise ValueError(f"{claim.id}: unsupported relation {relation}")
                for target in targets:
                    if target not in self.assertions:
                        raise ValueError(f"{claim.id}: dangling related assertion {target}")

    def assertions_at(self, moment: str) -> list[Assertion]:
        return [item for item in self.assertions.values() if item.applies_at(moment)]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
