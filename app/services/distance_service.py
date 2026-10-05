from math import atan2, cos, radians, sin, sqrt


class DistanceService:
    EARTH_RADIUS_KM = 6371.0

    @classmethod
    def calculate_distance_km(
        cls,
        latitude_1: float,
        longitude_1: float,
        latitude_2: float,
        longitude_2: float,
    ) -> float:
        lat1 = radians(latitude_1)
        lon1 = radians(longitude_1)

        lat2 = radians(latitude_2)
        lon2 = radians(longitude_2)

        delta_lat = lat2 - lat1
        delta_lon = lon2 - lon1

        a = (
            sin(delta_lat / 2) ** 2
            + cos(lat1)
            * cos(lat2)
            * sin(delta_lon / 2) ** 2
        )

        c = 2 * atan2(
            sqrt(a),
            sqrt(1 - a),
        )

        return cls.EARTH_RADIUS_KM * c