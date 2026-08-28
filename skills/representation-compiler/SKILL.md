---
name: representation-compiler
description: "Turn messy operational sources into evidence-backed visual representations when a user needs to understand, explain, or decide—not merely summarize."
---

# Representation Compiler

Use this skill when a user brings any material they need to understand, reason about, explain, track, or decide from. Company operations are one use case, not the boundary.

The goal is not a prettier summary. Build a source-grounded model, search for the representation that best helps the user understand the subject, and render competing visual explanations. Decision-making is a selectable downstream task.

## User invocation

The user only needs to provide two things: what they want to understand and the material.

```text
$representation-compiler

I want to understand: Why is this project late?

Material:
- emails/alpha-thread.md
- notes/launch-meeting.md
```

If material is pasted, treat the pasted content as the source. Do not make the user create JSON, choose a representation, name an entity, or run the local engine manually.

For a portable command packet that works from any agentic terminal, the user can run:

```bash
repr learn "transcript.txt" --goal "Explain the video's core mechanism and its failure cases"
```

They paste the resulting packet into their agent. This command does not call an LLM or require an API key; it makes the required reasoning protocol explicit.

## Required representation-discovery protocol

This is mandatory whenever the user asks for a better way to understand, explain, or reason about material. Do not reduce the task to a summary or select a diagram before this protocol is complete.

1. Treat the current representation as arbitrary. Identify primitive objects, explicit and implicit relationships, hidden symmetries, expensive operations, and distinctions that may be irrelevant.
2. Produce structurally different candidates: change objects, coordinates, invariances/equivalence classes, relations, latent state, or scale. Do not make cosmetic diagram variants.
3. For each candidate, record source-to-representation mapping, recoverability, preserved/discarded information, explicit invariants, what becomes easier/harder, a downstream task, and a falsifiable test.
4. Run a tournament on understanding utility: explain-back quality, transfer, visible uncertainty, cognitive load, and evidence traceability. Apply predictive power, compression, invariance, causal interpretability, robustness, and computational efficiency when measurable.
5. Keep a representation ledger. For every finalist, include its strongest counterexample/failure regime and what newly becomes visible. Continue with another transformation if the winning representation still leaves the key relationship obscure.

Search deliberately for quotients, coordinate systems, sufficient representations, generative representations, and transformations that turn hard operations into easier ones: nonlinear to linear, global to local, temporal to geometric, high-dimensional to sparse, relational to graphical, or repeated computation to lookup.

## Workflow

1. Ask what the user needs to understand, explain, track, or decide if it is not evident. Do not ask the user to select a diagram type.
2. Read only the supplied sources. Extract explicit claims, entities, dates, dependencies, and disagreements. Preserve uncertainty; do not merge conflicting perspectives.
3. Create a proposal JSON file using [proposal-file.md](references/proposal-file.md). Every claim needs an exact contiguous evidence quote from the supplied source.
4. Import it with:

   ```bash
   python3 -m representation_compiler.cli --import-proposals <proposal-file> --database data/representation-history.db
   ```

5. Start the local companion UI:

   ```bash
   python3 -m representation_compiler.cli --serve --database data/representation-history.db
   ```

6. Tell the user to review proposals in the browser. Only approved proposals become claims. Then run a representation tournament:

   ```bash
   python3 -m representation_compiler.cli --discover "<decision objective>" --database data/representation-history.db
   ```

   Explain the winner's structural advantage, what it discards, and its falsification test before rendering it.

## Discovery loop

When the user asks for a genuinely better way to reason, run at least two rounds:

1. Generate at least five structurally different representation candidates. At least one must change primitives, one coordinates/time, one add relations, one preserve disagreement, and one remove irrelevant variation.
2. Critique each candidate: identify the strongest counterexample, information it discards, and the smallest downstream test that could show it is not useful.
3. Refine or discard candidates. Do not select a winner until its advantage is tied to the stated decision objective.

Record the final candidates and critiques in the representation ledger. `representation_compiler.discovery_loop` provides the local contract for a host-model generator and critic; the host agent supplies the reasoning using its existing subscription.

Use `diagram-design` for the visual output when it is installed. Choose the semantic meaning first and the diagram grammar second: dependency graph for blockers, timeline for change, perspective swimlanes for disagreement, fishbone/causal map for causes.

## Invariants

- A diagram is a projection, never the source of truth.
- Every consequential visual claim must be traceable to evidence.
- Explicit disagreement must remain visible.
- The host agent subscription performs reasoning. Do not require an API key for this workflow.
- The user must approve or reject proposals; never auto-commit claims.
- Do not select a candidate because it looks familiar or visually elegant. Compare structurally different families and retain the tournament ledger.
- Optimize first for understanding utility: accurate explanation, transfer to a related case, visible uncertainty, and manageable cognitive load. Treat decision utility as one possible downstream measure.
