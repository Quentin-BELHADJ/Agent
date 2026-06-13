#!/usr/bin/env python3
"""
crisis_navigator.py — Implémentation de l'Agent d'Évacuation et de Guidage Routier (Crisis Navigator).
Coordonné avec LangChain et LangGraph.
"""

import os
import sys
import json
import subprocess
from pathlib import Path
from typing import Optional

# Importations LangChain / LangGraph
from langchain_core.tools import tool
from llm import get_llm
from langgraph.prebuilt import create_react_agent

# Configuration des chemins locaux pour importer et exécuter les compétences
BASE_DIR = Path(__file__).resolve().parent
if (BASE_DIR / ".gemini" / "skills").exists():
    SKILLS_DIR = BASE_DIR / ".gemini" / "skills"
else:
    SKILLS_DIR = BASE_DIR.parent / "skills"


def load_env_file():
    """Charge les variables d'environnement depuis un fichier .env local s'il existe."""
    env_path = BASE_DIR / ".env"
    if env_path.exists():
        try:
            with open(env_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        key, val = line.split("=", 1)
                        os.environ[key.strip()] = val.strip().strip('"').strip("'")
        except Exception:
            pass


# Chargement immédiat du .env s'il existe
load_env_file()



def run_skill(args: list[str], cwd: Optional[Path] = None, error_message: str = "Une erreur est survenue.") -> str:
    """Exécute une compétence dans un sous-processus et gère les erreurs."""
    res = subprocess.run(
        args,
        capture_output=True,
        text=True,
        check=False,
        cwd=str(cwd) if cwd else None
    )
    if res.returncode != 0:
        return json.dumps({
            "status": "error",
            "message": res.stderr.strip() or error_message
        }, ensure_ascii=False)
    return res.stdout.strip()


@tool
def self_location() -> str:
    """Détermine la position géographique actuelle (coordonnées GPS lat/lon, ville, pays)
    de l'utilisateur en utilisant la géolocalisation IP.
    À utiliser en priorité si l'utilisateur ne fournit pas sa position.
    """
    script_path = SKILLS_DIR / "self-position" / "self_location.py"
    return run_skill(
        [sys.executable, str(script_path)],
        error_message="Une erreur est survenue lors de la localisation."
    )


@tool
def proximity_search(tag_key: str, tag_value: str, location_hint: Optional[str] = None) -> str:
    """Localise des points d'intérêt à proximité via OpenStreetMap (ex: hôpitaux, casernes de pompiers).
    
    Args:
        tag_key: le type de tag OSM, e.g., 'amenity' ou 'shop'.
        tag_value: la valeur du tag OSM, e.g., 'hospital' pour un hôpital, 'fire_station' pour les pompiers.
        location_hint: un lieu optionnel (ville comme 'Besançon', adresse, ou coordonnées GPS 'lat,lon').
                       Si absent, se géolocalise par IP.
    """
    script_path = SKILLS_DIR / "proximity" / "find_nearby.py"
    args = [sys.executable, str(script_path), tag_key, tag_value]
    if location_hint:
        args.append(location_hint)
    return run_skill(
        args,
        cwd=SKILLS_DIR / "proximity",
        error_message="Une erreur est survenue lors de la recherche de proximité."
    )


@tool
def trafic_bison_fute(type_info: str, location_or_route: Optional[str] = None) -> str:
    """Fournit l'état du trafic routier en temps réel en France (bouchons, accidents, fermetures, chantiers).
    
    Args:
        type_info: le type de recherche. Doit être l'un de: 'bouchons', 'evenements' (pour fermetures/accidents), 'chantiers', 'previsions'.
        location_or_route: nom d'une ville, d'un département, d'une région ou d'une autoroute (ex: 'A6', 'Paris', '69').
                           Par défaut, 'France'.
    """
    script_path = SKILLS_DIR / "trafic" / "trafic.py"
    args = [sys.executable, str(script_path), type_info]
    if location_or_route:
        args.append(location_or_route)
    return run_skill(
        args,
        cwd=SKILLS_DIR / "trafic",
        error_message="Une erreur est survenue lors de la récupération du trafic."
    )


@tool
def vigicrues(lat: float, lon: float, radius: Optional[float] = 30.0, max_results: Optional[int] = 5) -> str:
    """Interroge les stations hydrométriques (hauteurs d'eau et débits des rivières) autour d'un point GPS pour évaluer les risques de crue.
    
    Args:
        lat: la latitude du point d'intérêt.
        lon: la longitude du point d'intérêt.
        radius: le rayon de recherche en km (défaut: 30.0).
        max_results: le nombre maximal de stations à renvoyer (défaut: 5).
    """
    script_path = SKILLS_DIR / "vigicrues" / "main.py"
    args = [
        sys.executable,
        str(script_path),
        "incident",
        "--lat", str(lat),
        "--lon", str(lon),
        "--radius", str(radius),
        "--max", str(max_results)
    ]
    return run_skill(
        args,
        cwd=SKILLS_DIR / "vigicrues",
        error_message="Une erreur est survenue lors de l'appel à Vigicrues."
    )



def load_system_prompt() -> str:
    """Charge le prompt de l'agent depuis le fichier markdown correspondant,
    avec un fallback si le fichier est manquant ou illisible.
    """
    path = BASE_DIR / ".gemini" / "agents" / "crisis-navigator.md"
    if not path.exists():
        path = BASE_DIR / "crisis-navigator.md"

    if path.exists():
        try:
            content = path.read_text(encoding="utf-8")
            parts = content.split("---")
            if len(parts) >= 3:
                # Le prompt commence après la fin du second séparateur frontmatter
                return "---".join(parts[2:]).strip()
        except Exception:
            pass
    return """Tu es "Crisis Navigator", l'Agent d'Évacuation et de Guidage Routier en situation d'urgence.
Ton objectif est d'aider un utilisateur ou un véhicule de secours à planifier un trajet sûr en situation d'urgence, en évitant les zones à risques immédiats et les blocages routiers.
Réponds toujours en français de manière calme et opérationnelle.
"""


def run_agent(query: str) -> str:
    """Initialise et exécute le workflow de l'agent Crisis Navigator."""
    model = get_llm(temperature=0.1)
    
    tools = [self_location, proximity_search, trafic_bison_fute, vigicrues]
    system_prompt = load_system_prompt()
    
    # Création de l'agent ReAct LangGraph
    app = create_react_agent(model, tools, prompt=system_prompt)
    
    inputs = {"messages": [("user", query)]}
    result = app.invoke(inputs, config={"recursion_limit": 50})
    
    # Récupération du message final
    last_message = result["messages"][-1]
    return last_message.content


def main() -> int:
    query = sys.argv[1] if len(sys.argv) > 1 else None
    if not query:
        query = "Trouve la caserne de pompiers la plus proche de Besançon et évalue le trafic routier."
        print(f"Aucune requête fournie. Lancement du cas de test par défaut :", file=sys.stderr)
        print(f"'{query}'\n", file=sys.stderr)
        
    try:
        response = run_agent(query)
        print("--- RÉPONSE FINALE ---")
        print(response)
        return 0
    except Exception as e:
        print(f"Erreur lors de l'exécution de l'agent : {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
