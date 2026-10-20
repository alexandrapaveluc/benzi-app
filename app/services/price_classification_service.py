from app.models.station import FuelStation


class PriceClassificationService:
    @classmethod
    def classify_stations(
        cls,
        stations: list[FuelStation],
    ) -> None:

        price_paths = [
            ("gasoline", "standard"),
            ("gasoline", "premium"),
            ("diesel", "standard"),
            ("diesel", "premium"),
        ]

        for fuel_group, fuel_type in price_paths:
            prices = []

            for station in stations:
                group = getattr(
                    station.prices,
                    fuel_group,
                )

                fuel_price = getattr(
                    group,
                    fuel_type,
                )

                if fuel_price.value is not None:
                    prices.append(
                        fuel_price.value
                    )

            for station in stations:
                group = getattr(
                    station.prices,
                    fuel_group,
                )

                fuel_price = getattr(
                    group,
                    fuel_type,
                )

                fuel_price.level = cls._classify(
                    fuel_price.value,
                    prices,
                )

    @staticmethod
    def _classify(
        price: float | None,
        prices: list[float],
    ) -> str | None:

        if price is None or not prices:
            return None

        minimum = min(prices)
        maximum = max(prices)

        if minimum == maximum:
            return "medium"

        price_range = maximum - minimum

        low_limit = minimum + price_range / 3
        high_limit = minimum + (
            2 * price_range / 3
        )

        if price <= low_limit:
            return "low"

        if price >= high_limit:
            return "high"

        return "medium"