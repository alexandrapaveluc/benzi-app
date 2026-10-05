# ⛽ Benzinării România

Aplicație care arată benzinăriile din România pe hartă, găsește cele mai apropiate benzinării de o adresă și afișează prețurile oficiale la carburanți.

## Ce poate face

- **Lista benzinăriilor din România** – aproape 3.000 de benzinării descărcate din OpenStreetMap, cu brandurile scrise uniform.
- **Hartă interactivă** – toate benzinăriile, grupate și colorate după brand, cu filtru pe branduri.
- **Prețuri la carburanți** – prețuri oficiale de la Monitorul Prețurilor (Consiliul Concurenței): benzină, motorină (standard și premium) și GPL.
- **Cea mai apropiată benzinărie** – scrii un oraș sau o adresă și primești cele mai apropiate benzinării, cu distanța și prețul.
- **Aplicație web** – toate cele de mai sus într-o singură pagină, plus statistici pe branduri.

## Instalare

Ai nevoie de Python 3.10 sau mai nou.

```bash
git clone https://github.com/alexandrapaveluc/benzi-app.git
cd benzi-app
python -m venv venv
```

Activează mediul virtual:

- Windows: `venv\Scripts\activate`
- macOS / Linux: `source venv/bin/activate`

Apoi instalează bibliotecile:

```bash
pip install -r requirements.txt
```

## Folosire

### Aplicația web (recomandat)

```bash
streamlit run app.py
```

Se deschide în browser la http://localhost:8501.

- **Caută benzinării** – scrii un oraș sau o adresă, alegi brandul și carburantul și vezi harta, tabelul cu prețuri și cea mai ieftină benzinărie din zonă.
- **Statistici** – numărul de benzinării și cele mai mari rețele din țară.

### Din linia de comandă

| Comandă | Ce face |
|---|---|
| `python main.py` | Descarcă din nou lista de benzinării în `benzinarii_romania.json` |
| `python harta.py` | Creează `harta.html` cu toate benzinăriile (și prețurile, dacă există `preturi.json`) |
| `python preturi.py Cluj-Napoca` | Prețurile din zonă și cea mai ieftină benzinărie pentru fiecare carburant; salvează `preturi.json` |
| `python cautare.py "Piata Unirii, Bucuresti"` | Cele mai apropiate 5 benzinării, cu distanță și preț; creează `aproape.html` |

Exemple de opțiuni:

```bash
python preturi.py 44.4268 26.1025 --raza 3000
python cautare.py Brasov -n 10 --brand Petrom --carburant "Motorina standard"
python cautare.py Iasi --fara-preturi
```

Locația se poate da ca nume de oraș, adresă sau coordonate (`lat lon`). Pentru opțiunile complete: `python cautare.py --help`.

## Structura proiectului

```
benzi-app/
├── app.py                    # aplicatia web (Streamlit)
├── main.py                   # descarca benzinariile din OpenStreetMap
├── harta.py                  # harta cu toate benzinariile
├── preturi.py                # preturile de la Monitorul Preturilor
├── cautare.py                # cele mai apropiate benzinarii
├── geocodare.py              # transforma o adresa in coordonate
├── benzinarii_romania.json   # lista de benzinarii (generata de main.py)
└── requirements.txt
```

## Surse de date

| Date | Sursă |
|---|---|
| Benzinăriile (poziție, nume, brand) | [OpenStreetMap](https://www.openstreetmap.org/copyright), prin Overpass API – © contributorii OpenStreetMap, licență ODbL |
| Căutarea adreselor | [Nominatim](https://nominatim.org/) (OpenStreetMap) |
| Prețurile la carburanți | [Monitorul Prețurilor](https://monitorulpreturilor.info/) – Consiliul Concurenței |

## Limitări

- **Prețurile se văd doar pe zone.** Serverul Monitorului Prețurilor răspunde doar pentru o rază de cel mult 5 km, așa că prețurile se iau pe zone, nu pentru toată țara deodată.
- **Prețuri doar pentru rețelele mari:** Petrom, OMV, Rompetrol, MOL, Lukoil, SOCAR și Gazprom. Benzinăriile independente apar pe hartă, dar fără preț.
- **Unele benzinării nu au brand.** În OpenStreetMap, o parte din benzinării nu au brandul completat; apar ca „Necunoscut”.
- **Folosire cu măsură.** Nominatim acceptă cel mult o cerere pe secundă, așa că aplicația păstrează temporar rezultatele (locațiile o zi, prețurile o oră).
