import requests
import sys
import json

def get_code_insee(nom_commune):
    """
    Récupère le code INSEE d'une commune via l'API geo.api.gouv.fr
    """
    url = f"https://geo.api.gouv.fr/communes?nom={nom_commune}&fields=code&limit=1"
    headers = {'User-Agent': 'EmergencySkill/1.0'}
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        data = response.json()
        
        if not data:
            return json.dumps({
                "status": "error",
                "message": f"Commune introuvable : {nom_commune}"
            }, ensure_ascii=False)
            
        code_insee = data[0].get("code")
        return json.dumps({
            "status": "success",
            "commune": nom_commune,
            "code_insee": code_insee
        }, ensure_ascii=False)
        
    except Exception as e:
        return json.dumps({"status": "error", "message": f"Erreur lors de la requête : {str(e)}"}, ensure_ascii=False)

if __name__ == "__main__":
    commune = sys.argv[1] if len(sys.argv) > 1 else "Belfort"
    print(get_code_insee(commune))
