from app.clients.pretcarburant_client import PretCarburantClient
from app.config import settings
from app.models.fuel_prices import (
    DieselPrices,
    FuelPrices,
    GasolinePrices,
)
from app.models.location import UserLocation
from app.models.station import FuelStation
from app.models.station_response import StationSearchResponse
from app.services.distance_service import DistanceService


class StationService:
    def __init__(self):
        self.client = PretCarburantClient(
            base_url=settings.PRET_CARBURANT_BASE_URL,
            api_key=settings.PRET_CARBURANT_API_KEY,
            timeout=settings.API_TIMEOUT_SECONDS,
        )

    def search_nearby_stations(
        self,
        location: UserLocation,
        radius_km: float,
    ) -> StationSearchResponse:

        data = self.client.get_stations(
            latitude=location.latitude,
            longitude=location.longitude,
            radius_km=radius_km,
        )

        raw_stations = data.get("statii", [])

        stations_by_id = {}

        for raw_station in raw_stations:
            station_id = str(raw_station.get("id"))

            if station_id not in stations_by_id:
                stations_by_id[station_id] = {
                    "id": station_id,
                    "brand": raw_station.get("brand"),
                    "address": raw_station.get("adresa"),
                    "city": raw_station.get("oras"),
                    "county": raw_station.get("judet"),
                    "latitude": raw_station.get("lat"),
                    "longitude": raw_station.get("lng"),
                    "gasoline_standard": None,
                    "gasoline_premium": None,
                    "diesel_standard": None,
                    "diesel_premium": None,
                }

            fuel_type = raw_station.get("tip")
            price = raw_station.get("pret")

            if fuel_type == "benzina_standard":
                stations_by_id[station_id]["gasoline_standard"] = price

            elif fuel_type == "benzina_premium":
                stations_by_id[station_id]["gasoline_premium"] = price

            elif fuel_type == "motorina_standard":
                stations_by_id[station_id]["diesel_standard"] = price

            elif fuel_type == "motorina_premium":
                stations_by_id[station_id]["diesel_premium"] = price

        stations = []

        for station_data in stations_by_id.values():
            latitude = station_data["latitude"]
            longitude = station_data["longitude"]

            if latitude is None or longitude is None:
                continue

            distance = DistanceService.calculate_distance_km(
                location.latitude,
                location.longitude,
                latitude,
                longitude,
            )

            brand = station_data["brand"]
            city = station_data["city"]

            if brand and city:
                name = f"{brand} - {city}"
            elif brand:
                name = brand
            else:
                name = "Benzinarie"

            station = FuelStation(
                station_id=station_data["id"],
                name=name,
                brand=brand,
                address=station_data["address"],
                city=city,
                county=station_data["county"],
                latitude=latitude,
                longitude=longitude,
                distance_km=round(distance, 2),
                prices=FuelPrices(
                    gasoline=GasolinePrices(
                        standard=station_data["gasoline_standard"],
                        premium=station_data["gasoline_premium"],
                    ),
                    diesel=DieselPrices(
                        standard=station_data["diesel_standard"],
                        premium=station_data["diesel_premium"],
                    ),
                ),
            )

            stations.append(station)

        stations.sort(key=lambda station: station.distance_km)

        stations = stations[:settings.MAX_STATIONS]

        return StationSearchResponse(
            location=location,
            radius_km=radius_km,
            price_data_updated_at=data.get("actualizat_la"),
            stations=stations,
        )