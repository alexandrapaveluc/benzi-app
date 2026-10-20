from typing import Any

import requests

from app.config import settings


class GooglePlacesClient:
    def __init__(self):
        self.url = settings.GOOGLE_PLACES_URL
        self.api_key = settings.GOOGLE_MAPS_API_KEY
        self.timeout = settings.API_TIMEOUT_SECONDS

    def get_stations(
        self,
        latitude: float,
        longitude: float,
        radius_km: float,
        max_results: int | None = None,
    ) -> list[dict[str, Any]]:

        if not self.api_key:
            raise RuntimeError(
                "Lipseste GOOGLE_MAPS_API_KEY din fisierul .env."
            )

        radius_meters = radius_km * 1000

        limit = max_results or settings.MAX_STATIONS
        limit = max(1, min(limit, 20))

        headers = {
            "Content-Type": "application/json",
            "X-Goog-Api-Key": self.api_key,
            "X-Goog-FieldMask": (
                "places.id,"
                "places.displayName,"
                "places.formattedAddress,"
                "places.addressComponents,"
                "places.location,"
                "places.fuelOptions"
            ),
        }

        body = {
            "includedTypes": ["gas_station"],
            "maxResultCount": limit,
            "rankPreference": "DISTANCE",
            "locationRestriction": {
                "circle": {
                    "center": {
                        "latitude": latitude,
                        "longitude": longitude,
                    },
                    "radius": radius_meters,
                }
            },
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
                "Google Places nu a raspuns la timp."
            ) from exc

        except requests.RequestException as exc:
            raise RuntimeError(
                f"Nu s-a putut contacta Google Places: {exc}"
            ) from exc

        if response.status_code == 429:
            raise RuntimeError(
                "Google Places: limita de cereri a fost depasita."
            )

        if not response.ok:
            raise RuntimeError(
                f"Google Places HTTP {response.status_code}: "
                f"{response.text}"
            )

        data = response.json()

        return data.get("places", [])