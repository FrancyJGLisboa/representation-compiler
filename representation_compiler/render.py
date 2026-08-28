from __future__ import annotations

import csv
from pathlib import Path

from .model import CanonicalModel
from .views import Candidate, rows_for


def render_csv(model: CanonicalModel, candidate: Candidate, destination: Path) -> Path:
    destination.parent.mkdir(parents=True, exist_ok=True)
    rows = rows_for(model, candidate)
    columns = list(candidate.spec.columns)
    with destination.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
    return destination
