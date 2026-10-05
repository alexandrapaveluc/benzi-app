import os

from dotenv import load_dotenv


load_dotenv()


class Settings:
    PRET_CARBURANT_BASE_URL: str = os.getenv(
        "PRET_CARBURANT_BASE_URL",
        "https://pretcarburant.ro/api/v1",
    )

    PRET_CARBURANT_API_KEY: str | None = os.getenv(
        "PRET_CARBURANT_API_KEY"
    )

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