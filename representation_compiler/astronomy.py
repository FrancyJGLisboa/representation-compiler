"""Small, dependency-free executable checks for astronomy representation notebooks."""
from __future__ import annotations

from dataclasses import dataclass
from math import cos, radians, sin, sqrt


@dataclass(frozen=True)
class ICRSSkyPoint:
    """Right ascension and declination in degrees, in the ICRS frame."""

    right_ascension_deg: float
    declination_deg: float

    def validate(self) -> None:
        if not 0 <= self.right_ascension_deg < 360:
            raise ValueError("right ascension must be in [0, 360) degrees")
        if not -90 <= self.declination_deg <= 90:
            raise ValueError("declination must be in [-90, 90] degrees")


def icrs_unit_vector(point: ICRSSkyPoint) -> tuple[float, float, float]:
    """Encode ICRS spherical coordinates as a Cartesian unit vector."""
    point.validate()
    alpha, delta = radians(point.right_ascension_deg), radians(point.declination_deg)
    return (cos(delta) * cos(alpha), cos(delta) * sin(alpha), sin(delta))


def norm(vector: tuple[float, float, float]) -> float:
    return sqrt(sum(component * component for component in vector))
