import pytest

from representation_compiler.astronomy import ICRSSkyPoint, icrs_unit_vector, norm


def test_icrs_unit_vector_preserves_direction_as_unit_length():
    vector = icrs_unit_vector(ICRSSkyPoint(90, 0))
    assert vector == pytest.approx((0, 1, 0))
    assert norm(vector) == pytest.approx(1)


def test_icrs_point_rejects_invalid_coordinates():
    with pytest.raises(ValueError, match="right ascension"):
        icrs_unit_vector(ICRSSkyPoint(360, 0))
