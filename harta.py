import json

import folium
from folium.plugins import FeatureGroupSubGroup, MarkerCluster

FISIER_DATE = "benzinarii_romania.json"
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


def creeaza_harta(benzinarii):
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

    folium.LayerControl(collapsed=False).add_to(harta)
    return harta


def main():
    benzinarii = citeste_date()
    harta = creeaza_harta(benzinarii)
    harta.save(FISIER_HARTA)
    print(f"Harta cu {len(benzinarii)} benzinarii a fost salvata in {FISIER_HARTA}")


if __name__ == "__main__":
    main()
