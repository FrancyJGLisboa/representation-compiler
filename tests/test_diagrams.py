from representation_compiler.diagrams import render
from representation_compiler.fixtures import project_alpha
from representation_compiler.views import search


def diagram_for(question: str) -> str:
    model = project_alpha()
    return render(search(model, question)[0], model)


def test_dependency_candidate_is_a_accessible_svg():
    output = diagram_for("Why is Project Alpha late?")
    assert "Dependency graph" in output
    assert "role='img'" in output
    assert "<svg" in output


def test_timeline_candidate_is_a_accessible_svg():
    output = diagram_for("What changed over time?")
    assert "Timeline" in output
    assert "<svg" in output


def test_disagreement_candidate_is_a_accessible_svg():
    output = diagram_for("Where do teams disagree?")
    assert "Perspective contradiction view" in output
    assert "<svg" in output
