import requests
import json
import time

bbox = "43.6,20.2,48.3,29.7"  # sud, vest, nord, est - Romania

query = f"""
[out:json][timeout:180];
node["amenity"="fuel"]({bbox});
out body;
"""

headers = {
    "User-Agent": "Proiect-scoala-benzi-app/1.0 (student project, contact: exemplu@email.com)"
}

servere = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
    "https://overpass.openstreetmap.fr/api/interpreter",
]

data = None

for server in servere:
    print(f"Incerc serverul: {server} ...")
    try:
        response = requests.post(server, data={"data": query}, headers=headers, timeout=200)
        response.raise_for_status()
        data = response.json()
        print(f"A functionat cu: {server}")
        break
    except Exception as e:
        print(f"Nu a mers cu {server}. Eroare: {e}")
        print("Astept 15 secunde inainte sa incerc urmatorul server...")
        time.sleep(15)

if data is None:
    print("Niciun server Overpass nu a raspuns corect. Incearca din nou peste cateva minute.")
else:
    benzinarii = data["elements"]
    print(f"Am gasit {len(benzinarii)} benzinarii in Romania.")

    lista_curata = []
    for b in benzinarii:
        tags = b.get("tags", {})
        lista_curata.append({
            "id": b["id"],
            "nume": tags.get("name", "Fara nume"),
            "brand": tags.get("brand", "Necunoscut"),
            "lat": b["lat"],
            "lon": b["lon"]
        })

    with open("benzinarii_romania.json", "w", encoding="utf-8") as f:
        json.dump(lista_curata, f, ensure_ascii=False, indent=2)

    print("Salvat in fisierul benzinarii_romania.json")