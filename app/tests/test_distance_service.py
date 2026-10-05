from app.services.distance_service import DistanceService


def test_same_location_has_zero_distance():
    distance = DistanceService.calculate_distance_km(
        44.4268,
        26.1025,
        44.4268,
        26.1025,
    )

    assert distance == 0


def test_distance_is_positive():
    distance = DistanceService.calculate_distance_km(
        44.4268,
        26.1025,
        45.6579,
        25.6012,
    )

    assert distance > 0