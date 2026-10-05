import requests

# Nominatim = serviciul gratuit de cautare adrese al OpenStreetMap.
# Regula lor: maxim o cerere pe secunda si un User-Agent care ne identifica.
URL = "https://nominatim.openstreetmap.org/search"

headers = {
    "User-Agent": "benzi-app/1.0 (https://github.com/alexandrapaveluc/benzi-app)"
}


def gaseste_coordonate(text):
    """Transforma un oras/adresa in (lat, lon, nume complet). None daca nu gaseste."""
    params = {
        "q": text,
        "format": "jsonv2",
        "countrycodes": "ro",
        "limit": 1,
    }
    response = requests.get(URL, params=params, headers=headers, timeout=30)
    response.raise_for_status()
    rezultate = response.json()

    if not rezultate:
        return None

    r = rezultate[0]
    return float(r["lat"]), float(r["lon"]), r["display_name"]


def citeste_locatie(argumente):
    """
    Accepta fie coordonate ("44.43 26.10"), fie un text ("Piata Unirii, Bucuresti").
    Intoarce (lat, lon, descriere) sau None.
    """
    if len(argumente) >= 2:
        try:
            lat, lon = float(argumente[0]), float(argumente[1])
            return lat, lon, f"{lat}, {lon}"
        except ValueError:
            pass

    text = " ".join(argumente)
    return gaseste_coordonate(text)
