import requests
import sys
import json

def get_risque_sismique(code_insee):
    """
    Récupère le zonage sismique d'une commune via l'API Géorisques (en utilisant le code INSEE)
    """
    url = f"https://georisques.gouv.fr/api/v1/zonage_sismique?code_insee={code_insee}"
    headers = {'User-Agent': 'EmergencySkill/1.0'}
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        data = response.json()
        
        # L'API Géorisques renvoie {"data": [...]}
        results = data.get("data", [])
        
        if not results:
            return json.dumps({
                "status": "error",
                "message": f"Aucune donnée sismique trouvée pour le code INSEE : {code_insee}"
            }, ensure_ascii=False)
            
        zone_sismique = str(results[0].get("zone_sismicite"))
        
        # Traduction du code de zone en texte explicite
        descriptions = {
            "1": "Très faible",
            "2": "Faible",
            "3": "Modérée",
            "4": "Moyenne",
            "5": "Forte"
        }
        
        description = descriptions.get(zone_sismique, "Inconnue")
        
        return json.dumps({
            "status": "success",
            "code_insee": code_insee,
            "zone_sismique": zone_sismique,
            "description": description
        }, ensure_ascii=False)
        
    except Exception as e:
        return json.dumps({"status": "error", "message": f"Erreur lors de la requête sismique : {str(e)}"}, ensure_ascii=False)

if __name__ == "__main__":
    code = sys.argv[1] if len(sys.argv) > 1 else "90010" # 90010 = Belfort
    print(get_risque_sismique(code))
