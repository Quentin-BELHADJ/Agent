import sys
import json
import requests

def triangulate(json_args):
    result = {
        "status": "success",
        "total_trouve": 0,
        "resultats": []
    }
    
    try:
        # L'orchestrateur (Gemini) nous envoie ses déductions en JSON
        args = json.loads(json_args)
        pays = args.get("pays")
        rue = args.get("rue")
        poi = args.get("poi_proche") # Le Point d'Intérêt (ex: bakery, pharmacy)
        
        if not pays or not rue:
            return json.dumps({"status": "error", "message": "Les champs 'pays' et 'rue' sont obligatoires pour la triangulation."})
        
        # Construction de la requête spatiale Overpass QL
        query = '[out:json][timeout:25];\n'
        query += f'area["name"="{pays}"]->.searchArea;\n'
        query += f'way["name"="{rue}"](area.searchArea)->.target_street;\n'
        
        if poi:
            # S'il y a un POI, on cherche sa présence à moins de 50 mètres de la rue
            query += f'nwr(around.target_street:50)["amenity"="{poi}"];\n'
        else:
            # Sinon, on sort juste les coordonnées de la rue
            query += '.target_street;\n'
            
        query += 'out center;'
        
        # Requête vers le serveur public OpenStreetMap
        resp = requests.post("http://overpass-api.de/api/interpreter", data={'data': query})
        resp.raise_for_status()
        data = resp.json()
        
        elements = data.get("elements", [])
        result["total_trouve"] = len(elements)
        
        if not elements:
            result["message"] = "Aucun lieu ne correspond à cette combinaison."
            return json.dumps(result, indent=2)
            
        # On limite aux 5 premiers résultats pour ne pas inonder le terminal
        for el in elements[:5]:
            lat = el.get("lat") or el.get("center", {}).get("lat")
            lon = el.get("lon") or el.get("center", {}).get("lon")
            if lat and lon:
                result["resultats"].append({
                    "type_element": el.get("type"),
                    "google_maps_link": f"https://www.google.com/maps?q={lat},{lon}"
                })
                
        return json.dumps(result, indent=2)
        
    except json.JSONDecodeError:
        return json.dumps({"status": "error", "message": "Format JSON invalide fourni par l'agent."})
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"status": "error", "message": "Arguments JSON manquants."}))
        sys.exit(1)
        
    # sys.argv[1] sera la chaîne JSON générée par Gemini
    print(triangulate(sys.argv[1]))