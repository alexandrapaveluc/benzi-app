from typing import Any

import requests

from app.config import settings


class GoogleRoutesClient:
    def __init__(self):
        self.url = settings.GOOGLE_ROUTES_MATRIX_URL
        self.api_key = settings.GOOGLE_MAPS_API_KEY
        self.timeout = settings.API_TIMEOUT_SECONDS

    def get_route_matrix(
        self,
        origin_latitude: float,
        origin_longitude: float,
        destinations: list[dict[str, float]],
    ) -> dict[int, dict[str, Any]]:

        if not self.api_key:
            raise RuntimeError(
                "Lipseste GOOGLE_MAPS_API_KEY din fisierul .env."
            )

        if not destinations:
            return {}

        headers = {
            "Content-Type": "application/json",
            "X-Goog-Api-Key": self.api_key,
            "X-Goog-FieldMask": (
                "originIndex,"
                "destinationIndex,"
                "status,"
                "condition,"
                "distanceMeters,"
                "duration"
            ),
        }

        body = {
            "origins": [
                {
                    "waypoint": {
                        "location": {
                            "latLng": {
                                "latitude": origin_latitude,
                                "longitude": origin_longitude,
                            }
                        }
                    }
                }
            ],
            "destinations": [
                {
                    "waypoint": {
                        "location": {
                            "latLng": {
                                "latitude": destination["latitude"],
                                "longitude": destination["longitude"],
                            }
                        }
                    }
                }
                for destination in destinations
            ],
            "travelMode": "DRIVE",
            "routingPreference": "TRAFFIC_UNAWARE",
        }

        try:
            response = requests.post(
                self.url,
                headers=headers,
                json=body,
                timeout=self.timeout,
            )
        except requests.Timeout as exc:
            raise RuntimeError(
                "Google Routes nu a raspuns la timp."
            ) from exc
        except requests.RequestException as exc:
            raise RuntimeError(
                f"Nu s-a putut contacta Google Routes: {exc}"
            ) from exc

        if response.status_code == 429:
            raise RuntimeError(
                "Google Routes: limita de cereri a fost depasita."
            )

        if response.status_code in (401, 403):
            raise RuntimeError(
                "Google Routes: verifica cheia API si permisiunile."
            )

        if not response.ok:
            raise RuntimeError(
                f"Google Routes HTTP {response.status_code}: "
                f"{response.text}"
            )

        elements = response.json()
        routes: dict[int, dict[str, Any]] = {}

        for element in elements:
            destination_index = element.get("destinationIndex")

            if destination_index is None:
                continue

            if element.get("condition") != "ROUTE_EXISTS":
                continue

            distance_meters = element.get("distanceMeters")
            duration = element.get("duration", "0s")

            if distance_meters is None:
                continue

            duration_seconds = self._parse_duration_seconds(duration)

            routes[destination_index] = {
                "distance_km": round(distance_meters / 1000, 2),
                "duration_minutes": round(duration_seconds / 60, 1),
            }

        return routes

    @staticmethod
    def _parse_duration_seconds(duration: str) -> float:
        if not duration.endswith("s"):
            return 0.0

        try:
            return float(duration[:-1])
        except ValueError:
            return 0.0