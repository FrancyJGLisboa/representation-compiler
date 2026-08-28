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

## Astronomy CSV notebook

Create a shareable astronomy representation notebook from a CSV whose columns explicitly declare degrees as `ra_deg` and `dec_deg`:

```bash
python3 -m representation_compiler.cli \
  --import-star-catalog catalog.csv \
  --notebook-output catalog.notebook.json \
  --explorer-output catalog.sky.html
```

Pass `--catalog-source-uri` when the catalog has a stable public source URL. The JSON stores provenance, a checksum, named derived Cartesian vectors, the coordinate transform, representation trade-offs, and the executable invariant result. `catalog.sky.html` is a self-contained explorer that can be shared alongside the JSON.

## FITS catalog notebook

Install optional FITS support in a virtual environment:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -e '.[astronomy]'
```

Then import a FITS binary table whose selected coordinate columns declare units convertible to degrees:

```bash
.venv/bin/python -m representation_compiler.cli \
  --import-fits-catalog catalog.fits \
  --fits-ra-column RA \
  --fits-dec-column DEC \
  --notebook-output catalog.notebook.json
```

The importer accepts `ICRS`, `FK5`, `FK4`, and `GALACTIC` via `RADESYS` or `--fits-frame`. It transforms every supported input into ICRS before deriving Cartesian unit vectors, then records the source frame/equinox and ICRS output frame. For Galactic catalogs, pass the longitude and latitude columns through `--fits-ra-column` and `--fits-dec-column` (for example, `L` and `B`). Unsupported or unspecified frames are rejected rather than guessed.

## Supported local sources and general understanding notebooks

Create portable notebooks from three general material types:

```bash
# Notes, papers already extracted to text, and video transcripts
python3 -m representation_compiler.cli --import-text material.txt \
  --material-question "What is the central mechanism?" \
  --notebook-output material.notebook.json --explorer-output material.html

# CSV measurements, tables, and exported datasets
python3 -m representation_compiler.cli --import-table measurements.csv \
  --material-question "Which variables matter?" \
  --notebook-output measurements.notebook.json

# A local source directory
python3 -m representation_compiler.cli --import-codebase ./project \
  --material-question "How does a request move through this system?" \
  --notebook-output project.notebook.json
```

Each notebook indexes its original material, stores five structurally distinct candidate representations, records what each candidate preserves/discards/makes easier, and includes a falsification test. The standalone explorer lets a learner select a view, complete explain-back, and download the notebook with an updated `learning_ledger`.

`representation_compiler.connectors.local_file()` reads `.txt`, `.md`, `.csv`, `.json`, `.eml`, and selectable-text PDF files. Credentialed Slack, Notion, Google Drive, and Jira adapters obtain their tokens from environment variables; do not put credentials in source control.
