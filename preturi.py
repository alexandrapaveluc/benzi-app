import argparse
import json
import time
import xml.etree.ElementTree as ET

import requests
import truststore

from geocodare import citeste_locatie

# Serverul nu trimite certificatul intermediar corect, asa ca folosim
# certificatele sistemului de operare (care il pot completa singure)
truststore.inject_into_ssl()

# Sursa oficiala: Monitorul Preturilor (Consiliul Concurentei)
URL = "https://monitorulpreturilor.info/pmonsvc/Gas/GetGasItemsByLatLon"
NS = {"n": "http://schemas.datacontract.org/2004/07/pmonsvc.Models.Protos"}

FISIER_IESIRE = "preturi.json"

# Serverul nu raspunde la raze mai mari de ~5 km
RAZA_MAXIMA = 5000

# Id-urile carburantilor din catalogul Monitorului Preturilor
CARBURANTI = {
    11: "Benzina standard",
    12: "Benzina premium",
    21: "Motorina standard",
    22: "Motorina premium",
    31: "GPL",
}

headers = {
    "User-Agent": "benzi-app/1.0 (https://github.com/alexandrapaveluc/benzi-app)"
}

# Locul folosit daca nu se da nimic
LOCATIE_IMPLICITA = ["Bucuresti"]


def text(element, cale):
    gasit = element.find(cale, NS)
    if gasit is None or gasit.text is None:
        return ""
    return gasit.text.strip()


def cere_carburant(lat, lon, raza, id_carburant):
    """Intoarce statiile si preturile pentru un singur carburant."""
    params = {
        "lat": lat,
        "lon": lon,
        "buffer": raza,
        "CSVGasCatalogProductIds": id_carburant,
        "OrderBy": "price",
    }
    response = requests.get(URL, params=params, headers=headers, timeout=60)
    response.raise_for_status()
    return ET.fromstring(response.content)


def descarca_preturi(lat, lon, raza):
    statii = {}

    for id_carburant, nume_carburant in CARBURANTI.items():
        print(f"Descarc preturile pentru {nume_carburant} ...")
        radacina = cere_carburant(lat, lon, raza, id_carburant)

        for s in radacina.iterfind("n:Stations/n:GasStation", NS):
            id_statie = text(s, "n:Id")
            if id_statie not in statii:
                statii[id_statie] = {
                    "id": id_statie,
                    "nume": text(s, "n:Name"),
                    "retea": text(s, "n:Network/n:Name"),
                    "adresa": text(s, "n:Addr/n:Addrstring"),
                    "lat": float(text(s, "n:Addr/n:Location/n:Lat")),
                    "lon": float(text(s, "n:Addr/n:Location/n:Lon")),
                    "actualizat": text(s, "n:Updatedate"),
                    "preturi": {},
                }

        for p in radacina.iterfind("n:Products/n:GasProduct", NS):
            id_statie = text(p, "n:Stationid")
            pret = text(p, "n:Price")
            if id_statie in statii and pret:
                statii[id_statie]["preturi"][nume_carburant] = float(pret)

        # Pauza mica intre cereri, ca sa nu incarcam serverul
        time.sleep(1)

    return list(statii.values())


def afiseaza_cele_mai_ieftine(statii):
    for nume_carburant in CARBURANTI.values():
        cu_pret = [s for s in statii if nume_carburant in s["preturi"]]
        if not cu_pret:
            continue
        s = min(cu_pret, key=lambda x: x["preturi"][nume_carburant])
        print(f"{nume_carburant}: {s['preturi'][nume_carburant]:.2f} lei - {s['nume']} ({s['adresa']})")


def main():
    parser = argparse.ArgumentParser(description="Preturile la carburanti intr-o zona.")
    parser.add_argument("locatie", nargs="*",
                        help='oras/adresa ("Cluj-Napoca") sau coordonate (44.43 26.10)')
    parser.add_argument("--raza", type=int, default=RAZA_MAXIMA,
                        help=f"raza in metri (maxim {RAZA_MAXIMA})")
    args = parser.parse_args()

    raza = args.raza
    if raza > RAZA_MAXIMA:
        print(f"Raza maxima acceptata de server este {RAZA_MAXIMA} m, folosesc {RAZA_MAXIMA}.")
        raza = RAZA_MAXIMA

    locatie = citeste_locatie(args.locatie or LOCATIE_IMPLICITA)
    if locatie is None:
        print("Nu am gasit locatia. Incearca alt nume sau da coordonatele.")
        return
    lat, lon, descriere = locatie
    print(f"Caut in jurul: {descriere} (raza {raza} m)\n")

    try:
        statii = descarca_preturi(lat, lon, raza)
    except Exception as e:
        print(f"Nu am putut descarca preturile. Eroare: {e}")
        return

    print(f"\nAm gasit {len(statii)} benzinarii cu preturi.\n")
    print("Cele mai ieftine:")
    afiseaza_cele_mai_ieftine(statii)

    with open(FISIER_IESIRE, "w", encoding="utf-8") as f:
        json.dump(statii, f, ensure_ascii=False, indent=2)

    print(f"\nSalvat in fisierul {FISIER_IESIRE}")


if __name__ == "__main__":
    main()
