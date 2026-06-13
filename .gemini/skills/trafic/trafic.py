import requests
from bs4 import BeautifulSoup
import sys
import re
import json
import urllib3

# Désactiver les avertissements SSL pour éviter les messages polluants lors des requêtes verify=False
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Dictionnaire des sources TIPI de Bison Futé
SOURCES = {
    "bouchons": "https://tipi.bison-fute.gouv.fr/bison-fute-ouvert/publicationsDIR/Evenementiel-DIR/cnir/RecapBouchonsFranceEntiere.html",
    "evenements": "https://tipi.bison-fute.gouv.fr/bison-fute-ouvert/publicationsDIR/Evenementiel-DIR/cnir/RecapTraficFranceEntiere.html",
    "chantiers": "https://tipi.bison-fute.gouv.fr/bison-fute-ouvert/publicationsDIR/Evenementiel-DIR/cnir/RecapChantiersEnCours.html",
    "previsions": "https://tipi.bison-fute.gouv.fr/bison-fute-ouvert/publicationsDIR/Evenementiel-DIR/cnir/RecapChantiersPrevi.html"
}


def resoudre_ville(mot_cle):
    """Tente de résoudre une ville en numéro + nom de département via l'API geo.gouv.fr"""
    try:
        r = requests.get(
            "https://geo.api.gouv.fr/communes",
            params={"nom": mot_cle, "fields": "departement", "boost": "population", "limit": 1},
            timeout=5,
            verify=False
        )
        data = r.json()
        if data:
            dept = data[0]["departement"]
            return [mot_cle.lower(), dept["code"], dept["nom"].lower()]
    except Exception:
        pass
    return [mot_cle.lower()]  # fallback : on garde le mot-clé brut en minuscules


def scrape_tipi(type_info, mot_cle_raw):
    """Scrape le site de Bison Futé pour récupérer les infos trafic associées au mot-clé."""
    url = SOURCES.get(type_info, SOURCES["bouchons"])
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        # verify=False permet de contourner les erreurs locales de certificats racine sur certains serveurs de l'État
        response = requests.get(url, headers=headers, timeout=15, verify=False)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # On recolle le texte pour l'analyse
        texte_brut = soup.get_text(" ", strip=True)
        blocs = re.split(r'(\*{2,3})', texte_brut)
        
        mot_cle = resoudre_ville(mot_cle_raw)

        alertes_retrouvees = []
        for i in range(1, len(blocs), 2):
            symbole = blocs[i]
            contenu = blocs[i+1] if i+1 < len(blocs) else ""
            alerte_complete = f"{symbole} {contenu}"
            
            # mot_cle est une liste de termes en minuscules. On cherche si l'un d'eux est dans l'alerte.
            if any(term in alerte_complete.lower() for term in mot_cle):
                alerte_propre = ' '.join(alerte_complete.split())
                alertes_retrouvees.append(alerte_propre)
        
        if not alertes_retrouvees:
            return json.dumps({
                "status": "success",
                "type_info": type_info,
                "mot_cle": mot_cle_raw,
                "alertes": []
            }, ensure_ascii=False)

        return json.dumps({
            "status": "success",
            "type_info": type_info,
            "mot_cle": mot_cle_raw,
            "alertes": alertes_retrouvees[:3]
        }, ensure_ascii=False)

    except Exception as e:
        return json.dumps({"status": "error", "message": f"Erreur technique ({type_info}) : {str(e)}"}, ensure_ascii=False)


if __name__ == "__main__":
    # Usage : python3 trafic.py [bouchons|evenements|chantiers|previsions] [mot_cle]
    type_req = sys.argv[1] if len(sys.argv) > 1 else "bouchons"
    mot_cle = sys.argv[2] if len(sys.argv) > 2 else "France"
    print(scrape_tipi(type_req, mot_cle))