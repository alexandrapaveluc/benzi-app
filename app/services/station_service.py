from math import cos, radians, sin

from app.clients.monitorul_preturilor_client import (
    MAX_BUFFER_METERS,
    MonitorulPreturilorClient,
)
from app.config import settings
from app.models.fuel_prices import (
    DieselPrices,
    FuelPrices,
    GasolinePrices,
)
from app.models.location import UserLocation
from app.models.station import FuelStation
from app.models.station_response import StationSearchResponse
from app.services.cache_service import TTLCache
from app.services.distance_service import DistanceService


# Un cerc de cautare al Monitorului Preturilor are maxim 5 km
PROVIDER_RADIUS_KM = MAX_BUFFER_METERS / 1000

# Pentru raze mai mari de 5 km mai cautam in 6 puncte asezate pe un cerc
# la 7.5 km de utilizator. Impreuna cu cercul din centru acopera tot
# pana la ~9.8 km.
RING_DISTANCE_KM = 7.5
RING_POINTS = 6

KM_PER_DEGREE_LATITUDE = 111.32


class StationService:
    def __init__(self):
        self.client = MonitorulPreturilorClient(
            base_url=settings.MONITORUL_PRETURILOR_BASE_URL,
            timeout=settings.API_TIMEOUT_SECONDS,
        )
        self.cache = TTLCache(ttl_seconds=settings.CACHE_TTL_SECONDS)

    def search_nearby_stations(
        self,
        location: UserLocation,
        radius_km: float,
    ) -> StationSearchResponse:

        raw_stations = self._get_raw_stations(location, radius_km)

        stations = self._build_stations(location, raw_stations, radius_km)
        stations = stations[:settings.MAX_STATIONS]

        update_dates = [
            station.price_updated_at
            for station in stations
            if station.price_updated_at
        ]

        return StationSearchResponse(
            location=location,
            radius_km=radius_km,
            price_data_updated_at=max(update_dates) if update_dates else None,
            stations=stations,
        )

    def _get_raw_stations(
        self,
        location: UserLocation,
        radius_km: float,
    ) -> list[dict]:

        # Cautam in jurul coordonatelor rotunjite la ~100 m, ca utilizatorii
        # apropiati sa foloseasca aceleasi date din cache. Distantele se
        # calculeaza apoi fata de pozitia exacta a fiecarui utilizator.
        search_center = UserLocation(
            latitude=round(location.latitude, 3),
            longitude=round(location.longitude, 3),
        )
        cache_key = (search_center.latitude, search_center.longitude, radius_km)

        cached = self.cache.get(cache_key)
        if cached is not None:
            return cached

        raw_stations = self.client.get_stations(
            latitude=search_center.latitude,
            longitude=search_center.longitude,
            radius_km=radius_km,
        )

        # Daca in primii 5 km sunt destule benzinarii, ele sunt oricum
        # cele mai apropiate. Altfel cautam si in jurul cercului din centru.
        found = self._build_stations(search_center, raw_stations, radius_km)

        if radius_km > PROVIDER_RADIUS_KM and len(found) < settings.MAX_STATIONS:
            for latitude, longitude in self._ring_points(search_center):
                raw_stations += self.client.get_stations(
                    latitude=latitude,
                    longitude=longitude,
                    radius_km=PROVIDER_RADIUS_KM,
                )

        self.cache.set(cache_key, raw_stations)
        return raw_stations

    @staticmethod
    def _ring_points(location: UserLocation) -> list[tuple[float, float]]:
        points = []

        for index in range(RING_POINTS):
            angle = radians(360 / RING_POINTS * index)

            delta_latitude = RING_DISTANCE_KM * cos(angle) / KM_PER_DEGREE_LATITUDE
            delta_longitude = (
                RING_DISTANCE_KM
                * sin(angle)
                / (KM_PER_DEGREE_LATITUDE * cos(radians(location.latitude)))
            )

            points.append(
                (
                    location.latitude + delta_latitude,
                    location.longitude + delta_longitude,
                )
            )

        return points

    @staticmethod
    def _build_stations(
        location: UserLocation,
        raw_stations: list[dict],
        radius_km: float,
    ) -> list[FuelStation]:

        stations_by_id: dict[str, FuelStation] = {}

        for raw_station in raw_stations:
            station_id = raw_station["id"]
            latitude = raw_station["latitude"]
            longitude = raw_station["longitude"]

            if station_id in stations_by_id:
                continue

            if latitude is None or longitude is None:
                continue

            distance = DistanceService.calculate_distance_km(
                location.latitude,
                location.longitude,
                latitude,
                longitude,
            )

            if distance > radius_km:
                continue

            brand = raw_station["brand"]
            station_name = raw_station["name"]

            if brand and station_name:
                name = f"{brand} - {station_name}"
            else:
                name = brand or station_name or "Benzinarie"

            prices = raw_station["prices"]

            stations_by_id[station_id] = FuelStation(
                station_id=station_id,
                name=name,
                brand=brand,
                address=raw_station["address"],
                latitude=latitude,
                longitude=longitude,
                distance_km=round(distance, 2),
                price_updated_at=raw_station["updated_at"],
                prices=FuelPrices(
                    gasoline=GasolinePrices(
                        standard=prices.get("gasoline_standard"),
                        premium=prices.get("gasoline_premium"),
                    ),
                    diesel=DieselPrices(
                        standard=prices.get("diesel_standard"),
                        premium=prices.get("diesel_premium"),
                    ),
                    lpg=prices.get("lpg"),
                ),
            )

        return sorted(
            stations_by_id.values(),
            key=lambda station: station.distance_km,
        )
