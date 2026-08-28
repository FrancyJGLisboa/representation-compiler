from representation_compiler.fixtures import project_alpha
from representation_compiler.learning import assess_explanation, make_challenge, start_candidates


def test_explain_back_detects_missing_relationship_and_recommends_next_view():
    model = project_alpha()
    candidates = start_candidates(model, "Help me understand why the launch is late")
    assessment = assess_explanation("Project Alpha matters.", make_challenge(model), candidates)
    assert assessment.missing_terms
    assert assessment.next_representation_id in {item.id for item in candidates}


def test_explain_back_rewards_coverage():
    model = project_alpha()
    challenge = make_challenge(model)
    assessment = assess_explanation("Project Alpha depends on API v2.", challenge, start_candidates(model, "Help me understand this"))
    assert assessment.score > 0
