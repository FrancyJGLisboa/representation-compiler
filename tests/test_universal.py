import io
import json

from representation_compiler.notebook_explorer import render_notebook_explorer
from representation_compiler.universal import add_learning_record, import_codebase_material, import_table_material, import_text_material


def test_text_adapter_creates_structurally_different_representation_notebook(tmp_path):
    source = tmp_path / "lecture.txt"
    source.write_text("A battery stores energy.\n\nCurrent flows when a circuit closes.")

    imported = import_text_material(source, "Understand how a battery powers a circuit")
    notebook = imported.notebook

    assert imported.item_count == 2
    assert {"concept-map", "mechanism-map", "timeline", "state-machine", "concept-matrix"} <= set(notebook.representations)
    assert notebook.representations["mechanism-map"].discards
    assert notebook.representations["mechanism-map"].falsification_test
    assert notebook.derived_data["source-items"].rows[0]["fragment_id"] == "fragment-1"


def test_text_adapter_accepts_pasted_standard_input(monkeypatch):
    monkeypatch.setattr("sys.stdin", io.StringIO("A source pasted directly into the terminal."))

    notebook = import_text_material("-", "Understand pasted material").notebook

    assert notebook.datasets["pasted-material"].uri == "stdin://pasted-material"


def test_table_adapter_preserves_rows_and_learning_ledger(tmp_path):
    source = tmp_path / "measurements.csv"
    source.write_text("trial,temperature,result\n1,20,low\n2,30,high\n")
    notebook = import_table_material(source, "Understand the measurements").notebook

    add_learning_record(notebook, goal="Understand the measurements", representation_id="concept-matrix", reaction="clicked", explain_back="Temperature changes the result.", confidence=.8)

    assert notebook.derived_data["source-items"].rows[1]["result"] == "high"
    assert notebook.learning_ledger[0].recommended_representation_id
    notebook.validate()


def test_code_adapter_indexes_imports_and_generic_explorer_exports_notebook(tmp_path):
    code = tmp_path / "code"
    code.mkdir()
    (code / "app.py").write_text("import json\nfrom pathlib import Path\n")

    notebook = import_codebase_material(code, "Understand this architecture").notebook
    html = render_notebook_explorer(notebook.to_dict())

    assert notebook.derived_data["source-items"].rows[0]["imports"] == "json, pathlib"
    assert "This clicked" in html
    assert "learning_ledger" in html
    assert json.loads(json.dumps(notebook.to_dict()))["datasets"]["code"]["format"] == "codebase"
