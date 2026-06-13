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
        error_msg = str(e)
        if "ratelimit" in error_msg.lower() or "rate limit" in error_msg.lower():
            msg = "Erreur de recherche (DuckDuckGo Rate Limit). N'ESSAYEZ PLUS d'exécuter des recherches web pour cet incident. Vous devez dresser vos conclusions finales en utilisant uniquement les indices visuels et textuels (OCR) déjà collectés."
        else:
            msg = f"Erreur de recherche : {error_msg}. Si le moteur est indisponible, n'insistez pas et passez à la conclusion avec les éléments visuels et textuels."
        return json.dumps({"status": "error", "message": msg}, ensure_ascii=False)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"status": "error", "message": "Requête de recherche manquante."}))
        sys.exit(1)
        
    # sys.argv[1] sera la question posée par l'orchestrateur
    query = sys.argv[1]
    print(search_web(query))