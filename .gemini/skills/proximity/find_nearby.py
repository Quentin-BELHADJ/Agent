import requests
import sys
import json

def get_nearby_universal(tag_key, tag_value, location_name):
    # Géocodage (trouver les coordonnées de la ville/lieu)
    geo_url = f"https://nominatim.openstreetmap.org/search?q={location_name}&format=json&limit=1"
    headers = {'User-Agent': 'EmergencySkill/1.0'}
    
    try:
        geo_res = requests.get(geo_url, headers=headers, timeout=10)
        if not geo_res.json():
            return json.dumps({"status": "error", "message": f"Localisation introuvable : {location_name}"}, ensure_ascii=False)
        
        lat, lon = geo_res.json()[0]['lat'], geo_res.json()[0]['lon']

        # Requête Overpass Universelle
        # nwr = node, way, relation (trouve les points, les bâtiments et les zones)
        overpass_url = "http://overpass-api.de/api/interpreter"
        query = f"""
        [out:json];
        nwr["{tag_key}"="{tag_value}"](around:3000,{lat},{lon});
        out center;
        """
        
        response = requests.get(overpass_url, params={'data': query}, timeout=15)
        data = response.json()

        results = []
        for element in data.get('elements', [])[:8]: # Un peu plus de résultats
            name = element.get('tags', {}).get('name', 'Sans nom')
            e_lat = element.get('lat') or element.get('center', {}).get('lat')
            e_lon = element.get('lon') or element.get('center', {}).get('lon')
            map_link = f"https://www.google.com/maps?q={e_lat},{e_lon}"
            results.append({
                "name": name,
                "lat": e_lat,
                "lon": e_lon,
                "map_link": map_link
            })

        return json.dumps({
            "status": "success",
            "metadata": {"tag_key": tag_key, "tag_value": tag_value, "location": location_name},
            "results": results
        }, ensure_ascii=False)

    except Exception as e:
        return json.dumps({"status": "error", "message": f"Erreur : {str(e)}"}, ensure_ascii=False)

if __name__ == "__main__":
    # Usage: python3 find_nearby.py [tag_key] [tag_value] [location]
    k = sys.argv[1] if len(sys.argv) > 1 else "amenity"
    v = sys.argv[2] if len(sys.argv) > 2 else "restaurant"
    loc = sys.argv[3] if len(sys.argv) > 3 else "Belfort"
    print(get_nearby_universal(k, v, loc))