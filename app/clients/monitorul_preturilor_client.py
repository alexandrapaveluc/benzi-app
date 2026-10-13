import ssl
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from functools import lru_cache
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

import certifi
import requests
from requests.adapters import HTTPAdapter


# Serverul Monitorului Preturilor nu trimite certificatul intermediar.
# Il adaugam noi (certificatul oficial Sectigo), ca verificarea HTTPS
# sa mearga pe orice sistem, inclusiv pe Render.
INTERMEDIATE_CERT = Path(__file__).resolve().parent.parent / "certs" / "sectigo-dv-r36.pem"

XML_NAMESPACE = {
    "n": "http://schemas.datacontract.org/2004/07/pmonsvc.Models.Protos",
}

# Id-urile carburantilor din catalogul Monitorului Preturilor
FUEL_PRODUCTS = {
    11: "gasoline_standard",
    12: "gasoline_premium",
    21: "diesel_standard",
    22: "diesel_premium",
    31: "lpg",
}

BRANDS = {
    "PETROM": "Petrom",
    "OMV": "OMV",
    "ROMPETROL": "Rompetrol",
    "MOL": "MOL",
    "LUKOIL": "Lukoil",
    "SOCAR": "SOCAR",
    "GAZPROM": "Gazprom",
}

ROMANIA_TIMEZONE = ZoneInfo("Europe/Bucharest")

# Raza maxima la care serverul mai raspunde
MAX_BUFFER_METERS = 5000


class PriceProviderError(RuntimeError):
    pass


class _ExtraCertificateAdapter(HTTPAdapter):
    def __init__(self, ssl_context: ssl.SSLContext, **kwargs):
        self._ssl_context = ssl_context
        super().__init__(**kwargs)

    def init_poolmanager(self, *args, **kwargs):
        kwargs["ssl_context"] = self._ssl_context
        return super().init_poolmanager(*args, **kwargs)


@lru_cache(maxsize=1)
def _ssl_context() -> ssl.SSLContext:
    # Incarcarea certificatelor dureaza, asa ca o facem o singura data
    context = ssl.create_default_context(cafile=certifi.where())
    context.load_verify_locations(cafile=str(INTERMEDIATE_CERT))
    return context


def _build_session() -> requests.Session:
    session = requests.Session()
    session.mount("https://", _ExtraCertificateAdapter(_ssl_context()))
    session.headers["User-Agent"] = (
        "benzi-app/1.0 (https://github.com/alexandrapaveluc/benzi-app)"
    )
    return session


def _text(element: ET.Element, path: str) -> str:
    found = element.find(path, XML_NAMESPACE)

    if found is None or found.text is None:
        return ""

    return found.text.strip()


def _parse_update_date(value: str) -> str | None:
    """Transforma "28/09/2026 12:17" (ora Romaniei) in format ISO."""
    try:
        local_time = datetime.strptime(value, "%d/%m/%Y %H:%M")
    except ValueError:
        return None

    return local_time.replace(tzinfo=ROMANIA_TIMEZONE).isoformat()


class MonitorulPreturilorClient:
    def __init__(
        self,
        base_url: str,
        timeout: int = 15,
        max_workers: int = 5,
    ):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.max_workers = max_workers
        self.session = _build_session()

    def get_stations(
        self,
        latitude: float,
        longitude: float,
        radius_km: float,
    ) -> list[dict[str, Any]]:
        """
        Benzinariile cu preturi intr-un cerc de maxim 5 km.

        Serverul intoarce un singur carburant pe cerere, asa ca facem
        cate o cerere pentru fiecare carburant si unim rezultatele.
        """
        buffer_meters = min(int(radius_km * 1000), MAX_BUFFER_METERS)

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            responses = list(
                executor.map(
                    lambda product_id: self._fetch(
                        latitude,
                        longitude,
                        buffer_meters,
                        product_id,
                    ),
                    FUEL_PRODUCTS,
                )
            )

        stations: dict[str, dict[str, Any]] = {}

        for product_id, root in zip(FUEL_PRODUCTS, responses):
            fuel_key = FUEL_PRODUCTS[product_id]

            for raw_station in root.iterfind("n:Stations/n:GasStation", XML_NAMESPACE):
                station_id = _text(raw_station, "n:Id")

                if station_id and station_id not in stations:
                    stations[station_id] = self._parse_station(raw_station)

            for raw_product in root.iterfind("n:Products/n:GasProduct", XML_NAMESPACE):
                station_id = _text(raw_product, "n:Stationid")
                price = _text(raw_product, "n:Price")

                if station_id in stations and price:
                    stations[station_id]["prices"][fuel_key] = float(price)

        return list(stations.values())

    def _fetch(
        self,
        latitude: float,
        longitude: float,
        buffer_meters: int,
        product_id: int,
    ) -> ET.Element:
        params = {
            "lat": latitude,
            "lon": longitude,
            "buffer": buffer_meters,
            "CSVGasCatalogProductIds": product_id,
            "OrderBy": "dist",
        }

        try:
            response = self.session.get(
                f"{self.base_url}/GetGasItemsByLatLon",
                params=params,
                timeout=self.timeout,
            )
            response.raise_for_status()
            return ET.fromstring(response.content)

        except requests.Timeout as error:
            raise PriceProviderError(
                "Monitorul Preturilor nu a raspuns la timp."
            ) from error

        except requests.RequestException as error:
            raise PriceProviderError(
                f"Monitorul Preturilor nu este disponibil: {error}"
            ) from error

        except ET.ParseError as error:
            raise PriceProviderError(
                "Monitorul Preturilor a returnat un raspuns invalid."
            ) from error

    @staticmethod
    def _parse_station(raw_station: ET.Element) -> dict[str, Any]:
        network_id = _text(raw_station, "n:Network/n:Id")
        brand = BRANDS.get(network_id, _text(raw_station, "n:Network/n:Name") or None)

        latitude = _text(raw_station, "n:Addr/n:Location/n:Lat")
        longitude = _text(raw_station, "n:Addr/n:Location/n:Lon")

        return {
            "id": _text(raw_station, "n:Id"),
            "name": _text(raw_station, "n:Name") or None,
            "brand": brand,
            "address": _text(raw_station, "n:Addr/n:Addrstring") or None,
            "latitude": float(latitude) if latitude else None,
            "longitude": float(longitude) if longitude else None,
            "updated_at": _parse_update_date(_text(raw_station, "n:Updatedate")),
            "prices": {},
        }

