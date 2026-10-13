import pytest
from fastapi.testclient import TestClient

from app.clients.monitorul_preturilor_client import PriceProviderError
from app.main import app
from app.models.fuel_prices import DieselPrices, FuelPrices, GasolinePrices
from app.models.location import UserLocation
from app.models.station import FuelStation
from app.models.station_response import StationSearchResponse
from app.routers import station_router


client = TestClient(app)


@pytest.fixture
def fake_search(monkeypatch):
    calls = []

    def search(location, radius_km):
        calls.append((location, radius_km))
        return StationSearchResponse(
            location=location,
            radius_km=radius_km,
            price_data_updated_at="2026-10-07T11:05:00+03:00",
            stations=[
                FuelStation(
                    station_id="1",
                    name="Petrom - Test",
                    brand="Petrom",
                    latitude=44.857,
                    longitude=24.870,
                    distance_km=0.1,
                    prices=FuelPrices(
                        gasoline=GasolinePrices(standard=10.05),
                        diesel=DieselPrices(standard=10.91),
                        lpg=4.71,
                    ),
                ),
            ],
        )

    monkeypatch.setattr(station_router.station_service, "search_nearby_stations", search)
    return calls


def test_health():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_nearby_returns_stations(fake_search):
    response = client.get(
        "/stations/nearby",
        params={"latitude": 44.8565, "longitude": 24.8692, "radius_km": 5},
    )

    assert response.status_code == 200

    data = response.json()
    assert data["radius_km"] == 5
    assert data["stations"][0]["prices"]["gasoline"]["standard"] == 10.05
    assert data["stations"][0]["prices"]["lpg"] == 4.71
    assert fake_search[0] == (UserLocation(latitude=44.8565, longitude=24.8692), 5)


def test_default_radius_is_used(fake_search):
    client.get("/stations/nearby", params={"latitude": 44.8565, "longitude": 24.8692})

    assert fake_search[0][1] == 10


@pytest.mark.parametrize(
    "params",
    [
        {"latitude": 200, "longitude": 24.8692},
        {"latitude": 44.8565, "longitude": -500},
        {"latitude": 44.8565, "longitude": 24.8692, "radius_km": 0},
        {"latitude": 44.8565, "longitude": 24.8692, "radius_km": 11},
        {"longitude": 24.8692},
    ],
)
def test_invalid_parameters_are_rejected(fake_search, params):
    response = client.get("/stations/nearby", params=params)

    assert response.status_code == 422
    assert fake_search == []


def test_provider_error_returns_502(monkeypatch):
    def failing_search(location, radius_km):
        raise PriceProviderError("Monitorul Preturilor nu a raspuns la timp.")

    monkeypatch.setattr(
        station_router.station_service,
        "search_nearby_stations",
        failing_search,
    )

    response = client.get(
        "/stations/nearby",
        params={"latitude": 44.8565, "longitude": 24.8692},
    )

    assert response.status_code == 502
    assert response.json()["detail"] == "Monitorul Preturilor nu a raspuns la timp."


def test_cors_allows_browser_requests():
    response = client.get("/health", headers={"Origin": "https://exemplu.ro"})

    assert response.headers["access-control-allow-origin"] == "*"
