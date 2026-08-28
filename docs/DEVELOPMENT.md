# Development and local companion

This guide is for developers who want to run, extend, or self-host the Python companion. Ordinary users should start with the copyable prompt in the [README](../README.md).

## Run locally

```bash
python3 -m pytest
python3 -m representation_compiler.cli "Where do teams disagree?" --csv output/disagreements.csv
```

The example searches the built-in Project Alpha fixture and writes an Excel-compatible CSV projection.

## Local browser UI

After importing a proposal batch, start the local UI:

```bash
python3 -m representation_compiler.cli --serve --database data/representation-history.db
```

Open `http://127.0.0.1:8000`. The UI runs only on your computer. It retains sources, proposal reviews, approved claims, tournaments, and learning sessions in SQLite.

## Existing-subscription workflow

An agent using an existing subscription can create a proposal JSON file using `skills/representation-compiler/references/proposal-file.md`. Import it without using an API key:

```bash
python3 -m representation_compiler.cli --import-proposals proposals.json --database data/representation-history.db
```

Approve claims in the browser, then run a tournament:

```bash
python3 -m representation_compiler.cli --discover "Help a newcomer understand the system" --database data/representation-history.db
```

## Optional OpenAI API extraction

This is optional and separate from a ChatGPT/Codex subscription:

```bash
python3 -m pip install -e '.[openai]'
export OPENAI_API_KEY='...'
python3 -m representation_compiler.cli --extract notes.txt --model YOUR_MODEL --review-as Fran
```

Extraction creates pending proposals. Only reviewed, provenance-valid claims are committed.

## Learning ledger

After claims are approved:

```bash
python3 -m representation_compiler.cli --learn "Help me understand this system" --database data/representation-history.db
python3 -m representation_compiler.cli --explain SESSION_ID "My explanation in my own words" --confidence 0.6 --database data/representation-history.db
```

The system records explanation quality, confidence, remaining gaps, and the recommended next representation.

## Supported local sources

`representation_compiler.connectors.local_file()` reads `.txt`, `.md`, `.csv`, `.json`, `.eml`, and selectable-text PDF files. Credentialed Slack, Notion, Google Drive, and Jira adapters obtain their tokens from environment variables; do not put credentials in source control.
