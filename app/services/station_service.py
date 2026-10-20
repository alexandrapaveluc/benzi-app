from app.clients.google_places_client import (
    GooglePlacesClient,
)
from app.clients.google_routes_client import (
    GoogleRoutesClient,
)
from app.config import settings
from app.models.location import UserLocation
from app.models.station import FuelStation
from app.models.station_response import (
    StationSearchResponse,
)
from app.services.distance_service import (
    DistanceService,
)
from app.services.google_address_service import (
    GoogleAddressService,
)
from app.services.google_fuel_price_service import (
    GoogleFuelPriceService,
)
from app.services.price_classification_service import (
    PriceClassificationService,
)


class StationService:
    def __init__(self):
        self.google_places_client = (
            GooglePlacesClient()
        )

        self.google_routes_client = (
            GoogleRoutesClient()
        )

    def search_nearby_stations(
        self,
        location: UserLocation,
        radius_km: float,
    ) -> StationSearchResponse:

        # 1. Google Places:
        # benzinarii + adrese + preturi.
        google_stations = (
            self.google_places_client.get_stations(
                latitude=location.latitude,
                longitude=location.longitude,
                radius_km=radius_km,
                max_results=settings.MAX_STATIONS,
            )
        )

        # 2. Eliminam rezultatele fara coordonate.
        valid_stations = []

        for station in google_stations:
            google_location = station.get(
                "location",
                {},
            )

            latitude = google_location.get(
                "latitude"
            )

            longitude = google_location.get(
                "longitude"
            )

            if (
                latitude is None
                or longitude is None
            ):
                continue

            valid_stations.append(station)

        # 3. Pregatim destinatiile pentru Routes.
        destinations = [
            {
                "latitude": station[
                    "location"
                ]["latitude"],
                "longitude": station[
                    "location"
                ]["longitude"],
            }
            for station in valid_stations
        ]

        # 4. Google Routes:
        # distanta si durata cu masina.
        routes = {}

        if destinations:
            try:
                routes = (
                    self.google_routes_client
                    .get_route_matrix(
                        origin_latitude=(
                            location.latitude
                        ),
                        origin_longitude=(
                            location.longitude
                        ),
                        destinations=destinations,
                    )
                )

            except RuntimeError:
                # Fallback: distanta geometrica.
                routes = {}

        stations = []

        # 5. Construim fiecare benzinarie.
        for index, google_station in enumerate(
            valid_stations
        ):
            google_location = google_station[
                "location"
            ]

            latitude = float(
                google_location["latitude"]
            )

            longitude = float(
                google_location["longitude"]
            )

            display_name = google_station.get(
                "displayName",
                {},
            )

            name = (
                display_name.get("text")
                or "Benzinarie"
            )

            address = google_station.get(
                "formattedAddress"
            )

            address_data = (
                GoogleAddressService
                .extract_address(
                    google_station
                )
            )

            prices = (
                GoogleFuelPriceService
                .extract_prices(
                    google_station
                )
            )

            route = routes.get(index)

            if route:
                distance_km = route[
                    "distance_km"
                ]

                duration_minutes = route[
                    "duration_minutes"
                ]

            else:
                distance_km = (
                    DistanceService
                    .calculate_distance_km(
                        location.latitude,
                        location.longitude,
                        latitude,
                        longitude,
                    )
                )

                distance_km = round(
                    distance_km,
                    2,
                )

                duration_minutes = None

            station = FuelStation(
                station_id=google_station.get(
                    "id",
                    f"google-{index}",
                ),
                name=name,
                brand=name,
                address=address,
                city=address_data["city"],
                county=address_data["county"],
                country=address_data["country"],
                latitude=latitude,
                longitude=longitude,
                distance_km=distance_km,
                duration_minutes=(
                    duration_minutes
                ),
                prices=prices,
            )

            stations.append(station)

        # 6. Clasificam preturile.
        PriceClassificationService.classify_stations(
            stations
        )

        # 7. Cea mai apropiata statie prima.
        stations.sort(
            key=lambda station: (
                station.distance_km
            )
        )

        return StationSearchResponse(
            location=location,
            radius_km=radius_km,
            price_data_updated_at=None,
            stations=stations,
        )