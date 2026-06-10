import requests
import sys
import json
import math

def haversine(lat1, lon1, lat2, lon2):
    R = 6371000
    phi1, phi2 = math.radians(float(lat1)), math.radians(float(lat2))
    dphi = math.radians(float(lat2) - float(lat1))
    dlambda = math.radians(float(lon2) - float(lon1))
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
    return round(2 * R * math.asin(math.sqrt(a)))

def safe_json(response, context="requête"):
    if response.status_code != 200:
        raise ValueError(f"{context} a échoué : HTTP {response.status_code}")
    text = response.text.strip()
    if not text:
        raise ValueError(f"{context} a retourné une réponse vide")
    try:
        return response.json()
    except Exception:
        raise ValueError(f"{context} : JSON invalide — début de réponse : {response.text[:200]}")

def get_location(location_hint=None):
    headers = {'User-Agent': 'ProximitySkill/1.0 (projet-universitaire)'}

    if location_hint:
        r = requests.get(
            "https://nominatim.openstreetmap.org/search",
            params={"q": location_hint, "format": "json", "limit": 1},
            headers=headers, timeout=10
        )
        data = safe_json(r, "Nominatim")
        if not data:
            raise ValueError(f"Lieu introuvable : {location_hint}")
        return float(data[0]['lat']), float(data[0]['lon']), data[0]['display_name'], "geocodage"

    r = requests.get("http://ip-api.com/json", timeout=5)
    data = safe_json(r, "ip-api")
    if data.get("status") == "success":
        return data["lat"], data["lon"], f"{data['city']}, {data['regionName']}", "ip"
    raise ValueError("Géolocalisation IP impossible")

def get_nearby(tag_key, tag_value, location_hint=None, rayon=3000):
    try:
        lat, lon, location_name, methode = get_location(location_hint)

        query = f"""
        [out:json][timeout:25];
        nwr["{tag_key}"="{tag_value}"](around:{rayon},{lat},{lon});
        out center;
        """
        response = requests.get(
            "http://overpass-api.de/api/interpreter",
            params={'data': query},
            timeout=20
        )
        elements = safe_json(response, "Overpass").get('elements', [])

        results = []
        for el in elements:
            tags  = el.get('tags', {})
            e_lat = el.get('lat') or el.get('center', {}).get('lat')
            e_lon = el.get('lon') or el.get('center', {}).get('lon')
            if not e_lat or not e_lon:
                continue

            rue     = tags.get('addr:street', '')
            numero  = tags.get('addr:housenumber', '')
            adresse = f"{numero} {rue}".strip() or None

            results.append({
                "name":       tags.get('name', 'Sans nom'),
                "distance_m": haversine(lat, lon, e_lat, e_lon),
                "adresse":    adresse,
                "telephone":  tags.get('phone') or tags.get('contact:phone'),
                "horaires":   tags.get('opening_hours'),
                "map_link":   f"https://www.google.com/maps?q={e_lat},{e_lon}"
            })

        results.sort(key=lambda x: x['distance_m'])

        return json.dumps({
            "status":                "success",
            "localisation_utilisee": location_name,
            "methode_localisation":  methode,
            "tag":                   f"{tag_key}={tag_value}",
            "rayon_m":               rayon,
            "resultats":             results[:8]
        }, ensure_ascii=False)

    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)}, ensure_ascii=False)

if __name__ == "__main__":
    k   = sys.argv[1] if len(sys.argv) > 1 else "amenity"
    v   = sys.argv[2] if len(sys.argv) > 2 else "restaurant"
    loc = sys.argv[3] if len(sys.argv) > 3 else None
    print(get_nearby(k, v, loc))