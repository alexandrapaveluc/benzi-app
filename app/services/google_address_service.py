from typing import Any


class GoogleAddressService:
    @staticmethod
    def extract_address(
        google_station: dict[str, Any],
    ) -> dict[str, str | None]:

        components = google_station.get(
            "addressComponents",
            [],
        )

        city = None
        county = None
        country = None

        for component in components:
            types = component.get("types", [])
            name = component.get("longText")

            if "locality" in types:
                city = name

            elif "administrative_area_level_1" in types:
                county = name

            elif "country" in types:
                country = name

        return {
            "city": city,
            "county": county,
            "country": country,
        }