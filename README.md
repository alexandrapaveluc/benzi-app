# BENZI-APP

## Fuel Finder

BENZI-APP este o aplicație backend pentru identificarea benzinăriilor din apropierea utilizatorului și compararea prețurilor combustibililor.

Aplicația primește coordonatele geografice ale utilizatorului, caută benzinăriile din apropiere, preia prețurile oficiale ale combustibililor de la **Monitorul Prețurilor** (Consiliul Concurenței), calculează distanța până la fiecare stație și returnează rezultatele sortate după distanță.

---

## Funcționalități

Aplicația poate:

* primi latitudinea și longitudinea utilizatorului;
* căuta benzinării într-o rază de până la 10 km;
* prelua prețurile combustibililor: benzină și motorină (standard și premium) și GPL;
* calcula distanța dintre utilizator și fiecare benzinărie;
* sorta benzinăriile de la cea mai apropiată la cea mai îndepărtată;
* returna maximum 20 de benzinării;
* păstra rezultatele în cache, ca să răspundă rapid și să nu încarce sursa de date;
* afișa datele printr-un API REST, apelabil și din browser (CORS);
* permite testarea API-ului prin Swagger UI.

---

## Tehnologii

Proiectul folosește:

* Python
* FastAPI
* Pydantic
* Requests
* Pytest
* Uvicorn
* Monitorul Prețurilor (Consiliul Concurenței)
* Render pentru deploy

---

## Structura proiectului

```text
benzi-app/
│
├── app/
│   ├── certs/
│   │   └── sectigo-dv-r36.pem
│   │
│   ├── clients/
│   │   └── monitorul_preturilor_client.py
│   │
│   ├── models/
│   │   ├── fuel_prices.py
│   │   ├── location.py
│   │   ├── station.py
│   │   └── station_response.py
│   │
│   ├── routers/
│   │   └── station_router.py
│   │
│   ├── services/
│   │   ├── cache_service.py
│   │   ├── distance_service.py
│   │   └── station_service.py
│   │
│   ├── tests/
│   │   ├── test_cache_service.py
│   │   ├── test_distance_service.py
│   │   ├── test_monitorul_preturilor_client.py
│   │   ├── test_station_router.py
│   │   └── test_station_service.py
│   │
│   ├── config.py
│   └── main.py
│
├── docs/
│   ├── benzi-app-request.txt
│   └── benzi-app-response.json
│
├── .env.example
├── .gitignore
├── README.md
└── requirements.txt
```

---

# API

## GET `/stations/nearby`

Endpoint-ul principal al aplicației.

Primește:

* `latitude` — latitudinea utilizatorului (obligatoriu);
* `longitude` — longitudinea utilizatorului (obligatoriu);
* `radius_km` — raza de căutare în kilometri (opțional, implicit 10, maxim 10).

### Exemplu

```text
GET /stations/nearby?latitude=44.8565&longitude=24.8692&radius_km=10
```

### Exemplu cURL

```bash
curl -X 'GET' \
  'https://benzi-app.onrender.com/stations/nearby?latitude=44.8565&longitude=24.8692&radius_km=10' \
  -H 'accept: application/json'
```

### Coduri de răspuns

| Cod | Când apare |
| --- | ---------- |
| `200` | Căutarea a reușit (lista poate fi goală dacă nu există benzinării în rază) |
| `422` | Parametri greșiți (ex. `latitude` peste 90 sau `radius_km` peste 10) |
| `502` | Monitorul Prețurilor nu răspunde sau a trimis un răspuns invalid |

---

# Swagger UI

API-ul poate fi testat direct din browser folosind Swagger UI.

## Versiunea publică

```text
https://benzi-app.onrender.com/docs
```

În Swagger:

1. se deschide `GET /stations/nearby`;
2. se apasă `Try it out`;
3. se introduc coordonatele;
4. se introduce raza de căutare;
5. se apasă `Execute`.

Exemplu:

```text
latitude: 44.8565
longitude: 24.8692
radius_km: 10
```

> Serverul gratuit de pe Render „doarme” când nu e folosit. Prima cerere după o pauză poate dura aproximativ 30 de secunde.

---

# Răspunsul API

API-ul returnează informații despre locația utilizatorului, data celei mai recente actualizări a prețurilor și lista benzinăriilor.

Exemplu simplificat (răspunsul complet este în `docs/benzi-app-response.json`):

```json
{
  "location": {
    "latitude": 44.8565,
    "longitude": 24.8692
  },
  "radius_km": 10,
  "price_data_updated_at": "2026-10-09T11:15:00+03:00",
  "stations": [
    {
      "station_id": "P050",
      "name": "Lukoil - Pitesti 2",
      "brand": "Lukoil",
      "address": "str. Depozitelor",
      "city": null,
      "county": null,
      "latitude": 44.865709,
      "longitude": 24.878858,
      "distance_km": 1.28,
      "price_updated_at": "2026-10-08T14:05:00+03:00",
      "prices": {
        "gasoline": {
          "standard": 10.15,
          "premium": 10.74
        },
        "diesel": {
          "standard": 10.92,
          "premium": 11.81
        },
        "lpg": null
      }
    }
  ]
}
```

* `price_updated_at` — când a actualizat benzinăria prețurile (ora României);
* `price_data_updated_at` — cea mai recentă dintre aceste date;
* `city` și `county` sunt păstrate pentru compatibilitate, dar momentan sunt `null`, pentru că Monitorul Prețurilor nu trimite localitatea separat (ea apare în `address`).

---

# Tipuri de combustibil

Aplicația lucrează cu următoarele tipuri de combustibil:

| Câmp în răspuns     | Descriere         | Id Monitorul Prețurilor |
| ------------------- | ----------------- | ----------------------- |
| `gasoline.standard` | Benzină standard  | 11 |
| `gasoline.premium`  | Benzină premium   | 12 |
| `diesel.standard`   | Motorină standard | 21 |
| `diesel.premium`    | Motorină premium  | 22 |
| `lpg`               | GPL               | 31 |

Dacă un anumit tip de combustibil nu are preț disponibil, valoarea este `null`.

---

# Calcularea distanței

Distanța dintre utilizator și benzinărie este calculată folosind formula Haversine.

Aceasta calculează distanța geografică în linie dreaptă dintre două coordonate GPS.

Rezultatul este exprimat în kilometri.

> Distanța calculată nu reprezintă distanța rutieră. Pentru distanța reală pe drum ar fi necesar un serviciu de routing.

---

# Arhitectura aplicației

Fluxul principal este:

```text
Utilizator
    │
    │ latitude + longitude
    ▼
FastAPI Router
    │
    ▼
StationService ──── TTLCache (rezultate recente)
    │
    ├── DistanceService
    │
    └── MonitorulPreturilorClient
              │
              ▼
       Monitorul Prețurilor
              │
              ▼
       Date benzinării + prețuri
              │
              ▼
       StationService
              │
              ▼
       FastAPI Response
```

### `clients/`

Conține codul care comunică direct cu API-uri externe.

`monitorul_preturilor_client.py`:

* face câte o cerere pentru fiecare tip de combustibil (în paralel);
* citește răspunsul XML și unește prețurile pe benzinărie;
* transformă erorile de rețea în erori clare (`502`).

### `services/`

Conține logica aplicației.

`station_service.py`:

* preia datele;
* caută și în jurul zonei, dacă raza este mai mare de 5 km și sunt puține benzinării;
* calculează distanța;
* elimină benzinăriile din afara razei;
* sortează rezultatele;
* limitează rezultatele la maximum 20 de stații.

`cache_service.py` păstrează datele primite de la Monitorul Prețurilor (implicit 15 minute). Utilizatorii aflați la mai puțin de ~100 m unul de altul folosesc aceleași date, dar fiecare primește distanțele calculate față de propria poziție.

`distance_service.py` calculează distanța dintre coordonate.

### `models/`

Conține modelele Pydantic folosite pentru validarea și structurarea datelor.

### `routers/`

Conține endpoint-urile API.

### `certs/`

Conține certificatul intermediar oficial Sectigo. Serverul Monitorului Prețurilor nu îl trimite, iar fără el verificarea HTTPS eșuează pe Linux (inclusiv pe Render). Verificarea HTTPS rămâne activă.

### `tests/`

Conține testele automate ale aplicației.

---

# Configurare

Aplicația folosește variabile de mediu. Toate sunt opționale.

Pentru configurare locală, copiază `.env.example` în `.env`:

```env
MONITORUL_PRETURILOR_BASE_URL=https://monitorulpreturilor.info/pmonsvc/Gas
DEFAULT_RADIUS_KM=10
MAX_RADIUS_KM=10
MAX_STATIONS=20
API_TIMEOUT_SECONDS=15
CACHE_TTL_SECONDS=900
CORS_ORIGINS=*
```

`CORS_ORIGINS` acceptă mai multe domenii, separate prin virgulă (ex. `https://site-ul-meu.ro,http://localhost:8501`).

Fișierul `.env` este ignorat de Git și nu trebuie publicat în repository.

---

# Instalare locală

## 1. Clonarea proiectului

```bash
git clone https://github.com/alexandrapaveluc/benzi-app.git
cd benzi-app
```

## 2. Crearea mediului virtual

```bash
python3 -m venv venv
```

Pe Windows: `python -m venv venv`

## 3. Activarea mediului virtual

Pe macOS/Linux:

```bash
source venv/bin/activate
```

Pe Windows:

```bash
venv\Scripts\activate
```

## 4. Instalarea dependențelor

```bash
pip install -r requirements.txt
```

---

# Pornirea aplicației local

Din folderul principal al proiectului:

```bash
uvicorn app.main:app
```

Aplicația va fi disponibilă la:

```text
http://127.0.0.1:8000
```

Swagger UI:

```text
http://127.0.0.1:8000/docs
```

---

# Testare

Testele automate pot fi rulate folosind:

```bash
pytest
```

Testele nu fac cereri reale către Monitorul Prețurilor; răspunsurile sunt simulate.

Testele verifică, printre altele:

* calcularea distanței (inclusiv valori cunoscute, ex. București – Brașov);
* citirea răspunsului XML și unirea prețurilor pe benzinărie;
* tratarea erorilor de rețea, a timeout-urilor și a răspunsurilor invalide;
* sortarea, limitarea la 20 de rezultate și eliminarea stațiilor din afara razei;
* căutarea extinsă pentru raze mai mari de 5 km;
* cache-ul;
* validarea parametrilor și codurile de răspuns ale endpoint-ului;
* CORS.

---

# Deploy

Aplicația este publicată folosind Render.

Repository-ul GitHub:

```text
https://github.com/alexandrapaveluc/benzi-app
```

API public:

```text
https://benzi-app.onrender.com
```

Swagger public:

```text
https://benzi-app.onrender.com/docs
```

Render preia codul din branch-ul `main`, instalează dependențele și pornește aplicația FastAPI folosind Uvicorn.

---

# Surse de date și limitări

Prețurile provin de la [Monitorul Prețurilor](https://monitorulpreturilor.info/), platforma oficială a Consiliului Concurenței. Datele sunt încărcate de rețelele de benzinării și sunt gratuite.

Limitări:

* sunt incluse doar rețelele mari: Petrom, OMV, Rompetrol, MOL, Lukoil, SOCAR și Gazprom;
* serverul răspunde pe o rază de maximum 5 km și cu maximum 50 de benzinării pe cerere; pentru raze între 5 și 10 km aplicația face cereri suplimentare în jurul zonei;
* serviciul nu are documentație publică, deci formatul se poate schimba;
* prețurile sunt cele raportate de benzinării și pot avea o întârziere față de prețul de la pompă.

---

# Exemplu de utilizare

Un utilizator poate transmite coordonatele:

```text
Latitude: 44.8565
Longitude: 24.8692
Radius: 10 km
```

Backend-ul:

1. primește coordonatele;
2. verifică dacă are deja datele zonei în cache;
3. dacă nu, cere benzinăriile și prețurile de la Monitorul Prețurilor;
4. grupează informațiile pe benzinărie;
5. calculează distanța;
6. sortează benzinăriile;
7. returnează primele 20 de rezultate.

---

# Direcții viitoare

Proiectul poate fi extins cu:

* interfață web;
* aplicație mobilă;
* detectarea automată a locației GPS;
* hartă cu benzinăriile;
* filtrare după tipul de combustibil;
* sortare după preț;
* calcularea costului unei alimentări;
* calcularea costului unei călătorii;
* estimarea economiei dintre două benzinării;
* istoric și statistici ale prețurilor;
* autentificare și conturi de utilizatori;
* notificări când prețul unui combustibil scade.

---

# Status proiect

**Versiune:** MVP

Aplicația are în prezent un backend funcțional care poate:

* comunica cu Monitorul Prețurilor;
* căuta benzinării în apropierea unei locații;
* calcula distanțele;
* procesa prețurile;
* returna rezultatele prin REST API;
* fi testat prin Swagger;
* fi accesat public prin Render.
