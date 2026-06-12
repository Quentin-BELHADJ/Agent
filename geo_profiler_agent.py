import os
import sys
import json
import base64
import subprocess
from langchain_core.tools import tool
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage
from langgraph.prebuilt import create_react_agent

# Get the base directory dynamically
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SKILLS_DIR = os.path.join(BASE_DIR, ".gemini", "skills")

# Prompts
SYSTEM_PROMPT = """Tu es "Geo-Profiler", un agent d'investigation OSINT et GEOINT expert.
Ton objectif est de déterminer la localisation géographique exacte (pays, ville, rue, coordonnées GPS) de toute photographie fournie par l'utilisateur. Tu ne dois JAMAIS deviner ou halluciner une localisation : tu dois la prouver en utilisant tes outils dans un ordre logique et strict.

Pour chaque image fournie, tu DOIS suivre cette procédure pas à pas (L'Entonnoir GEOINT) :

ÉTAPE 1 : L'ADN du fichier
Commence TOUJOURS par utiliser l'outil geoint_exif_extractor. 
Si des coordonnées GPS sont trouvées, note-les, mais NE LES VALIDE PAS ENCORE.

ÉTAPE 2 : L'Observation de l'environnement
Utilise ensuite geoint_vision_analyzer pour scanner l'infrastructure, la végétation, l'architecture et le climat.
Confronte les éventuelles données EXIF à l'analyse visuelle. Déduis une région ou un pays.

ÉTAPE 3 : L'Extraction de texte
Utilise geoint_ocr_reader pour extraire mathématiquement tout le texte visible (panneaux, devantures).

ÉTAPE 4 : La Vérification des Faits
Si tu as extrait des textes, utilise geoint_web_search pour faire une recherche afin de trouver le pays ou la ville.

ÉTAPE 5 : La Triangulation
Une fois que tu as déduit avec certitude un PAYS, et que l'OCR a trouvé un NOM DE RUE, utilise geoint_map_triangulator.

Format de Réponse (Dossier de renseignement) :
1. Rapport d'intégrité : Les EXIF étaient-ils présents ou trafiqués ?
2. Faits Visuels : Ce qui a trahi la région.
3. Indices textuels : Ce que l'OCR a révélé et que le Web a confirmé.
4. Conclusion : La localisation finale avec un lien Google Maps.

Réponds en français de manière calme et opérationnelle. Sortie JSON ou texte structuré clair.
"""

VISION_PROMPT = """Tu es un analyste expert en GEOINT et en observation OSINT. 
Ton rôle est de déconstruire visuellement cette image pour en extraire des faits physiques indiscutables, qui serviront de base à une triangulation géographique.
Tu ne dois JAMAIS deviner, extrapoler ou annoncer le pays/la ville finale à cette étape. Ton unique but est de remplir une grille d'observation stricte.

Directives d'Analyse Visuelle :
1. Infrastructure Routière (La priorité) : Marquage au sol, bollards (délinéateurs), panneaux de signalisation, sens de circulation.
2. Réseaux et Architecture : Poteaux électriques / Télécoms, véhicules (plaques d'immatriculation), urbanisme (style, toiture, matériaux).
3. Environnement et Topographie : Géologie (sol), botanique (végétation), topographie (relief).
4. Climat et Lumière : Ombres et Soleil, météo.

Génère ta réponse sous la forme d'un objet JSON pur et valide (aucune explication autour).
{
  "infrastructure_routiere": {
    "marquage_au_sol": "",
    "bollards_delineateurs": "",
    "panneaux_et_supports": "",
    "sens_de_circulation": ""
  },
  "reseaux_et_architecture": {
    "poteaux_electriques": "",
    "plaques_immatriculation": "",
    "details_architecturaux": ""
  },
  "environnement_naturel": {
    "couleur_et_type_de_sol": "",
    "vegetation_dominante": "",
    "topographie": ""
  },
  "climat_et_lumiere": {
    "direction_des_ombres": "",
    "conditions_visibles": ""
  },
  "textes_et_lettrages_visibles": [],
  "anomalies_ou_details_specifiques": ""
}
"""

# Tools
@tool
def geoint_exif_extractor(image_path: str) -> str:
    """Extrait les métadonnées cachées (EXIF) et les coordonnées GPS d'une photographie."""
    script_path = os.path.join(SKILLS_DIR, "geoint-exif", "extract_exif.py")
    result = subprocess.run([sys.executable, script_path, image_path], capture_output=True, text=True)
    return result.stdout

@tool
def geoint_ocr_reader(image_path: str) -> str:
    """Extrait de manière fiable tout le texte visible sur une image (panneaux, devantures, plaques) grâce à l'intelligence artificielle (EasyOCR)."""
    script_path = os.path.join(SKILLS_DIR, "geoint-ocr", "extract_text.py")
    result = subprocess.run([sys.executable, script_path, image_path], capture_output=True, text=True)
    return result.stdout

@tool
def geoint_web_search(query: str) -> str:
    """Effectue des recherches sur le web pour vérifier des indices géographiques, des normes routières ou la localisation de points d'intérêt."""
    script_path = os.path.join(SKILLS_DIR, "geoint-search", "search_web.py")
    result = subprocess.run([sys.executable, script_path, query], capture_output=True, text=True)
    return result.stdout

@tool
def geoint_map_triangulator(pays: str, rue: str, poi_proche: str = "") -> str:
    """Utilise la base de données cartographique (OpenStreetMap) pour trouver les coordonnées GPS exactes en croisant un pays, un nom de rue et un commerce de proximité."""
    data = {"pays": pays, "rue": rue, "poi_proche": poi_proche}
    script_path = os.path.join(SKILLS_DIR, "geoint-map", "triangulate.py")
    result = subprocess.run([sys.executable, script_path, json.dumps(data)], capture_output=True, text=True)
    return result.stdout

@tool
def geoint_vision_analyzer(image_path: str) -> str:
    """Analyse visuelle experte d'une photographie pour extraire la "méta" géographique (infrastructure, environnement, architecture) et générer une grille de faits structurés."""
    try:
        with open(image_path, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode("utf-8")
    except Exception as e:
        return json.dumps({"status": "error", "message": f"Erreur lors de la lecture de l'image : {e}"})

    llm = ChatGoogleGenerativeAI(model="gemini-1.5-pro", temperature=0)
    
    msg = HumanMessage(
        content=[
            {"type": "text", "text": VISION_PROMPT},
            {
                "type": "image_url",
                "image_url": {"url": f"data:image/jpeg;base64,{encoded_string}"},
            },
        ]
    )
    
    try:
        response = llm.invoke([msg])
        return response.content
    except Exception as e:
        return json.dumps({"status": "error", "message": f"Erreur lors de l'appel vision : {e}"})

# Build agent
def create_geoprofiler_agent():
    tools = [geoint_exif_extractor, geoint_ocr_reader, geoint_web_search, geoint_map_triangulator, geoint_vision_analyzer]
    llm = ChatGoogleGenerativeAI(model="gemini-1.5-pro", temperature=0.1)
    agent_executor = create_react_agent(llm, tools, state_modifier=SYSTEM_PROMPT)
    return agent_executor

if __name__ == "__main__":
    if len(sys.argv) > 1:
        target_image = sys.argv[1]
        print(json.dumps({"status": "info", "message": f"Début de l'investigation sur : {target_image}"}))
        try:
            agent = create_geoprofiler_agent()
            response = agent.invoke({"messages": [("user", f"Localise cette image de façon méthodique : {target_image}")]})
            print(json.dumps({
                "status": "success",
                "result": response["messages"][-1].content
            }, indent=2))
        except Exception as e:
             print(json.dumps({"status": "error", "message": str(e)}, indent=2))
    else:
        print(json.dumps({"status": "error", "message": "Usage: python geo_profiler_agent.py <chemin_vers_image>"}, indent=2))
