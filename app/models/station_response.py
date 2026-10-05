from pydantic import BaseModel

from app.models.location import UserLocation
from app.models.station import FuelStation


class StationSearchResponse(BaseModel):
    location: UserLocation
    radius_km: float
    price_data_updated_at: str | None = None
    stations: list[FuelStation]