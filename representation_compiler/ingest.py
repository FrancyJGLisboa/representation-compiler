from __future__ import annotations

import re
from datetime import UTC, datetime

from .model import Assertion, CanonicalModel, Evidence, Origin


def compile_notes(model: CanonicalModel, source_id: str, text: str, asserted_by: str = "importer") -> list[str]:
    """Compile explicit `Subject | predicate | object` lines into claims with provenance.

    This deterministic importer is a safe boundary for an LLM extractor: its proposed
    records still enter through the same validator.
    """
    created: list[str] = []
    for line_no, line in enumerate(text.splitlines(), 1):
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        pieces = [part.strip() for part in line.split("|")]
        if len(pieces) != 3:
            continue
        subject, predicate, obj = pieces
        entity_id = re.sub(r"[^a-z0-9]+", "-", subject.lower()).strip("-")
        if entity_id not in model.entities:
            raise ValueError(f"line {line_no}: unknown entity {subject!r}")
        evidence_id = f"ev-{source_id}-{line_no}"
        assertion_id = f"as-{source_id}-{line_no}"
        model.evidence[evidence_id] = Evidence(evidence_id, source_id, line, f"line:{line_no}", datetime.now(UTC).isoformat())
        model.assertions[assertion_id] = Assertion(
            assertion_id, entity_id, predicate, obj, datetime.now(UTC).isoformat(),
            asserted_by, 0.8, "shared", Origin.OBSERVED, (evidence_id,)
        )
        created.append(assertion_id)
    model.validate()
    return created
