from representation_compiler.discovery import discover
from representation_compiler.fixtures import project_alpha


def test_discovery_returns_structurally_distinct_candidates_with_falsifiers():
    candidates = discover(project_alpha(), "Where do teams disagree and what changed over time?")
    assert len(candidates) == 5
    assert len({item.family for item in candidates}) == 5
    assert all(item.falsification_test and item.components for item in candidates)
    assert all("understanding_utility" in item.components for item in candidates)


def test_disagreement_objective_prefers_perspective_representation():
    candidates = discover(project_alpha(), "Where do teams disagree?", limit=6)
    assert [item.id for item in candidates].index("perspective-model") < 3
