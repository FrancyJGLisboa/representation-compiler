import json

import pytest

from representation_compiler.catalog import import_icrs_catalog


def test_catalog_import_writes_a_portable_validated_notebook(tmp_path):
    catalog = tmp_path / "orion.csv"
    catalog.write_text("name,ra_deg,dec_deg\nM42,83.822,-5.391\nRigel,78.634,-8.202\n", encoding="utf-8")

    imported = import_icrs_catalog(catalog, "https://example.org/orion.csv")
    output = imported.notebook.write_json(tmp_path / "orion.notebook.json")
    payload = json.loads(output.read_text())

    assert imported.row_count == 2
    assert imported.max_unit_norm_error < 1e-12
    assert payload["datasets"]["orion"]["uri"] == "https://example.org/orion.csv"
    assert payload["tests"]["unit-norm"]["status"] == "passed"
    assert payload["representations"]["unit-sphere"]["coordinate_frame_id"] == "icrs-cartesian"


def test_catalog_rejects_missing_explicit_degree_columns(tmp_path):
    catalog = tmp_path / "ambiguous.csv"
    catalog.write_text("ra,dec\n83.822,-5.391\n", encoding="utf-8")

    with pytest.raises(ValueError, match="degree-declared columns"):
        import_icrs_catalog(catalog)
