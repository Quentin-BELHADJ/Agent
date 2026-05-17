import sys
import json
from duckduckgo_search import DDGS

def search_web(query, max_results=3):
    results_list = []
    
    try:
        with DDGS() as ddgs:
            # On utilise text() pour faire une recherche web classique
            results = ddgs.text(query, max_results=max_results)
            
            for r in results:
                results_list.append({
                    "titre": r.get("title", ""),
                    "lien": r.get("href", ""),
                    "resume": r.get("body", "")
                })
                
        if not results_list:
             return json.dumps({"status": "error", "message": "Aucun résultat trouvé pour cette recherche."})
             
        return json.dumps({"status": "success", "query": query, "results": results_list}, indent=2)

    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"status": "error", "message": "Requête de recherche manquante."}))
        sys.exit(1)
        
    # sys.argv[1] sera la question posée par l'orchestrateur
    query = sys.argv[1]
    print(search_web(query))