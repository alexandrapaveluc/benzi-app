import pytest

from app.config import settings
from app.models.location import UserLocation
from app.services.station_service import StationService


USER = UserLocation(latitude=44.8565, longitude=24.8692)


def raw_station(station_id, latitude, longitude, prices=None, brand="Petrom"):
    return {
        "id": station_id,
        "name": f"Statia {station_id}",
        "brand": brand,
        "address": "Strada Test 1",
        "latitude": latitude,
        "longitude": longitude,
        "updated_at": "2026-10-07T11:05:00+03:00",
        "prices": prices or {},
    }


@pytest.fixture
def service():
    return StationService()


def fake_client(monkeypatch, service, stations_by_call):
    """Inlocuieste clientul; fiecare apel primeste urmatoarea lista."""
    calls = []

    def fake_get_stations(latitude, longitude, radius_km):
        calls.append((latitude, longitude, radius_km))
        index = min(len(calls) - 1, len(stations_by_call) - 1)
        return list(stations_by_call[index])

    monkeypatch.setattr(service.client, "get_stations", fake_get_stations)
    return calls


def test_builds_stations_with_all_prices(monkeypatch, service):
    fake_client(monkeypatch, service, [[
        raw_station(
            "123",
            44.8565,
            24.8692,
            prices={
                "gasoline_standard": 7.10,
                "gasoline_premium": 7.50,
                "diesel_standard": 7.20,
                "lpg": 3.90,
            },
        ),
    ]])

    result = service.search_nearby_stations(USER, radius_km=5)

    assert len(result.stations) == 1

    station = result.stations[0]

    assert station.station_id == "123"
    assert station.name == "Petrom - Statia 123"
    assert station.prices.gasoline.standard == 7.10
    assert station.prices.gasoline.premium == 7.50
    assert station.prices.diesel.standard == 7.20
    assert station.prices.diesel.premium is None
    assert station.prices.lpg == 3.90
    assert result.price_data_updated_at == "2026-10-07T11:05:00+03:00"


def test_sorts_by_distance_and_skips_too_far(monkeypatch, service):
    fake_client(monkeypatch, service, [[
        raw_station("departe", 44.90, 24.87),       # ~4.9 km
        raw_station("aproape", 44.857, 24.870),     # ~0.1 km
        raw_station("mijloc", 44.87, 24.87),        # ~1.5 km
        raw_station("fara-coordonate", None, None),
    ]])

    result = service.search_nearby_stations(USER, radius_km=3)

    assert [s.station_id for s in result.stations] == ["aproape", "mijloc"]
    assert result.stations[0].distance_km < result.stations[1].distance_km


def test_duplicate_stations_appear_once(monkeypatch, service):
    fake_client(monkeypatch, service, [[
        raw_station("1", 44.857, 24.870),
        raw_station("1", 44.857, 24.870),
    ]])

    result = service.search_nearby_stations(USER, radius_km=5)

    assert len(result.stations) == 1


def test_limits_number_of_stations(monkeypatch, service):
    many = [
        raw_station(str(i), 44.8565 + i * 0.0005, 24.8692)
        for i in range(settings.MAX_STATIONS + 10)
    ]
    fake_client(monkeypatch, service, [many])

    result = service.search_nearby_stations(USER, radius_km=5)

    assert len(result.stations) == settings.MAX_STATIONS


def test_small_radius_uses_one_search(monkeypatch, service):
    calls = fake_client(monkeypatch, service, [[raw_station("1", 44.857, 24.870)]])

    service.search_nearby_stations(USER, radius_km=5)

    assert len(calls) == 1


def test_large_radius_searches_around_when_few_stations(monkeypatch, service):
    center = [raw_station("centru", 44.857, 24.870)]
    ring = [raw_station("inel", 44.92, 24.8692)]  # ~7 km nord
    calls = fake_client(monkeypatch, service, [center, ring])

    result = service.search_nearby_stations(USER, radius_km=10)

    # centrul + 6 puncte pe cerc
    assert len(calls) == 7
    assert {s.station_id for s in result.stations} == {"centru", "inel"}


def test_large_radius_skips_extra_searches_when_enough_stations(monkeypatch, service):
    many = [
        raw_station(str(i), 44.8565 + i * 0.0005, 24.8692)
        for i in range(settings.MAX_STATIONS)
    ]
    calls = fake_client(monkeypatch, service, [many])

    service.search_nearby_stations(USER, radius_km=10)

    assert len(calls) == 1


def test_results_are_cached(monkeypatch, service):
    calls = fake_client(monkeypatch, service, [[raw_station("1", 44.857, 24.870)]])

    first = service.search_nearby_stations(USER, radius_km=5)

    # alt utilizator, la cativa metri distanta
    neighbour = UserLocation(latitude=44.8563, longitude=24.8694)
    second = service.search_nearby_stations(neighbour, radius_km=5)

    assert len(calls) == 1

    # fiecare primeste propria locatie si propriile distante
    assert second.location == neighbour
    assert first.stations[0].distance_km != second.stations[0].distance_km


def test_different_radius_is_not_taken_from_cache(monkeypatch, service):
    calls = fake_client(monkeypatch, service, [[raw_station("1", 44.857, 24.870)]])

    service.search_nearby_stations(USER, radius_km=5)
    service.search_nearby_stations(USER, radius_km=3)

    assert len(calls) == 2
