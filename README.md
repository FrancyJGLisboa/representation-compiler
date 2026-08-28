# Understand anything in a way that clicks

**Copy this prompt into ChatGPT, Claude, Codex, Copilot, or any AI assistant you already use.**

```text
Use the Representation Compiler method to help me understand the material below.

My goal: [what I want to understand, explain, or reason about]
My familiarity: [new / partial / confident]
Material:
[paste a video transcript, article, notes, document text, or URL]

Do not merely summarize it. Treat the current way of describing this subject as potentially wrong. Create at least five genuinely different ways to represent it. Change the objects, coordinate system, relationships, hidden state, invariances, or scale; do not make five cosmetic diagram variants.

For each candidate, explain what it preserves and discards, what becomes easier or harder to see, what invariant becomes visible, and the smallest test of whether it actually helps understanding.

Compare the candidates for: Can I explain it back? Can I apply it to a related case? Does it make uncertainty visible? Is it mentally manageable?

Show me the best three representations. Ask which one clicked. Then ask me to explain the idea in my own words, give me one “what changes if…” question, identify my gap, and recommend the next representation.
```

That is enough to start. You do not need an API key, Python, or an account with this project.

## What you do

1. Paste the prompt above into your usual AI assistant.
2. Add something you want to understand: a video, article, notes, a work problem, or a question.
3. Look at the three explanations it creates.
4. Say **“this clicked”**, **“too abstract”**, or **“show me another way.”**
5. Explain the idea back. The agent finds the missing piece and gives you a better next view.

## Example: learning from a YouTube video

```text
My goal: Understand why the speaker thinks interest rates affect housing prices.
My familiarity: new
Material: https://www.youtube.com/watch?v=...
```

If your AI assistant cannot read the video, open YouTube’s **Show transcript**, copy it, and paste it under `Material`.

You should get different explanations—not just different drawings—including a causal map, a timeline, a mechanism map, a state model, or a concept comparison. Pick the one that makes the idea easier to explain and use.

## Want a slash command in a coding agent?

This is optional. It is for people who use Codex CLI, Claude Code, or Copilot CLI often.

- **Claude Code:** install the [Claude adapter](adapters/claude-code), then type `/representation-compiler`.
- **GitHub Copilot CLI:** run the one install command in the [Copilot guide](adapters/copilot/README.md), then say `Use the /representation-compiler skill`.
- **Codex / ChatGPT:** import the skill-only [plugin bundle](plugins/representation-compiler) where Plugins are available. Plugin availability varies by plan and workspace.

All three use the same [canonical skill](skills/representation-compiler/SKILL.md). It instructs the agent to run representation discovery, rather than make a normal summary.

## What this is—and is not

This is a method for helping people understand things. It makes an AI search for better ways to describe the same reality, then adapts based on which explanation clicked for you.

It is not a promise that an AI will discover new science every time. A skill gives the agent strong instructions; the visible check is whether it shows distinct candidate representations, what they discard, and tests that could prove them unhelpful.

## For developers and self-hosters

The Python companion stores sources, evidence, review history, representation tournaments, and learning sessions locally. It is optional for ordinary use.

## Build a portable notebook from your own material

The companion now supports material beyond astronomy. It never needs an LLM API key: use your existing agent subscription for the source-specific representation-discovery skill, and use these adapters to preserve the material, candidate structures, learner feedback, and resulting model.

```bash
# A transcript, paper extracted to text, notes, or a copied article
python3 -m representation_compiler.cli \
  --import-text lecture.txt \
  --material-question "Understand how feedback loops stabilise this system" \
  --notebook-output lecture.notebook.json \
  --explorer-output lecture.explorer.html

# A measurement table
python3 -m representation_compiler.cli \
  --import-table experiment.csv \
  --material-question "What controls the outcome?" \
  --notebook-output experiment.notebook.json

# A code repository or source directory
python3 -m representation_compiler.cli \
  --import-codebase ./my-project \
  --material-question "How does this system process a request?" \
  --notebook-output architecture.notebook.json
```

Open the generated HTML explorer. It presents five structurally different starting views—concept map, mechanism map, timeline, state machine, and concept matrix. Select what clicked, explain it back, then download the updated notebook with your learning ledger included.

See [development and local companion setup](docs/DEVELOPMENT.md).
