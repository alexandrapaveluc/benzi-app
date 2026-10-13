from fastapi import APIRouter, HTTPException, Query

from app.clients.monitorul_preturilor_client import PriceProviderError
from app.config import settings
from app.models.location import UserLocation
from app.models.station_response import StationSearchResponse
from app.services.station_service import StationService


router = APIRouter(
    prefix="/stations",
    tags=["Stations"],
)


station_service = StationService()


@router.get(
    "/nearby",
    response_model=StationSearchResponse,
)
def get_nearby_stations(
    latitude: float = Query(
        ...,
        ge=-90,
        le=90,
        description="Latitudinea utilizatorului",
    ),
    longitude: float = Query(
        ...,
        ge=-180,
        le=180,
        description="Longitudinea utilizatorului",
    ),
    radius_km: float = Query(
        settings.DEFAULT_RADIUS_KM,
        gt=0,
        le=settings.MAX_RADIUS_KM,
        description="Raza de cautare in kilometri",
    ),
):
    location = UserLocation(
        latitude=latitude,
        longitude=longitude,
    )

    try:
        return station_service.search_nearby_stations(
            location=location,
            radius_km=radius_km,
        )

    except PriceProviderError as error:
        raise HTTPException(
            status_code=502,
            detail=str(error),
        )