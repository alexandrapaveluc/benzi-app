import os

from dotenv import load_dotenv


load_dotenv()


class Settings:
    MONITORUL_PRETURILOR_BASE_URL: str = os.getenv(
        "MONITORUL_PRETURILOR_BASE_URL",
        "https://monitorulpreturilor.info/pmonsvc/Gas",
    )

    DEFAULT_RADIUS_KM: float = float(
        os.getenv("DEFAULT_RADIUS_KM", "10")
    )

    # Monitorul Preturilor raspunde pe o raza de maxim 5 km pe cerere;
    # pana la 10 km acoperim zona cu mai multe cereri (vezi StationService)
    MAX_RADIUS_KM: float = float(
        os.getenv("MAX_RADIUS_KM", "10")
    )

    MAX_STATIONS: int = int(
        os.getenv("MAX_STATIONS", "20")
    )

    API_TIMEOUT_SECONDS: int = int(
        os.getenv("API_TIMEOUT_SECONDS", "15")
    )

    # Cat timp pastram rezultatele unei cautari, ca sa nu cerem
    # aceleasi date de fiecare data
    CACHE_TTL_SECONDS: int = int(
        os.getenv("CACHE_TTL_SECONDS", "900")
    )

    # Domeniile care pot apela API-ul din browser, separate prin virgula
    CORS_ORIGINS: list[str] = [
        origin.strip()
        for origin in os.getenv("CORS_ORIGINS", "*").split(",")
        if origin.strip()
    ]


settings = Settings()
