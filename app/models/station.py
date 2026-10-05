from pydantic import BaseModel, Field

from app.models.fuel_prices import FuelPrices


class FuelStation(BaseModel):
    station_id: str
    name: str
    brand: str | None = None
    address: str | None = None
    city: str | None = None
    county: str | None = None

    latitude: float
    longitude: float

    distance_km: float = Field(ge=0)

    prices: FuelPrices