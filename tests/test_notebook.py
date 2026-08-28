import pytest

from representation_compiler.notebook import (
    CoordinateFrame,
    DatasetReference,
    Representation,
    RepresentationNotebook,
    RepresentationTest,
)


def astronomy_notebook() -> RepresentationNotebook:
    return RepresentationNotebook(
        id="m42-sky-geometry",
        title="Where is M42 on the celestial sphere?",
        question="Which representation makes angular relationships between catalog objects easiest to reason about?",
        datasets={"catalog": DatasetReference("catalog", "Catalog sample", "local://catalog.csv", "csv", "sha256:example")},
        frames={"icrs-cartesian": CoordinateFrame("icrs-cartesian", "ICRS Cartesian", ("x", "y", "z"), ("unit", "unit", "unit"), "J2000", "ICRS")},
        tests={"unit-norm": RepresentationTest("unit-norm", "Every encoded direction has norm one", "Compute Euclidean norm", "passed", "norm = 1 within tolerance")},
        representations={"unit-sphere": Representation("unit-sphere", "Unit sphere", "coordinate transformation", ("catalog",), "icrs-cartesian", "RA/Dec degrees → unit Cartesian vector", "unit Cartesian vector → RA/Dec degrees", ("angular direction", "great-circle geometry"), ("radial distance", "photometric brightness"), ("angular separation", "rotation-invariant comparison"), ("rotate sky", "select object"), ("unit-norm",))},
    )


def test_representation_notebook_is_self_describing_and_valid():
    notebook = astronomy_notebook()
    notebook.validate()
    assert notebook.to_dict()["representations"]["unit-sphere"]["preserves"] == ("angular direction", "great-circle geometry")


def test_notebook_rejects_unverifiable_representation():
    notebook = astronomy_notebook()
    item = notebook.representations["unit-sphere"]
    notebook.representations["unit-sphere"] = Representation(**{**item.__dict__, "test_ids": ("missing",)})
    with pytest.raises(ValueError, match="unknown test"):
        notebook.validate()
