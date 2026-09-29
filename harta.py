import json
import os

import folium
from folium.plugins import FeatureGroupSubGroup, MarkerCluster

FISIER_DATE = "benzinarii_romania.json"
FISIER_PRETURI = "preturi.json"
FISIER_HARTA = "harta.html"

# Culori apropiate de cele ale fiecarui brand
CULORI = {
    "Rompetrol": "#e2001a",
    "Petrom": "#1f4e9c",
    "Lukoil": "#c8102e",
    "MOL": "#00843d",
    "OMV": "#003a70",
    "SOCAR": "#00a3e0",
    "Oscar": "#f28c00",
    "Gazprom": "#0079c1",
}
CULOARE_ALTELE = "#7f7f7f"


def citeste_date():
    with open(FISIER_DATE, encoding="utf-8") as f:
        return json.load(f)


def text_popup(b):
    link = f"https://www.google.com/maps/search/?api=1&query={b['lat']},{b['lon']}"
    return (
        f"<b>{b['nume']}</b><br>"
        f"Brand: {b['brand']}<br>"
        f"<a href='{link}' target='_blank'>Deschide in Google Maps</a>"
    )


def citeste_preturi():
    """Preturile sunt optionale: exista doar daca a fost rulat preturi.py."""
    if not os.path.exists(FISIER_PRETURI):
        return []
    with open(FISIER_PRETURI, encoding="utf-8") as f:
        return json.load(f)


def adauga_preturi(harta, statii):
    strat = folium.FeatureGroup(name=f"Preturi ({len(statii)})")

    cu_benzina = [s["preturi"]["Benzina standard"] for s in statii if "Benzina standard" in s["preturi"]]
    cel_mai_mic = min(cu_benzina) if cu_benzina else None

    for s in statii:
        pret = s["preturi"].get("Benzina standard")
        eticheta = f"{pret:.2f}" if pret else "-"
        culoare = "#00843d" if pret is not None and pret == cel_mai_mic else "#333333"

        randuri = "".join(
            f"{carburant}: <b>{valoare:.2f} lei</b><br>"
            for carburant, valoare in s["preturi"].items()
        )
        popup = (
            f"<b>{s['nume']}</b> ({s['retea']})<br>"
            f"{s['adresa']}<br><br>"
            f"{randuri}<br>"
            f"<small>Actualizat: {s['actualizat']}</small>"
        )

        folium.Marker(
            location=[s["lat"], s["lon"]],
            icon=folium.DivIcon(
                icon_size=(46, 20),
                icon_anchor=(23, 10),
                html=(
                    f"<div style='background:{culoare};color:white;font-size:11px;"
                    f"font-weight:bold;text-align:center;border-radius:4px;"
                    f"padding:2px 0;box-shadow:0 1px 3px rgba(0,0,0,.4)'>{eticheta}</div>"
                ),
            ),
            popup=folium.Popup(popup, max_width=280),
            tooltip=f"{s['nume']} - benzina {eticheta} lei",
        ).add_to(strat)

    strat.add_to(harta)


def creeaza_harta(benzinarii, preturi):
    harta = folium.Map(location=[45.9, 24.9], zoom_start=7, tiles="OpenStreetMap")

    # Un singur cluster comun, cu cate un strat pentru fiecare brand,
    # ca sa poti ascunde/afisa brandurile din coltul din dreapta sus
    cluster = MarkerCluster(name="Toate benzinariile", control=False)
    cluster.add_to(harta)

    straturi = {}
    for brand in list(CULORI) + ["Altele"]:
        strat = FeatureGroupSubGroup(cluster, name=brand)
        strat.add_to(harta)
        straturi[brand] = strat

    numar = {brand: 0 for brand in straturi}

    for b in benzinarii:
        brand = b["brand"] if b["brand"] in CULORI else "Altele"
        culoare = CULORI.get(brand, CULOARE_ALTELE)

        folium.CircleMarker(
            location=[b["lat"], b["lon"]],
            radius=6,
            color=culoare,
            fill=True,
            fill_color=culoare,
            fill_opacity=0.85,
            weight=1,
            popup=folium.Popup(text_popup(b), max_width=250),
            tooltip=b["nume"],
        ).add_to(straturi[brand])
        numar[brand] += 1

    # Punem numarul de benzinarii in numele fiecarui strat
    for brand, strat in straturi.items():
        strat.layer_name = f"{brand} ({numar[brand]})"

    if preturi:
        adauga_preturi(harta, preturi)

    folium.LayerControl(collapsed=False).add_to(harta)
    return harta


def main():
    benzinarii = citeste_date()
    preturi = citeste_preturi()
    harta = creeaza_harta(benzinarii, preturi)
    harta.save(FISIER_HARTA)
    print(f"Harta cu {len(benzinarii)} benzinarii a fost salvata in {FISIER_HARTA}")
    if preturi:
        print(f"Am adaugat preturile pentru {len(preturi)} benzinarii.")
    else:
        print("Nu exista preturi.json - ruleaza intai preturi.py daca vrei si preturile.")


if __name__ == "__main__":
    main()
