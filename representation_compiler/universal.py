"""Typed adapters that turn common learning material into portable notebooks."""
from __future__ import annotations

import ast
import csv
import hashlib
import re
import sys
from dataclasses import dataclass
from pathlib import Path

from .catalog import _slug
from .notebook import CoordinateFrame, DatasetReference, DerivedData, LearningRecord, Representation, RepresentationNotebook, RepresentationTest
from .source_graph import extract_source_graph


@dataclass(frozen=True)
class MaterialImport:
    notebook: RepresentationNotebook
    item_count: int


_CANDIDATES = (
    ("concept-map", "Concept Map", "concept graph", "Terms and claims become nodes; stated relationships become labeled links.", "concepts and explicit relations", "source order and rhetorical style", "definitions, dependencies, and missing links", "Ask a learner to connect two concepts not shown together. If they cannot, add no link."),
    ("mechanism-map", "Mechanism Map", "causal / mechanism model", "Actors, inputs, processes, and effects become a mechanism chain.", "proposed mechanisms and intervention points", "unrelated detail and unproven causality", "causal pathways and intervention points", "For every causal arrow, name an observation that would make it false."),
    ("timeline", "Timeline", "temporal trajectory", "Events and state changes become an ordered sequence.", "order, timing, and supersession", "cross-cutting structure without time", "change, delay, and supersession", "Remove dates. If the explanation remains equally clear, time is not doing useful work."),
    ("state-machine", "State Machine", "state-transition model", "The subject becomes states, transitions, triggers, and constraints.", "allowed changes and transition conditions", "continuous nuance within a state", "what can change next and why", "Find an observed transition with no trigger. It remains a hypothesis until sourced."),
    ("concept-matrix", "Concept Matrix", "comparison matrix", "Concepts become rows; properties, evidence, and cases become comparable columns.", "similarities, differences, and coverage gaps", "sequence and causal direction", "comparison and missing distinctions", "Hide one column. If a learner's conclusion is unchanged, that distinction is not useful."),
)


def import_text_material(path: str | Path, question: str, source_uri: str | None = None) -> MaterialImport:
    if str(path) == "-":
        source, text = Path("pasted-material.txt"), sys.stdin.read()
        checksum = hashlib.sha256(text.encode()).hexdigest()
    else:
        source = Path(path)
        text = source.read_text(encoding="utf-8")
        checksum = None
    fragments = _text_fragments(text)
    if not fragments:
        raise ValueError("text material must contain at least one non-empty paragraph")
    return _build_notebook(source, question, "text", fragments, ("fragment_id", "text"), source_uri or ("stdin://pasted-material" if str(path) == "-" else None), checksum=checksum)


def import_table_material(path: str | Path, question: str, source_uri: str | None = None) -> MaterialImport:
    source = Path(path)
    with source.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames:
            raise ValueError("CSV material requires a header row")
        columns = tuple(reader.fieldnames)
        rows = tuple({"row_id": str(index), **{column: value for column, value in row.items()}} for index, row in enumerate(reader, start=1))
    if not rows:
        raise ValueError("CSV material must contain at least one data row")
    return _build_notebook(source, question, "table", rows, ("row_id",) + columns, source_uri)


def import_codebase_material(path: str | Path, question: str, source_uri: str | None = None) -> MaterialImport:
    root = Path(path)
    if not root.is_dir():
        raise ValueError("code material must be a directory")
    rows = tuple(_code_rows(root))
    if not rows:
        raise ValueError("code material must contain supported source files")
    checksum = hashlib.sha256("".join(f"{row['path']}:{row['checksum']}" for row in rows).encode()).hexdigest()
    return _build_notebook(root, question, "codebase", rows, ("path", "language", "line_count", "imports", "checksum"), source_uri, checksum=checksum)


def add_learning_record(notebook: RepresentationNotebook, *, goal: str, representation_id: str, reaction: str = "", explain_back: str = "", confidence: float | None = None) -> RepresentationNotebook:
    if representation_id not in notebook.representations:
        raise ValueError(f"unknown representation: {representation_id}")
    recommendation = _next_representation(notebook, representation_id, reaction, explain_back)
    gaps = _gaps(explain_back, notebook) if explain_back else ()
    record = LearningRecord(goal, representation_id, reaction, explain_back, confidence, _challenge(notebook), gaps, recommendation)
    notebook.learning_ledger = (*notebook.learning_ledger, record)
    notebook.validate()
    return notebook


def _build_notebook(source: Path, question: str, material_type: str, rows: tuple[dict, ...], columns: tuple[str, ...], source_uri: str | None, checksum: str | None = None) -> MaterialImport:
    dataset_id = _slug(source.stem) or material_type
    checksum = checksum or hashlib.sha256(source.read_bytes()).hexdigest()
    frame_id = f"{material_type}-source"
    index_id = "source-index"
    graph = extract_source_graph(rows, f"{source.stem}: source concept graph")
    dataset = DatasetReference(dataset_id, source.name, source_uri or f"file://{source}", material_type, f"sha256:{checksum}", {"item_count": str(len(rows)), "adapter": material_type, "columns": ",".join(columns)})
    representations = {index_id: Representation(index_id, "Source index", "source index", (dataset_id,), frame_id, "source material → addressable fragments or records", "addressable fragment or record → source material", ("source provenance", "verbatim fragments"), ("interpretation",), ("audit a representation against its material",), (), ("source-coverage",), "source-items")}
    for identifier, title, family, mapping, preserves, discards, easier, falsification in _CANDIDATES:
        representations[identifier] = Representation(identifier, title, family, (dataset_id,), frame_id, mapping, "Use source identifiers to return to the original material.", (preserves, "source traceability"), (discards,), (easier,), ("this clicked", "too abstract", "another way", "go deeper"), ("source-coverage",), "", falsification, graph.id)
    notebook = RepresentationNotebook(
        id=f"{dataset_id}-understanding",
        title=f"{source.stem}: understanding notebook",
        question=question,
        datasets={dataset_id: dataset},
        frames={frame_id: CoordinateFrame(frame_id, f"{material_type.title()} source frame", columns, tuple("text" for _ in columns), reference="source material")},
        representations=representations,
        derived_data={"source-items": DerivedData("source-items", index_id, columns, rows)},
        tests={"source-coverage": RepresentationTest("source-coverage", "Every source item has a portable address", "Count derived rows and compare with adapter output", "passed", f"{len(rows)} items indexed")},
        graphs={graph.id: graph},
    )
    notebook.validate()
    return MaterialImport(notebook, len(rows))


def _text_fragments(text: str) -> tuple[dict[str, str], ...]:
    parts = [part.strip() for part in re.split(r"\n\s*\n", text) if part.strip()]
    if len(parts) == 1:
        parts = [part.strip() for part in re.split(r"(?<=[.!?])\s+", text) if part.strip()]
    return tuple({"fragment_id": f"fragment-{index}", "text": part} for index, part in enumerate(parts, start=1))


def _code_rows(root: Path):
    suffixes = {".py": "python", ".js": "javascript", ".ts": "typescript", ".tsx": "typescript", ".jsx": "javascript", ".java": "java", ".go": "go", ".rs": "rust"}
    for path in sorted(root.rglob("*")):
        if not path.is_file() or any(part.startswith(".") or part in {"node_modules", "vendor", "dist", "build"} for part in path.parts):
            continue
        language = suffixes.get(path.suffix)
        if not language:
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        yield {"path": str(path.relative_to(root)), "language": language, "line_count": str(text.count("\n") + 1), "imports": ", ".join(_imports(text, language)), "checksum": hashlib.sha256(text.encode()).hexdigest()}


def _imports(text: str, language: str) -> tuple[str, ...]:
    if language == "python":
        try:
            tree = ast.parse(text)
            return tuple(sorted({node.names[0].name if isinstance(node, ast.Import) else (node.module or "") for node in ast.walk(tree) if isinstance(node, (ast.Import, ast.ImportFrom))}))
        except SyntaxError:
            return ()
    return tuple(sorted(set(re.findall(r"(?:from\s+|import\s*(?:\(\s*)?['\"])([^'\"\s/]+)", text))))


def _challenge(notebook: RepresentationNotebook) -> str:
    return f"Explain the central relationship in your own words. Then answer: what would change if one important relationship in {notebook.title} disappeared?"


def _gaps(answer: str, notebook: RepresentationNotebook) -> tuple[str, ...]:
    source = next(iter(notebook.derived_data.values())).rows
    words = re.findall(r"[a-zA-Z]{5,}", " ".join(str(value) for row in source[:20] for value in row.values()).lower())
    frequent = [word for word in dict.fromkeys(words) if words.count(word) > 1][:5]
    lowered = answer.lower()
    return tuple(word for word in frequent if word not in lowered)


def _next_representation(notebook: RepresentationNotebook, selected: str, reaction: str, explanation: str) -> str:
    if reaction in {"too_abstract", "another way"}:
        return "concept-matrix"
    if reaction == "go_deeper" or _gaps(explanation, notebook):
        return "mechanism-map" if selected != "mechanism-map" else "state-machine"
    return "timeline" if selected != "timeline" else "concept-map"
