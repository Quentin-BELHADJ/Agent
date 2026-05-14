import requests
from bs4 import BeautifulSoup
import sys
import re

# Dictionnaire des sources TIPI
SOURCES = {
    "bouchons": "https://tipi.bison-fute.gouv.fr/bison-fute-ouvert/publicationsDIR/Evenementiel-DIR/cnir/RecapBouchonsFranceEntiere.html",
    "evenements": "https://tipi.bison-fute.gouv.fr/bison-fute-ouvert/publicationsDIR/Evenementiel-DIR/cnir/RecapTraficFranceEntiere.html",
    "chantiers": "https://tipi.bison-fute.gouv.fr/bison-fute-ouvert/publicationsDIR/Evenementiel-DIR/cnir/RecapChantiersEnCours.html",
    "previsions": "https://tipi.bison-fute.gouv.fr/bison-fute-ouvert/publicationsDIR/Evenementiel-DIR/cnir/RecapChantiersPrevi.html"
}

def scrape_tipi(type_info, mot_cle):
    url = SOURCES.get(type_info, SOURCES["bouchons"])
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        
        # On recolle le texte comme précédemment
        texte_brut = soup.get_text(" ", strip=True)
        blocs = re.split(r'(\*{2,3})', texte_brut)
        
        alertes_retrouvees = []
        for i in range(1, len(blocs), 2):
            symbole = blocs[i]
            contenu = blocs[i+1] if i+1 < len(blocs) else ""
            alerte_complete = f"{symbole} {contenu}"
            
            if mot_cle.lower() in alerte_complete.lower():
                alerte_propre = ' '.join(alerte_complete.split())
                alertes_retrouvees.append(alerte_propre)
        
        if not alertes_retrouvees:
            return f"RAS sur '{type_info}' pour '{mot_cle}'."

        return f"--- Source : {type_info.upper()} ---\n" + "\n\n".join(alertes_retrouvees[:3])

    except Exception as e:
        return f"Erreur technique ({type_info}) : {str(e)}"

if __name__ == "__main__":
    # Usage : python3 trafic.py [bouchons|evenements|chantiers|previsions] [mot_cle]
    type_req = sys.argv[1] if len(sys.argv) > 1 else "bouchons"
    mot_cle = sys.argv[2] if len(sys.argv) > 2 else "France"
    print(scrape_tipi(type_req, mot_cle))