from representation_compiler.fixtures import project_alpha
from representation_compiler.render import render_csv
from representation_compiler.views import search


def test_returns_deterministic_competing_views():
    model = project_alpha()
    first = search(model, "Why is Project Alpha late?")
    assert len(first) == 3
    assert first == search(model, "Why is Project Alpha late?")
    assert first[0].spec.id in {"dependency-map", "commitment-tracker", "risk-register"}


def test_conflict_question_prioritises_conflict_view():
    results = search(project_alpha(), "Where do teams disagree?", top_k=7)
    assert [item.spec.id for item in results].index("contradiction-matrix") < 3


def test_temporal_question_prioritises_timeline():
    results = search(project_alpha(), "What changed over time?", top_k=7)
    assert [item.spec.id for item in results].index("timeline") < 3


def test_csv_retains_evidence(tmp_path):
    candidate = search(project_alpha(), "Where do teams disagree?")[0]
    path = render_csv(project_alpha(), candidate, tmp_path / "view.csv")
    assert "evidence" in path.read_text()
    assert "roadmap:12" in path.read_text()
