import requests
import json
import time

FISIER_IESIRE = "benzinarii_romania.json"

# Cautam doar in interiorul granitei Romaniei (nu intr-un dreptunghi),
# si luam atat punctele (node) cat si cladirile/poligoanele (way, relation).
query = """
[out:json][timeout:180];
area["ISO3166-1"="RO"][admin_level=2]->.ro;
nwr["amenity"="fuel"](area.ro);
out center tags;
"""

headers = {
    "User-Agent": "benzi-app/1.0 (https://github.com/alexandrapaveluc/benzi-app)"
}

servere = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
    "https://overpass.openstreetmap.fr/api/interpreter",
]

# Cuvinte cheie din nume/operator -> numele corect al brandului
BRANDURI = {
    "rompetrol": "Rompetrol",
    "petromidia": "Rompetrol",
    "petrom": "Petrom",
    "omv": "OMV",
    "lukoil": "Lukoil",
    "socar": "SOCAR",
    "gazprom": "Gazprom",
    "shell": "Shell",
    "avia": "Avia",
    "mol": "MOL",
}


def gaseste_brand(text):
    """Returneaza brandul cunoscut care apare in text, sau None."""
    cuvinte = text.lower().replace("-", " ").split()
    for cheie, brand in BRANDURI.items():
        # cuvintele scurte le cautam separat, ca sa nu prindem "Bemol" sau "Aviatiei"
        if cheie in ("mol", "avia"):
            if cheie in cuvinte:
                return brand
        elif cheie in text.lower():
            return brand
    return None


def normalizeaza_brand(tags):
    """Alege brandul din tagurile OSM si il scrie mereu la fel."""
    brand = tags.get("brand", "")
    nume = tags.get("name", "")
    operator = tags.get("operator", "")

    for text in (brand, nume, operator):
        gasit = gaseste_brand(text)
        if gasit:
            return gasit

    if brand:
        return brand
    return "Necunoscut"


def descarca_date():
    for i, server in enumerate(servere):
        print(f"Incerc serverul: {server} ...")
        try:
            response = requests.post(server, data={"data": query}, headers=headers, timeout=200)
            response.raise_for_status()
            print(f"A functionat cu: {server}")
            return response.json()
        except Exception as e:
            print(f"Nu a mers cu {server}. Eroare: {e}")
            if i < len(servere) - 1:
                print("Astept 15 secunde inainte sa incerc urmatorul server...")
                time.sleep(15)
    return None


def curata_date(elemente):
    lista_curata = []
    for b in elemente:
        tags = b.get("tags", {})

        # node-urile au lat/lon direct, way/relation au "center"
        if "lat" in b:
            lat, lon = b["lat"], b["lon"]
        elif "center" in b:
            lat, lon = b["center"]["lat"], b["center"]["lon"]
        else:
            continue

        brand = normalizeaza_brand(tags)
        nume = tags.get("name") or (brand if brand != "Necunoscut" else "Fara nume")

        lista_curata.append({
            "id": b["id"],
            "tip": b["type"],
            "nume": nume,
            "brand": brand,
            "lat": lat,
            "lon": lon
        })
    return lista_curata


def main():
    data = descarca_date()
    if data is None:
        print("Niciun server Overpass nu a raspuns corect. Incearca din nou peste cateva minute.")
        return

    benzinarii = curata_date(data["elements"])
    print(f"Am gasit {len(benzinarii)} benzinarii in Romania.")

    with open(FISIER_IESIRE, "w", encoding="utf-8") as f:
        json.dump(benzinarii, f, ensure_ascii=False, indent=2)

    print(f"Salvat in fisierul {FISIER_IESIRE}")


if __name__ == "__main__":
    main()
