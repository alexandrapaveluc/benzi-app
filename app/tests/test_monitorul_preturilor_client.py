import pytest
import requests

from app.clients.monitorul_preturilor_client import (
    MonitorulPreturilorClient,
    PriceProviderError,
)


def make_xml(product_id: int, price: float, include_second_station: bool = True) -> bytes:
    second_station = """
        <GasStation>
            <Addr>
                <Addrstring>Calea Bucuresti 10</Addrstring>
                <Location><Lat>44.86</Lat><Lon>24.88</Lon></Location>
            </Addr>
            <Id>S2</Id>
            <Name>Pitesti 2</Name>
            <Network><Id>ROMPETROL</Id><Name>Rompetrol</Name></Network>
            <Updatedate>06/10/2026 09:00</Updatedate>
        </GasStation>
    """ if include_second_station else ""

    return f"""
    <GasItems xmlns="http://schemas.datacontract.org/2004/07/pmonsvc.Models.Protos">
        <Products>
            <GasProduct>
                <Price>{price}</Price>
                <Stationid>S1</Stationid>
            </GasProduct>
        </Products>
        <Stations>
            <GasStation>
                <Addr>
                    <Addrstring>Str. Abatorului 6</Addrstring>
                    <Location><Lat>44.8524</Lat><Lon>24.88562</Lon></Location>
                </Addr>
                <Id>S1</Id>
                <Name>Pitesti 1</Name>
                <Network><Id>PETROM</Id><Name>PETROM</Name></Network>
                <Updatedate>07/10/2026 11:05</Updatedate>
            </GasStation>
            {second_station}
        </Stations>
    </GasItems>
    """.encode("utf-8")


class FakeResponse:
    def __init__(self, content: bytes, status_code: int = 200):
        self.content = content
        self.status_code = status_code

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(f"HTTP {self.status_code}")


PRICES = {11: 10.05, 12: 10.65, 21: 10.91, 22: 11.76, 31: 4.71}


@pytest.fixture
def client():
    return MonitorulPreturilorClient(base_url="https://example.test/Gas")


def test_get_stations_merges_all_fuels(client, monkeypatch):
    requested = []

    def fake_get(url, params, timeout):
        requested.append(params)
        product_id = params["CSVGasCatalogProductIds"]
        return FakeResponse(make_xml(product_id, PRICES[product_id]))

    monkeypatch.setattr(client.session, "get", fake_get)

    stations = client.get_stations(44.8565, 24.8692, radius_km=10)

    # o cerere pentru fiecare carburant, cu raza limitata la 5 km
    assert sorted(p["CSVGasCatalogProductIds"] for p in requested) == [11, 12, 21, 22, 31]
    assert all(p["buffer"] == 5000 for p in requested)

    by_id = {station["id"]: station for station in stations}
    assert set(by_id) == {"S1", "S2"}

    first = by_id["S1"]
    assert first["brand"] == "Petrom"
    assert first["name"] == "Pitesti 1"
    assert first["address"] == "Str. Abatorului 6"
    assert first["latitude"] == 44.8524
    assert first["updated_at"] == "2026-10-07T11:05:00+03:00"
    assert first["prices"] == {
        "gasoline_standard": 10.05,
        "gasoline_premium": 10.65,
        "diesel_standard": 10.91,
        "diesel_premium": 11.76,
        "lpg": 4.71,
    }

    # benzinaria fara preturi apare, dar fara preturi
    assert by_id["S2"]["prices"] == {}
    assert by_id["S2"]["brand"] == "Rompetrol"


def test_small_radius_is_sent_in_meters(client, monkeypatch):
    requested = []

    def fake_get(url, params, timeout):
        requested.append(params["buffer"])
        return FakeResponse(make_xml(params["CSVGasCatalogProductIds"], 10.0))

    monkeypatch.setattr(client.session, "get", fake_get)

    client.get_stations(44.8565, 24.8692, radius_km=2.5)

    assert set(requested) == {2500}


def test_connection_error_becomes_provider_error(client, monkeypatch):
    def fake_get(url, params, timeout):
        raise requests.ConnectionError("no network")

    monkeypatch.setattr(client.session, "get", fake_get)

    with pytest.raises(PriceProviderError):
        client.get_stations(44.8565, 24.8692, radius_km=5)


def test_timeout_becomes_provider_error(client, monkeypatch):
    def fake_get(url, params, timeout):
        raise requests.Timeout()

    monkeypatch.setattr(client.session, "get", fake_get)

    with pytest.raises(PriceProviderError, match="la timp"):
        client.get_stations(44.8565, 24.8692, radius_km=5)


def test_server_error_becomes_provider_error(client, monkeypatch):
    monkeypatch.setattr(
        client.session,
        "get",
        lambda url, params, timeout: FakeResponse(b"", status_code=503),
    )

    with pytest.raises(PriceProviderError):
        client.get_stations(44.8565, 24.8692, radius_km=5)


def test_invalid_xml_becomes_provider_error(client, monkeypatch):
    monkeypatch.setattr(
        client.session,
        "get",
        lambda url, params, timeout: FakeResponse(b"<html>eroare"),
    )

    with pytest.raises(PriceProviderError, match="invalid"):
        client.get_stations(44.8565, 24.8692, radius_km=5)
