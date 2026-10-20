from typing import Any

from app.models.fuel_prices import (
    DieselPrices,
    FuelPrice,
    FuelPrices,
    GasolinePrices,
)


class GoogleFuelPriceService:
    @staticmethod
    def _money_to_float(
        price: dict[str, Any] | None,
    ) -> float | None:
        if not price:
            return None

        try:
            units = int(price.get("units", 0))
            nanos = int(price.get("nanos", 0))

            return round(
                units + nanos / 1_000_000_000,
                2,
            )

        except (TypeError, ValueError):
            return None

    @classmethod
    def extract_prices(
        cls,
        google_station: dict[str, Any],
    ) -> FuelPrices:

        fuel_options = (
            google_station.get("fuelOptions") or {}
        )

        fuel_prices = fuel_options.get(
            "fuelPrices",
            [],
        )

        gasoline_standard = None
        gasoline_premium_candidates = []

        diesel_standard = None
        diesel_premium = None

        for fuel in fuel_prices:
            fuel_type = fuel.get("type")

            value = cls._money_to_float(
                fuel.get("price")
            )

            if value is None:
                continue

            price_data = {
                "value": value,
                "updated_at": fuel.get("updateTime"),
            }

            if fuel_type == "SP95":
                gasoline_standard = price_data

            elif fuel_type in {
                "SP98",
                "SP99",
                "SP100",
            }:
                gasoline_premium_candidates.append(
                    price_data
                )

            elif fuel_type == "DIESEL":
                diesel_standard = price_data

            elif fuel_type == "DIESEL_PLUS":
                diesel_premium = price_data

        gasoline_premium = None

        if gasoline_premium_candidates:
            gasoline_premium = min(
                gasoline_premium_candidates,
                key=lambda item: item["value"],
            )

        return FuelPrices(
            gasoline=GasolinePrices(
                standard=FuelPrice(
                    **gasoline_standard
                )
                if gasoline_standard
                else FuelPrice(),
                premium=FuelPrice(
                    **gasoline_premium
                )
                if gasoline_premium
                else FuelPrice(),
            ),
            diesel=DieselPrices(
                standard=FuelPrice(
                    **diesel_standard
                )
                if diesel_standard
                else FuelPrice(),
                premium=FuelPrice(
                    **diesel_premium
                )
                if diesel_premium
                else FuelPrice(),
            ),
        )