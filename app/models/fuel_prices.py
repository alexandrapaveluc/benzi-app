from pydantic import BaseModel


class GasolinePrices(BaseModel):
    standard: float | None = None
    premium: float | None = None


class DieselPrices(BaseModel):
    standard: float | None = None
    premium: float | None = None


class FuelPrices(BaseModel):
    gasoline: GasolinePrices
    diesel: DieselPrices