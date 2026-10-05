import json
import os
from collections import Counter

import pandas as pd
import streamlit as st
from streamlit_folium import st_folium

from cautare import cele_mai_apropiate, construieste_harta, potriveste_preturi
from geocodare import citeste_locatie
from preturi import CARBURANTI, RAZA_MAXIMA, descarca_preturi

# Calea fata de app.py, ca aplicatia sa mearga din orice folder e pornita
FISIER_DATE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "benzinarii_romania.json")

st.set_page_config(page_title="Benzinarii Romania", page_icon="⛽", layout="wide")


# --- Date (pastrate in cache, ca sa nu le cerem de fiecare data) ---

@st.cache_data
def citeste_benzinarii():
    with open(FISIER_DATE, encoding="utf-8") as f:
        return json.load(f)


@st.cache_data(ttl=24 * 3600, show_spinner=False)
def cauta_locatie(text):
    return citeste_locatie(text.split()) if text.strip() else None


# Preturile se schimba des, le pastram doar o ora
@st.cache_data(ttl=3600, show_spinner=False)
def preturi_in_zona(lat, lon):
    return descarca_preturi(lat, lon, RAZA_MAXIMA)


benzinarii = citeste_benzinarii()
numar_branduri = Counter(b["brand"] for b in benzinarii)
branduri = [b for b, n in numar_branduri.most_common() if n >= 5 and b != "Necunoscut"]

st.title("⛽ Benzinarii Romania")

tab_cautare, tab_statistici = st.tabs(["Cauta benzinarii", "Statistici"])


# --- Tab 1: cautare ---

with tab_cautare:
    with st.form("cautare"):
        col1, col2, col3, col4 = st.columns([3, 1.2, 1.5, 1.5])
        text_locatie = col1.text_input("Oras sau adresa", "Piata Unirii, Bucuresti")
        cate = col2.number_input("Cate benzinarii", min_value=1, max_value=20, value=5)
        brand = col3.selectbox("Brand", ["Toate"] + branduri)
        carburant = col4.selectbox("Carburant", list(CARBURANTI.values()))
        cu_preturi = st.checkbox("Arata si preturile (Monitorul Preturilor)", value=True)
        cauta = st.form_submit_button("Cauta", type="primary")

    if cauta:
        st.session_state["ultima_cautare"] = (text_locatie, cate, brand, carburant, cu_preturi)

    if "ultima_cautare" in st.session_state:
        text_locatie, cate, brand, carburant, cu_preturi = st.session_state["ultima_cautare"]

        with st.spinner("Caut locatia..."):
            locatie = cauta_locatie(text_locatie)

        if locatie is None:
            st.error("Nu am gasit locatia. Incearca alt nume sau scrie coordonatele (ex: 44.43 26.10).")
            st.stop()

        lat, lon, descriere = locatie
        st.caption(f"📍 {descriere}")

        apropiate = cele_mai_apropiate(
            benzinarii, lat, lon, cate, None if brand == "Toate" else brand
        )
        if not apropiate:
            st.warning("Nu am gasit nicio benzinarie.")
            st.stop()

        if cu_preturi:
            try:
                with st.spinner("Descarc preturile din zona..."):
                    potriveste_preturi(apropiate, preturi_in_zona(lat, lon))
            except Exception as e:
                st.warning(f"Nu am putut descarca preturile: {e}")

        # Cifre principale
        cu_pret = [b for b in apropiate if carburant in b.get("preturi", {})]
        m1, m2, m3 = st.columns(3)
        m1.metric("Cea mai apropiata", f"{apropiate[0]['distanta']:.2f} km", apropiate[0]["nume"],
                  delta_color="off", delta_arrow="off")
        if cu_pret:
            ieftina = min(cu_pret, key=lambda b: b["preturi"][carburant])
            scumpa = max(cu_pret, key=lambda b: b["preturi"][carburant])
            m2.metric(f"Cel mai mic pret - {carburant.lower()}",
                      f"{ieftina['preturi'][carburant]:.2f} lei", ieftina["nume"], delta_color="off", delta_arrow="off")
            m3.metric("Diferenta fata de cel mai scump",
                      f"{scumpa['preturi'][carburant] - ieftina['preturi'][carburant]:.2f} lei/l")
        else:
            m2.metric(f"Pret {carburant.lower()}", "-")

        col_harta, col_tabel = st.columns([3, 2])

        with col_harta:
            harta = construieste_harta(apropiate, lat, lon, descriere, carburant)
            st_folium(harta, height=500, use_container_width=True, returned_objects=[])

        with col_tabel:
            tabel = pd.DataFrame([
                {
                    "Benzinarie": b["nume"],
                    "Brand": b["brand"],
                    "Distanta (km)": round(b["distanta"], 2),
                    "Pret (lei)": b.get("preturi", {}).get(carburant),
                }
                for b in apropiate
            ])
            tabel.index = range(1, len(tabel) + 1)
            st.dataframe(tabel, width="stretch")
            if cu_preturi:
                st.caption(
                    "Preturile sunt disponibile doar pentru retelele mari "
                    "(Petrom, OMV, Rompetrol, MOL, Lukoil, SOCAR, Gazprom)."
                )
    else:
        st.info("Scrie un oras sau o adresa si apasa **Cauta**.")


# --- Tab 2: statistici ---

with tab_statistici:
    s1, s2, s3 = st.columns(3)
    s1.metric("Benzinarii in Romania", len(benzinarii))
    s2.metric("Branduri diferite", len(numar_branduri))
    s3.metric("Fara brand cunoscut", numar_branduri["Necunoscut"])

    st.subheader("Cele mai mari retele")
    top = pd.DataFrame(
        [(b, n) for b, n in numar_branduri.most_common() if b != "Necunoscut"][:10],
        columns=["Brand", "Benzinarii"],
    ).set_index("Brand")
    st.bar_chart(top, horizontal=True, sort="-Benzinarii")

    st.caption("Date: OpenStreetMap (benzinarii), Monitorul Preturilor - Consiliul Concurentei (preturi).")
