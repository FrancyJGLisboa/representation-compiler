# Representation Compiler v0

Turns messy material into competing, evidence-backed representations that help a person understand, reason about, and explain a subject. Decision support is one downstream use case. The model is the source of truth; Excel/CSV is a projection, never the database.

## Run it

```bash
python3 -m pytest
python3 -m representation_compiler.cli "Where do teams disagree?" --csv output/disagreements.csv
```

The command searches the built-in Project Alpha fixture, prints the highest-scoring candidate views with score rationales, and writes the winner as an Excel-compatible CSV.

## What works now

- Canonical `Entity`, `Event`, `Assertion`, `Evidence`, and `Perspective` types.
- Validation for provenance, confidence, stable references, and permitted assertion relations.
- Deterministic source ingestion for structured notes (`Subject | predicate | object`).
- Competing representation search: timeline, decision ledger, commitment tracker, dependency map, contradiction matrix, risk register, and claim/evidence table.
- Inspectable scoring: answerability, traceability, applicability, and cognitive complexity.
- Evidence-preserving CSV export.
- Optional OpenAI extraction that creates **pending proposals only**; approved proposals must still pass local provenance validation before they are committed.

## LLM extraction with review

Install the optional client and set your key in the shell (never in source control):

```bash
python3 -m pip install -e '.[openai]'
export OPENAI_API_KEY='...'
python3 -m representation_compiler.cli --extract notes.txt --model YOUR_MODEL
```

The command prints pending claims. The adapter asks for strict structured output, requires each proposal to quote its source exactly, and does not mutate the model. Programmatic callers review a specific proposal with `review(batch, proposal_id, ProposalStatus.APPROVED, reviewer)` and then call `apply_approved(model, batch)`.

To review proposals interactively, one at a time:

```bash
python3 -m representation_compiler.cli --extract notes.txt --model YOUR_MODEL --review-as Fran
```

For each proposal, use `a` to approve, `r` to reject, `e` to edit its fields, `s` to leave it pending, or `q` to pause. Only approved proposals are committed; every commit is rechecked against the original source text.

When you use `--review-as`, the tool writes a local `representation_compiler.db` SQLite audit history. It retains the original source, proposals, each review decision and proposal snapshot, and the committed assertion/evidence JSON. Choose another location with `--database path/to/history.db`.

## Browser UI

Start the local UI after creating an extraction batch:

```bash
python3 -m representation_compiler.cli --serve --database data/representation-history.db
```

Open `http://127.0.0.1:8000`. The UI lists prior sources, displays the original text, presents one pending proposal for approve/reject/edit, and compares candidate representations for a question. It binds only to your computer (`127.0.0.1`).

Click a candidate view to open its editorial, evidence-linked SVG diagram. The first visual library renders dependency graphs, timelines, and perspective swimlanes; the representation search determines which one leads.

## Use with an existing AI subscription (no API key)

An agent skill can inspect sources using the model the user already subscribes to, then write a proposal JSON file using the schema in `skills/representation-compiler/references/proposal-file.md`. Import it without calling any model API:

```bash
python3 -m representation_compiler.cli --import-proposals proposals.json --database data/representation-history.db
```

After approving and committing claims in the browser, run a structurally diverse representation tournament:

```bash
python3 -m representation_compiler.cli --discover "Decide whether the launch can happen this quarter" --database data/representation-history.db
```

Each candidate records its primitive objects, mapping from the source model, preserved/discarded information, understanding-utility scoring components, and an experiment that could falsify its usefulness.

## Ingestion

Local `.txt`, `.md`, `.csv`, `.json`, `.eml`, and selectable-text PDF files are supported through `representation_compiler.connectors.local_file()`. Credentialed adapters are available for Slack channels, Notion pages, Google Drive files, and Jira issues. Tokens are read only from environment variables (`SLACK_BOT_TOKEN`, `NOTION_API_KEY`, `GOOGLE_DRIVE_ACCESS_TOKEN`, `JIRA_API_TOKEN`); never place them in source files.

## Learning loop

After claims are approved, start a learning session and answer its explain-back challenge:

```bash
python3 -m representation_compiler.cli --learn "Help me understand this system" --database data/representation-history.db
python3 -m representation_compiler.cli --explain SESSION_ID "My explanation in my own words" --confidence 0.6 --database data/representation-history.db
```

The response names missing concepts and recommends the next representation to try. Sessions, confidence, explanation quality, and gaps are saved in the SQLite learning ledger. The same loop is now available in the browser: open a source batch, choose **Start learning**, mark a candidate as clicked or too abstract, then submit the explain-back response.

## Next product slice

Replace the deterministic note importer with an LLM extraction adapter that emits the same canonical contract, then add human review before claims become active.
