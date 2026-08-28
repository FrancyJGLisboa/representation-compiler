import json

from representation_compiler.catalog import import_icrs_catalog
from representation_compiler.sky_explorer import write_sky_explorer


def test_catalog_notebook_contains_derived_vectors_and_explorer(tmp_path):
    catalog = tmp_path / "orion.csv"
    catalog.write_text("name,ra_deg,dec_deg\nM42,83.822,-5.391\nRigel,78.634,-8.202\n", encoding="utf-8")
    notebook = import_icrs_catalog(catalog).notebook
    payload = notebook.to_dict()
    json_payload = json.loads(json.dumps(payload))

    rows = json_payload["derived_data"]["icrs-unit-vectors"]["rows"]
    assert rows[0]["id"] == "M42"
    assert {"x", "y", "z"} <= set(rows[0])

    output = write_sky_explorer(json_payload, tmp_path / "sky.html")
    html = output.read_text(encoding="utf-8")
    assert "Longitude rotation" in html
    assert "M42" in html
    assert "orthographic projection" in html
