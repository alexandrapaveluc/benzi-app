import pytest

from app.services.distance_service import DistanceService


def test_same_location_has_zero_distance():
    distance = DistanceService.calculate_distance_km(
        44.4268,
        26.1025,
        44.4268,
        26.1025,
    )

    assert distance == 0


def test_one_degree_on_equator_is_about_111_km():
    distance = DistanceService.calculate_distance_km(
        0,
        0,
        0,
        1,
    )

    assert distance == pytest.approx(111.19, abs=0.01)


def test_distance_bucuresti_brasov():
    # Centrul Bucurestiului - centrul Brasovului, in linie dreapta
    distance = DistanceService.calculate_distance_km(
        44.4268,
        26.1025,
        45.6579,
        25.6012,
    )

    assert distance == pytest.approx(142.4, abs=0.5)


def test_distance_is_symmetric():
    there = DistanceService.calculate_distance_km(44.4268, 26.1025, 45.6579, 25.6012)
    back = DistanceService.calculate_distance_km(45.6579, 25.6012, 44.4268, 26.1025)

    assert there == pytest.approx(back)
