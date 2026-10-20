from app.models.location import UserLocation
from app.services.station_service import StationService


def test_station_service_uses_google_data(monkeypatch):
    fake_google_stations = [
        {
            "id": "google-station-1",
            "displayName": {
                "text": "Test Oil",
            },
            "formattedAddress": (
                "Strada Test 1, Bucuresti, Romania"
            ),
            "addressComponents": [
                {
                    "longText": "Bucuresti",
                    "types": ["locality"],
                },
                {
                    "longText": "Bucuresti",
                    "types": [
                        "administrative_area_level_1"
                    ],
                },
                {
                    "longText": "Romania",
                    "types": ["country"],
                },
            ],
            "location": {
                "latitude": 44.4268,
                "longitude": 26.1025,
            },
            "fuelOptions": {
                "fuelPrices": [
                    {
                        "type": "SP95",
                        "price": {
                            "currencyCode": "RON",
                            "units": "10",
                            "nanos": 120000000,
                        },
                        "updateTime": (
                            "2026-10-20T10:00:00Z"
                        ),
                    },
                    {
                        "type": "SP100",
                        "price": {
                            "currencyCode": "RON",
                            "units": "10",
                            "nanos": 690000000,
                        },
                        "updateTime": (
                            "2026-10-20T10:00:00Z"
                        ),
                    },
                    {
                        "type": "DIESEL",
                        "price": {
                            "currencyCode": "RON",
                            "units": "10",
                            "nanos": 920000000,
                        },
                        "updateTime": (
                            "2026-10-20T10:00:00Z"
                        ),
                    },
                    {
                        "type": "DIESEL_PLUS",
                        "price": {
                            "currencyCode": "RON",
                            "units": "11",
                            "nanos": 810000000,
                        },
                        "updateTime": (
                            "2026-10-20T10:00:00Z"
                        ),
                    },
                ]
            },
        }
    ]

    fake_routes = {
        0: {
            "distance_km": 1.44,
            "duration_minutes": 4.8,
        }
    }

    def fake_places_get_stations(
        self,
        latitude,
        longitude,
        radius_km,
        max_results=None,
    ):
        return fake_google_stations

    def fake_route_matrix(
        self,
        origin_latitude,
        origin_longitude,
        destinations,
    ):
        return fake_routes

    monkeypatch.setattr(
        "app.clients.google_places_client."
        "GooglePlacesClient.get_stations",
        fake_places_get_stations,
    )

    monkeypatch.setattr(
        "app.clients.google_routes_client."
        "GoogleRoutesClient.get_route_matrix",
        fake_route_matrix,
    )

    service = StationService()

    location = UserLocation(
        latitude=44.4268,
        longitude=26.1025,
    )

    response = service.search_nearby_stations(
        location=location,
        radius_km=5,
    )

    assert len(response.stations) == 1

    station = response.stations[0]

    assert station.station_id == "google-station-1"
    assert station.name == "Test Oil"
    assert station.brand == "Test Oil"

    assert station.city == "Bucuresti"
    assert station.county == "Bucuresti"
    assert station.country == "Romania"

    assert station.distance_km == 1.44
    assert station.duration_minutes == 4.8

    assert (
        station.prices.gasoline.standard.value
        == 10.12
    )

    assert (
        station.prices.gasoline.premium.value
        == 10.69
    )

    assert (
        station.prices.diesel.standard.value
        == 10.92
    )

    assert (
        station.prices.diesel.premium.value
        == 11.81
    )

    assert (
        station.prices.gasoline.standard.updated_at
        == "2026-10-20T10:00:00Z"
    )

    assert (
        station.prices.gasoline.standard.level
        == "medium"
    )