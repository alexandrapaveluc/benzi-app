from app.models.location import UserLocation
from app.services.station_service import StationService


def test_station_service_aggregates_fuel_prices(monkeypatch):

    fake_response = {
        "status": "ok",
        "actualizat_la": "2026-10-05T12:00:00+00:00",
        "statii": [
            {
                "id": "123",
                "brand": "Test Oil",
                "adresa": "Strada Test 1",
                "oras": "Pitesti",
                "judet": "Arges",
                "lat": 44.8565,
                "lng": 24.8692,
                "tip": "benzina_standard",
                "pret": 7.10,
            },
            {
                "id": "123",
                "brand": "Test Oil",
                "adresa": "Strada Test 1",
                "oras": "Pitesti",
                "judet": "Arges",
                "lat": 44.8565,
                "lng": 24.8692,
                "tip": "benzina_premium",
                "pret": 7.50,
            },
            {
                "id": "123",
                "brand": "Test Oil",
                "adresa": "Strada Test 1",
                "oras": "Pitesti",
                "judet": "Arges",
                "lat": 44.8565,
                "lng": 24.8692,
                "tip": "motorina_standard",
                "pret": 7.20,
            },
        ],
    }

    def fake_get_stations(
        self,
        latitude,
        longitude,
        radius_km,
    ):
        return fake_response

    monkeypatch.setattr(
        "app.clients.pretcarburant_client.PretCarburantClient.get_stations",
        fake_get_stations,
    )

    service = StationService()

    result = service.search_nearby_stations(
        location=UserLocation(
            latitude=44.8565,
            longitude=24.8692,
        ),
        radius_km=10,
    )

    assert len(result.stations) == 1

    station = result.stations[0]

    assert station.station_id == "123"
    assert station.prices.gasoline.standard == 7.10
    assert station.prices.gasoline.premium == 7.50
    assert station.prices.diesel.standard == 7.20
    assert station.prices.diesel.premium is None