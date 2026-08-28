"""Portable, inspectable representation notebooks for scientific work."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True)
class DatasetReference:
    id: str
    title: str
    uri: str
    format: str
    checksum: str = ""
    license: str = ""


@dataclass(frozen=True)
class CoordinateFrame:
    id: str
    name: str
    axes: tuple[str, ...]
    units: tuple[str, ...]
    epoch: str = ""
    reference: str = ""


@dataclass(frozen=True)
class Representation:
    id: str
    title: str
    family: str
    dataset_ids: tuple[str, ...]
    coordinate_frame_id: str
    encode: str
    decode: str
    preserves: tuple[str, ...]
    discards: tuple[str, ...]
    makes_easier: tuple[str, ...]
    controls: tuple[str, ...] = ()
    test_ids: tuple[str, ...] = ()


@dataclass(frozen=True)
class RepresentationTest:
    id: str
    statement: str
    method: str
    status: str = "pending"
    result: str = ""


@dataclass
class RepresentationNotebook:
    """The shareable object; diagrams and chat transcripts are projections of it."""

    id: str
    title: str
    question: str
    datasets: dict[str, DatasetReference] = field(default_factory=dict)
    frames: dict[str, CoordinateFrame] = field(default_factory=dict)
    representations: dict[str, Representation] = field(default_factory=dict)
    tests: dict[str, RepresentationTest] = field(default_factory=dict)
    claims: tuple[str, ...] = ()
    version: str = "0.1"

    def validate(self) -> None:
        if not self.question.strip():
            raise ValueError("notebook question is required")
        for frame in self.frames.values():
            if not frame.axes or len(frame.axes) != len(frame.units):
                raise ValueError(f"{frame.id}: axes and units must have the same non-zero length")
        for representation in self.representations.values():
            if not representation.dataset_ids:
                raise ValueError(f"{representation.id}: at least one dataset is required")
            if representation.coordinate_frame_id not in self.frames:
                raise ValueError(f"{representation.id}: unknown coordinate frame")
            if not representation.encode or not representation.decode:
                raise ValueError(f"{representation.id}: both encode and decode mappings are required")
            if not representation.preserves or not representation.discards:
                raise ValueError(f"{representation.id}: preserved and discarded information are required")
            for dataset_id in representation.dataset_ids:
                if dataset_id not in self.datasets:
                    raise ValueError(f"{representation.id}: unknown dataset {dataset_id}")
            for test_id in representation.test_ids:
                if test_id not in self.tests:
                    raise ValueError(f"{representation.id}: unknown test {test_id}")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
