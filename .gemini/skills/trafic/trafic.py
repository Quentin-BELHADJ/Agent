import requests
from bs4 import BeautifulSoup
import sys
import re

def scrape_adaptatif(mot_cle):
    url = "https://tipi.bison-fute.gouv.fr/bison-fute-ouvert/publicationsDIR/Evenementiel-DIR/cnir/RecapBouchonsFranceEntiere.html"
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(response.text, 'html.parser')
        alertes_retrouvees = []
        
        # On récupère tout le texte et on nettoie les espaces multiples
        # On remplace les retours à la ligne par des espaces simples pour "recoller" les phrases
        texte_brut = soup.get_text(" ", strip=True)
        
        # On utilise une expression régulière pour séparer les alertes qui commencent par ** ou ***
        # Cela crée une liste de blocs d'informations complets
        blocs = re.split(r'(\*{2,3})', texte_brut)
        
        alertes_reconstituees = []
        # On parcourt les blocs (on recolle le symbole ** avec son texte)
        for i in range(1, len(blocs), 2):
            symbole = blocs[i]
            contenu = blocs[i+1] if i+1 < len(blocs) else ""
            alerte_complete = f"{symbole} {contenu}"
            
            # Filtrage par mot-clé (ex: A8)
            if mot_cle.lower() in alerte_complete.lower():
                # On nettoie les espaces doubles créés par le collage
                alerte_propre = ' '.join(alerte_complete.split())
                alertes_retrouvees.append(alerte_propre)
        
        if not alertes_retrouvees:
            return f"RAS : Aucune alerte active pour '{mot_cle}'."

        # On limite à 3 résultats pour préserver le contexte de Gemini 
        return "\n\n".join(alertes_retrouvees[:3])

    except Exception as e:
        return f"Erreur technique : {str(e)}"

if __name__ == "__main__":
    query = sys.argv[1] if len(sys.argv) > 1 else "France"
    print(scrape_adaptatif(query))