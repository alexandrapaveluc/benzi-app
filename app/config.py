import os

from dotenv import load_dotenv


load_dotenv()


class Settings:

    # Google Maps Platform
    GOOGLE_MAPS_API_KEY: str = os.getenv(
        "GOOGLE_MAPS_API_KEY",
        "",
    )

    GOOGLE_PLACES_URL: str = (
        "https://places.googleapis.com/v1/places:searchNearby"
    )

    GOOGLE_ROUTES_MATRIX_URL: str = (
        "https://routes.googleapis.com/distanceMatrix/v2:computeRouteMatrix"
    )

    # Configurare aplicație
    DEFAULT_RADIUS_KM: float = float(
        os.getenv("DEFAULT_RADIUS_KM", "10")
    )

    MAX_STATIONS: int = int(
        os.getenv("MAX_STATIONS", "20")
    )

    API_TIMEOUT_SECONDS: int = int(
        os.getenv("API_TIMEOUT_SECONDS", "10")
    )


settings = Settings()