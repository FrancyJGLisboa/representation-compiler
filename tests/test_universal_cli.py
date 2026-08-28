import json

from representation_compiler import cli


def test_cli_imports_text_and_writes_explorer(tmp_path, monkeypatch):
    source = tmp_path / "notes.txt"
    output = tmp_path / "notes.notebook.json"
    explorer = tmp_path / "notes.explorer.html"
    source.write_text("First idea.\n\nSecond idea.")
    monkeypatch.setattr("sys.argv", ["representation-compiler", "--import-text", str(source), "--material-question", "Understand these notes", "--notebook-output", str(output), "--explorer-output", str(explorer)])

    cli.main()

    assert json.loads(output.read_text())["question"] == "Understand these notes"
    assert "This clicked" in explorer.read_text()
