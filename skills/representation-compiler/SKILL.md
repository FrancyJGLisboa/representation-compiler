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
