# BENZI-APP

## Fuel Finder

BENZI-APP este o aplicație backend pentru identificarea benzinăriilor din apropierea utilizatorului și compararea prețurilor combustibililor.

Aplicația primește coordonatele geografice ale utilizatorului, caută benzinăriile din apropiere, preia prețurile combustibililor prin API-ul PretCarburant, calculează distanța până la fiecare stație și returnează rezultatele sortate după distanță.

---

## Funcționalități

Aplicația poate:

* primi latitudinea și longitudinea utilizatorului;
* căuta benzinării într-o anumită rază;
* prelua prețurile combustibililor;
* identifica tipul de combustibil disponibil;
* calcula distanța dintre utilizator și fiecare benzinărie;
* sorta benzinăriile de la cea mai apropiată la cea mai îndepărtată;
* returna maximum 20 de benzinării;
* afișa datele printr-un API REST;
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
* PretCarburant API
* Render pentru deploy

---

## Structura proiectului

```text
benzi-app/
│
├── app/
│   ├── clients/
│   │   └── pretcarburant_client.py
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
│   │   ├── distance_service.py
│   │   └── station_service.py
│   │
│   ├── tests/
│   │   ├── test_distance_service.py
│   │   └── test_station_service.py
│   │
│   ├── config.py
│   └── main.py
│
├── .env
├── .gitignore
├── README.md
└── requirements.txt
```

---

# API

## GET `/stations/nearby`

Endpoint-ul principal al aplicației.

Primește:

* `latitude` — latitudinea utilizatorului;
* `longitude` — longitudinea utilizatorului;
* `radius_km` — raza de căutare în kilometri.

### Exemplu

```text
GET /stations/nearby?latitude=44.8565&longitude=24.8692&radius_km=10
```

### Exemplu cURL

```bash
curl -X 'GET' \
  'https://benzi-app.onrender.com/stations/nearby?latitude=44.8565&longitude=24.8692&radius_km=10' \
  -H 'accept: */*' \
  -H 'X-Api-Key: test123'
```

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

---

# Răspunsul API

API-ul returnează informații despre locația utilizatorului, data actualizării prețurilor și lista benzinăriilor.

Exemplu simplificat:

```json
{
  "location": {
    "latitude": 44.8565,
    "longitude": 24.8692
  },
  "radius_km": 10,
  "price_data_updated_at": "2026-10-05T17:15:07+00:00",
  "stations": [
    {
      "station_id": "123",
      "name": "Petrom - Pitesti",
      "brand": "Petrom",
      "address": "Exemplu",
      "city": "Pitesti",
      "county": "Arges",
      "latitude": 44.856,
      "longitude": 24.869,
      "distance_km": 1.37,
      "prices": {
        "gasoline": {
          "standard": 10.05,
          "premium": null
        },
        "diesel": {
          "standard": 10.91,
          "premium": 11.76
        }
      }
    }
  ]
}
```

---

# Tipuri de combustibil

Aplicația lucrează cu următoarele tipuri de combustibil:

| Tip API             | Descriere         |
| ------------------- | ----------------- |
| `benzina_standard`  | Benzină standard  |
| `benzina_premium`   | Benzină premium   |
| `motorina_standard` | Motorină standard |
| `motorina_premium`  | Motorină premium  |

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
StationService
    │
    ├── DistanceService
    │
    └── PretCarburantClient
              │
              ▼
       PretCarburant API
              │
              ▼
       Date benzinării
              │
              ▼
       StationService
              │
              ▼
       FastAPI Response
```

### `clients/`

Conține codul care comunică direct cu API-uri externe.

`pretcarburant_client.py` se ocupă de request-urile către PretCarburant API.

### `services/`

Conține logica aplicației.

`station_service.py`:

* preia datele;
* grupează informațiile aceleiași benzinării;
* asociază prețurile combustibililor;
* calculează distanța;
* sortează rezultatele;
* limitează rezultatele la maximum 20 de stații.

`distance_service.py` calculează distanța dintre coordonate.

### `models/`

Conține modelele Pydantic folosite pentru validarea și structurarea datelor.

### `routers/`

Conține endpoint-urile API.

### `tests/`

Conține testele automate ale aplicației.

---

# Configurare

Aplicația folosește variabile de mediu.

Exemplu `.env`:

```env
PRET_CARBURANT_BASE_URL=https://pretcarburant.ro/api/v1
PRET_CARBURANT_API_KEY=
DEFAULT_RADIUS_KM=10
MAX_STATIONS=20
API_TIMEOUT_SECONDS=10
```

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

## 3. Activarea mediului virtual

Pe macOS/Linux:

```bash
source venv/bin/activate
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

Testele verifică, printre altele:

* calcularea distanței;
* agregarea prețurilor combustibililor;
* construirea corectă a obiectelor pentru benzinării.

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

# Exemplu de utilizare

Un utilizator poate transmite coordonatele:

```text
Latitude: 44.8565
Longitude: 24.8692
Radius: 10 km
```

Backend-ul:

1. primește coordonatele;
2. cere benzinăriile din zonă;
3. primește prețurile combustibililor;
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

* comunica cu PretCarburant API;
* căuta benzinării în apropierea unei locații;
* calcula distanțele;
* procesa prețurile;
* returna rezultatele prin REST API;
* fi testat prin Swagger;
* fi accesat public prin Render.
