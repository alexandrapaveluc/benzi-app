import argparse
import json
import math

import folium

from geocodare import citeste_locatie
from preturi import RAZA_MAXIMA, descarca_preturi

FISIER_DATE = "benzinarii_romania.json"
FISIER_HARTA = "aproape.html"

# Doua puncte la mai putin de atatia metri le consideram aceeasi benzinarie
DISTANTA_POTRIVIRE = 150


def distanta_km(lat1, lon1, lat2, lon2):
    """Distanta in linie dreapta intre doua puncte (formula haversine)."""
    raza_pamant = 6371
    f1, f2 = math.radians(lat1), math.radians(lat2)
    df = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(df / 2) ** 2 + math.cos(f1) * math.cos(f2) * math.sin(dl / 2) ** 2
    return 2 * raza_pamant * math.asin(math.sqrt(a))


def cele_mai_apropiate(benzinarii, lat, lon, cate, brand=None):
    if brand:
        benzinarii = [b for b in benzinarii if b["brand"].lower() == brand.lower()]

    # Facem copii, ca sa nu modificam lista originala
    cu_distanta = [dict(b, distanta=distanta_km(lat, lon, b["lat"], b["lon"])) for b in benzinarii]

    return sorted(cu_distanta, key=lambda b: b["distanta"])[:cate]


def adauga_preturi(apropiate, lat, lon):
    """Cauta preturile in zona si le lipeste de benzinariile gasite."""
    try:
        statii_cu_preturi = descarca_preturi(lat, lon, RAZA_MAXIMA)
    except Exception as e:
        print(f"Nu am putut descarca preturile. Eroare: {e}")
        return

    potriveste_preturi(apropiate, statii_cu_preturi)


def potriveste_preturi(apropiate, statii_cu_preturi):
    """Leaga preturile de benzinariile noastre dupa pozitie."""
    for b in apropiate:
        b["preturi"] = {}
        for s in statii_cu_preturi:
            if distanta_km(b["lat"], b["lon"], s["lat"], s["lon"]) * 1000 <= DISTANTA_POTRIVIRE:
                b["preturi"] = s["preturi"]
                break


def afiseaza(apropiate, carburant):
    print()
    for i, b in enumerate(apropiate, start=1):
        linie = f"{i}. {b['nume']} ({b['brand']}) - {b['distanta']:.2f} km"
        pret = b.get("preturi", {}).get(carburant)
        if pret:
            linie += f" - {carburant.lower()}: {pret:.2f} lei"
        print(linie)


def construieste_harta(apropiate, lat, lon, descriere, carburant):
    harta = folium.Map(location=[lat, lon], zoom_start=14)

    folium.Marker(
        [lat, lon],
        tooltip="Tu esti aici",
        popup=descriere,
        icon=folium.Icon(color="red", icon="user", prefix="fa"),
    ).add_to(harta)

    for i, b in enumerate(apropiate, start=1):
        randuri = "".join(
            f"{c}: <b>{v:.2f} lei</b><br>" for c, v in b.get("preturi", {}).items()
        )
        link = f"https://www.google.com/maps/dir/?api=1&destination={b['lat']},{b['lon']}"
        popup = (
            f"<b>{i}. {b['nume']}</b> ({b['brand']})<br>"
            f"{b['distanta']:.2f} km<br><br>"
            f"{randuri}"
            f"<a href='{link}' target='_blank'>Traseu in Google Maps</a>"
        )
        pret = b.get("preturi", {}).get(carburant)
        tooltip = f"{i}. {b['nume']}" + (f" - {pret:.2f} lei" if pret else "")

        folium.Marker(
            [b["lat"], b["lon"]],
            tooltip=tooltip,
            popup=folium.Popup(popup, max_width=280),
            icon=folium.Icon(color="blue", icon="gas-pump", prefix="fa"),
        ).add_to(harta)

    # Incadram harta astfel incat sa se vada toate punctele
    puncte = [[lat, lon]] + [[b["lat"], b["lon"]] for b in apropiate]
    harta.fit_bounds(puncte, padding=(30, 30))
    return harta


def creeaza_harta(apropiate, lat, lon, descriere, carburant):
    harta = construieste_harta(apropiate, lat, lon, descriere, carburant)
    harta.save(FISIER_HARTA)


def main():
    parser = argparse.ArgumentParser(description="Cele mai apropiate benzinarii de o locatie.")
    parser.add_argument("locatie", nargs="+",
                        help='oras/adresa ("Piata Unirii, Bucuresti") sau coordonate (44.43 26.10)')
    parser.add_argument("-n", type=int, default=5, help="cate benzinarii sa afiseze (implicit 5)")
    parser.add_argument("--brand", help="doar un anumit brand, ex. Petrom")
    parser.add_argument("--carburant", default="Benzina standard",
                        help='carburantul afisat in lista (implicit "Benzina standard")')
    parser.add_argument("--fara-preturi", action="store_true", help="nu descarca preturile")
    args = parser.parse_args()

    locatie = citeste_locatie(args.locatie)
    if locatie is None:
        print("Nu am gasit locatia. Incearca alt nume sau da coordonatele.")
        return
    lat, lon, descriere = locatie
    print(f"Locatia ta: {descriere}\n")

    with open(FISIER_DATE, encoding="utf-8") as f:
        benzinarii = json.load(f)

    apropiate = cele_mai_apropiate(benzinarii, lat, lon, args.n, args.brand)
    if not apropiate:
        print("Nu am gasit nicio benzinarie.")
        return

    if not args.fara_preturi:
        adauga_preturi(apropiate, lat, lon)

    afiseaza(apropiate, args.carburant)

    creeaza_harta(apropiate, lat, lon, descriere, args.carburant)
    print(f"\nHarta salvata in {FISIER_HARTA}")


if __name__ == "__main__":
    main()
