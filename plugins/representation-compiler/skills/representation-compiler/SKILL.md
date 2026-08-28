---
name: representation-compiler
description: "Help a person understand any supplied material through structurally different, evidence-backed representations—not a normal summary."
---

# Representation Compiler

Use this skill when someone wants to understand, explain, learn from, or reason about supplied material: a video transcript, article, notes, document, or question.

The user gives only two things: what they want to understand and the material. Do not require an API key, JSON, diagram choice, or local Python setup.

## Required representation-discovery protocol

Do not merely summarize. Treat the current representation as potentially wrong.

1. Identify the current primitive objects, explicit and implicit relationships, hidden symmetries, expensive operations, and distinctions that may be irrelevant.
2. Generate at least five structurally different candidates. Change objects, coordinate systems, invariances/equivalence classes, relations, latent state, or scale; never make cosmetic diagram variants.
3. For every candidate, state: what it preserves and discards; what becomes easier and harder; the relevant invariant; a downstream task; and the smallest falsifiable test of whether it helps.
4. Run a tournament based on understanding utility: explain-back quality, transfer to a related case, visible uncertainty, cognitive load, and evidence traceability. Use prediction, compression, invariance, causal interpretation, robustness, and computational efficiency where the source allows measurement.
5. Show the best three representations. Ask which one clicked. Ask the learner to explain it back in their own words, pose one transfer question, identify the gap, and recommend the next representation.

Search deliberately for quotients, coordinate-system changes, sufficient representations, generative models, and transformations that turn hard operations into easier ones: nonlinear to linear, global to local, temporal to geometric, high-dimensional to sparse, relational to graphical, or repeated computation to lookup.

## Evidence and honesty

- Ground consequential claims in the supplied material and preserve uncertainty or disagreement.
- A diagram is a projection, not the source of truth.
- Do not claim the method discovered a new fact unless the material supports it.
- The visible proof of following this skill is a set of genuinely different candidates, their trade-offs, and their falsification tests.
