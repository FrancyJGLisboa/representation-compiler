"""Small, inspectable source-to-concept graph extraction for understanding notebooks."""
from __future__ import annotations

import re
from dataclasses import asdict
from typing import Any

from .notebook import EvidenceEdge, EvidenceNode, RepresentationGraph


_AI_INFRASTRUCTURE = (
    ("gpu", "GPU", "hardware"), ("vram", "VRAM", "memory"), ("model-server", "Model server", "service"),
    ("prefill", "Prefill", "phase"), ("kv-cache", "KV cache", "cache"), ("decode", "Decode", "phase"),
    ("batching", "Batching", "scheduling"), ("sharding", "Sharding", "distribution"), ("routing", "Smart routing", "scheduling"),
    ("kubernetes", "Kubernetes", "orchestration"), ("llm-d", "llm-d", "orchestration"),
)
_AI_EDGES = (
    ("gpu", "vram", "is fed by"), ("vram", "model-server", "holds model weights for"),
    ("model-server", "prefill", "processes prompt in"), ("prefill", "kv-cache", "writes reusable work to"),
    ("kv-cache", "decode", "avoids repeating work during"), ("decode", "batching", "is shared through"),
    ("batching", "sharding", "is constrained when models need"), ("sharding", "routing", "creates fleet topology for"),
    ("routing", "llm-d", "is performed by"), ("llm-d", "kubernetes", "runs on"),
)


def extract_source_graph(rows: tuple[dict, ...], title: str) -> RepresentationGraph:
    text_by_id = {str(row.get("fragment_id") or row.get("row_id") or row.get("path") or index): " ".join(str(value) for value in row.values()) for index, row in enumerate(rows, start=1)}
    corpus = " ".join(text_by_id.values()).lower()
    concepts = _AI_INFRASTRUCTURE if sum(term in corpus for term, _, _ in _AI_INFRASTRUCTURE) >= 5 else _generic_concepts(text_by_id)
    nodes = tuple(EvidenceNode(identifier, label, kind, _evidence_for(label, text_by_id)) for identifier, label, kind in concepts)
    node_ids = {node.id for node in nodes}
    edges = []
    for source, target, relation in _AI_EDGES:
        if source in node_ids and target in node_ids:
            evidence = _evidence_for(_node_label(source, nodes), text_by_id) + _evidence_for(_node_label(target, nodes), text_by_id)
            edges.append(EvidenceEdge(source, target, relation, tuple(dict.fromkeys(evidence))[:3]))
    if not edges:
        edges = [EvidenceEdge(nodes[index].id, nodes[index + 1].id, "is introduced before", tuple(dict.fromkeys(nodes[index].evidence_ids + nodes[index + 1].evidence_ids))[:2]) for index in range(len(nodes) - 1)]
    return RepresentationGraph("source-concept-graph", title, nodes, tuple(edges))


def enrich_notebook_payload(payload: dict[str, Any]) -> dict[str, Any]:
    """Add a source graph to notebooks created before graph extraction existed."""
    derived = next(iter(payload.get("derived_data", {}).values()), None)
    if not derived or not derived.get("rows"):
        raise ValueError("notebook has no indexed source rows to graph")
    graph = extract_source_graph(tuple(derived["rows"]), f"{payload.get('title', 'Notebook')}: source concept graph")
    payload["graphs"] = {graph.id: asdict(graph)}
    for representation in payload.get("representations", {}).values():
        if representation.get("family") != "source index":
            representation["graph_id"] = graph.id
    return payload


def _generic_concepts(text_by_id: dict[str, str]) -> tuple[tuple[str, str, str], ...]:
    words = re.findall(r"[A-Za-z][A-Za-z-]{4,}", " ".join(text_by_id.values()).lower())
    ignored = {"about", "their", "there", "which", "would", "every", "these", "those", "because", "where", "other", "through", "between"}
    frequent = [word for word in dict.fromkeys(words) if word not in ignored and words.count(word) > 1][:8]
    if len(frequent) < 2:
        frequent = ["source", "idea"]
    return tuple((f"concept-{index}", word.replace("-", " ").title(), "concept") for index, word in enumerate(frequent, start=1))


def _evidence_for(label: str, text_by_id: dict[str, str]) -> tuple[str, ...]:
    terms = [part.lower() for part in re.findall(r"[A-Za-z0-9]+", label) if len(part) > 1]
    found = [identifier for identifier, text in text_by_id.items() if any(term in text.lower() for term in terms)]
    return tuple(found[:3]) or (next(iter(text_by_id)),)


def _node_label(identifier: str, nodes: tuple[EvidenceNode, ...]) -> str:
    return next(node.label for node in nodes if node.id == identifier)
