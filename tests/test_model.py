import pytest

from representation_compiler.fixtures import project_alpha
from representation_compiler.model import Assertion, Origin


def test_fixture_is_valid_and_conflicts_coexist():
    model = project_alpha()
    assert model.assertions["as-3"].relations["contradicts"] == ("as-2",)
    assert model.assertions["as-5"].origin == Origin.INFERRED


def test_dangling_evidence_fails():
    model = project_alpha()
    original = model.assertions["as-1"]
    model.assertions["as-1"] = Assertion(**{**original.__dict__, "evidence_ids": ("missing",)})
    with pytest.raises(ValueError, match="dangling evidence"):
        model.validate()


def test_invalid_confidence_fails():
    model = project_alpha()
    original = model.assertions["as-1"]
    model.assertions["as-1"] = Assertion(**{**original.__dict__, "confidence": 1.1})
    with pytest.raises(ValueError, match="confidence"):
        model.validate()


def test_historical_assertions_remain_queryable():
    model = project_alpha()
    assert "as-6" in {item.id for item in model.assertions_at("2026-08-10")}
    assert "as-6" not in {item.id for item in model.assertions_at("2026-08-21")}
