"""Portable, inspectable instructions for representation discovery."""
from __future__ import annotations

from pathlib import Path


DISCOVERY_HARNESS = """Your task is to discover useful representations of a target system, not merely solve tasks inside the current representation.

Treat the existing representation as arbitrary and potentially misleading. Identify the current primitive objects, explicit and implicit relationships, hidden symmetries, expensive operations, and distinctions that may be irrelevant.

Generate structurally different candidates rather than cosmetic variants. Include candidates that change primitive objects, coordinate systems, invariances/equivalence classes, relational structure, latent state, and scale when applicable. Consider graphs, sequences, state machines, causal models, matrices, probability models, grammars, constraints, hierarchies, and hybrid symbolic-neural representations.

For every candidate representation R, record: its definition; source-to-R mapping; R-to-source mapping when possible; information preserved and discarded; explicit invariants; encoding/decoding ambiguity and complexity; what becomes easier and harder; a downstream task; and a falsifiable experiment.

Search for transformations that make important operations simpler: nonlinear to linear, global to local, temporal to geometric, high-dimensional to sparse, relational to graphical, or repeated computation to lookup. Search for sufficient, generative, and quotient representations. Ask what changes in raw material without changing the outcome, then remove that irrelevant variation.

Run a tournament. Compare candidates on understanding utility first: accurate explain-back, transfer to a related case, visible uncertainty, cognitive load, and evidence traceability. Use prediction, compression, invariance, causal interpretability, robustness, and computational efficiency when the material supports measurement. Critique the strongest counterexample and failure regime for every finalist. Do not select a familiar or visually attractive view without a structural advantage.

Maintain a representation ledger. The surviving representation must state what it reveals that was obscure before, what would falsify its usefulness, and whether another transformation of it should be explored. A diagram is only a projection of the evidence-backed model, never the model itself."""


def learning_invocation(goal: str, material: str) -> str:
    """Return a portable task packet for an agent that has access to this skill."""
    return f"""Use the representation-compiler skill.

I want to understand: {goal}

Material:
{material}

Required representation-discovery protocol:
{DISCOVERY_HARNESS}
"""


def material_reference(value: str) -> str:
    """Make paths explicit while allowing URLs and pasted material unchanged."""
    path = Path(value)
    return f"Local file: {path}" if path.exists() else value
