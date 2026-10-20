from pydantic import BaseModel


class FuelPrice(BaseModel):
    value: float | None = None
    level: str | None = None
    updated_at: str | None = None


class GasolinePrices(BaseModel):
    standard: FuelPrice
    premium: FuelPrice


class DieselPrices(BaseModel):
    standard: FuelPrice
    premium: FuelPrice


class FuelPrices(BaseModel):
    gasoline: GasolinePrices
    diesel: DieselPrices