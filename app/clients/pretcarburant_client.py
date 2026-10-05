from typing import Any

import requests


class PretCarburantClient:
    def __init__(
        self,
        base_url: str,
        api_key: str | None = None,
        timeout: int = 10,
    ):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout

    def _build_headers(self) -> dict[str, str]:
        headers = {}

        if self.api_key:
            headers["X-Api-Key"] = self.api_key

        return headers

    def get_stations(
        self,
        latitude: float,
        longitude: float,
        radius_km: float,
    ) -> dict[str, Any]:
        url = f"{self.base_url}/statii"

        params = {
            "lat": latitude,
            "lon": longitude,
            "raza": radius_km,
        }

        response = requests.get(
            url,
            params=params,
            headers=self._build_headers(),
            timeout=self.timeout,
        )

        if response.status_code == 429:
            raise RuntimeError(
                "PretCarburant API: limita de cereri a fost depasita."
            )

        if response.status_code == 401:
            raise RuntimeError(
                "PretCarburant API: cheia API nu este valida."
            )

        response.raise_for_status()

        data = response.json()

        if data.get("status") != "ok":
            raise RuntimeError(
                "PretCarburant API a returnat un raspuns invalid."
            )

        return data