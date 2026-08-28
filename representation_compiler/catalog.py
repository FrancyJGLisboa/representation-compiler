"""Import simple ICRS star catalogs into portable representation notebooks."""
from __future__ import annotations

import csv
import hashlib
from dataclasses import dataclass
from pathlib import Path

from .astronomy import ICRSSkyPoint, icrs_unit_vector, norm
from .notebook import CoordinateFrame, DatasetReference, DerivedData, Representation, RepresentationNotebook, RepresentationTest


REQUIRED_COLUMNS = {"ra_deg", "dec_deg"}
UNCERTAINTY_COLUMNS = {"uncertainty_deg", "ra_error_deg", "dec_error_deg"}


@dataclass(frozen=True)
class CatalogImport:
    notebook: RepresentationNotebook
    row_count: int
    max_unit_norm_error: float


def import_icrs_catalog(path: str | Path, source_uri: str | None = None) -> CatalogImport:
    """Read a CSV with degree-declared ``ra_deg`` and ``dec_deg`` columns."""
    source = Path(path)
    with source.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        headers = set(reader.fieldnames or ())
        missing = REQUIRED_COLUMNS - headers
        if missing:
            raise ValueError(f"catalog requires degree-declared columns: {', '.join(sorted(missing))}")
        vectors, derived_rows, has_uncertainty = [], [], False
        for row_number, row in enumerate(reader, start=2):
            try:
                point = ICRSSkyPoint(float(row["ra_deg"]), float(row["dec_deg"]))
                vector = icrs_unit_vector(point)
                vectors.append(vector)
                derived = {
                    "id": row.get("id") or row.get("name") or f"row-{row_number - 1}",
                    "ra_deg": point.right_ascension_deg, "dec_deg": point.declination_deg,
                    "x": vector[0], "y": vector[1], "z": vector[2],
                }
                uncertainty = _uncertainty_deg(row)
                if uncertainty is not None:
                    derived["uncertainty_deg"] = uncertainty
                    has_uncertainty = True
                derived_rows.append(derived)
            except (TypeError, ValueError) as error:
                raise ValueError(f"row {row_number}: invalid ICRS coordinates: {error}") from error
    if not vectors:
        raise ValueError("catalog must contain at least one coordinate row")
    max_error = max(abs(norm(vector) - 1) for vector in vectors)
    checksum = hashlib.sha256(source.read_bytes()).hexdigest()
    dataset_id = _slug(source.stem) or "catalog"
    notebook = RepresentationNotebook(
        id=f"{dataset_id}-unit-sphere",
        title=f"{source.stem}: ICRS unit-sphere representation",
        question="Which angular relationships in this catalog become easier to reason about in Cartesian coordinates?",
        datasets={dataset_id: DatasetReference(
            dataset_id, source.name, source_uri or f"file://{source.name}", "csv", f"sha256:{checksum}",
            metadata={"row_count": str(len(vectors)), "ra_column": "ra_deg", "dec_column": "dec_deg", "angle_unit": "deg", "uncertainty_columns": ",".join(sorted(headers & UNCERTAINTY_COLUMNS))},
        )},
        frames={"icrs-cartesian": CoordinateFrame("icrs-cartesian", "ICRS Cartesian unit sphere", ("x", "y", "z"), ("unit", "unit", "unit"), "J2000", "ICRS")},
        tests={"unit-norm": RepresentationTest(
            "unit-norm", "Every ICRS direction encodes to a unit Cartesian vector", "Compute max(abs(norm(vector) - 1)) over catalog rows", "passed",
            f"{len(vectors)} rows checked; maximum norm error = {max_error:.3g}",
        )},
        representations={"unit-sphere": Representation(
            "unit-sphere", "ICRS unit sphere", "coordinate transformation", (dataset_id,), "icrs-cartesian",
            "(ra_deg, dec_deg) → (cos(dec)cos(ra), cos(dec)sin(ra), sin(dec))",
            "(x, y, z) → (atan2(y, x), asin(z))",
            ("angular direction", "great-circle geometry", "rotation-invariant angular comparison"),
            ("radial distance", "brightness", "catalog row order"),
            ("angular separation", "vector-based sky rotations", "spatial indexing"),
            ("select object", "rotate sky"), ("unit-norm",), "icrs-unit-vectors",
        )},
        derived_data={"icrs-unit-vectors": DerivedData(
            "icrs-unit-vectors", "unit-sphere", ("id", "ra_deg", "dec_deg", "x", "y", "z") + (("uncertainty_deg",) if has_uncertainty else ()), tuple(derived_rows),
        )},
    )
    notebook.validate()
    return CatalogImport(notebook, len(vectors), max_error)


def _slug(value: str) -> str:
    return "".join(character.lower() if character.isalnum() else "-" for character in value).strip("-")


def _uncertainty_deg(row: dict[str, str]) -> float | None:
    values = []
    for column in ("uncertainty_deg", "ra_error_deg", "dec_error_deg"):
        value = row.get(column, "").strip()
        if value:
            parsed = float(value)
            if parsed < 0:
                raise ValueError(f"{column} must be non-negative")
            values.append(parsed)
    return max(values) if values else None
