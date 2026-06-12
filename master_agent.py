#!/usr/bin/env python3
"""
master_agent.py — Agent Superviseur d'Urgence coordonnant les 4 agents d'urgence.
Coordonné avec LangChain et LangGraph.
"""

import os
import sys
import warnings
from pathlib import Path

# Ignorer les avertissements de dépréciation d'importations tierces
warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", category=UserWarning)

# Importations LangChain / LangGraph
from langchain_core.tools import tool
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.prebuilt import create_react_agent

# Configuration des chemins locaux
ROOT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT_DIR))


def load_env_file():
    """Charge les variables d'environnement depuis un fichier .env local s'il existe."""
    env_path = ROOT_DIR / ".env"
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


@tool
def call_crisis_navigator(query: str) -> str:
    """Planifie un itinéraire routier sûr en situation d'urgence, recherche des points de secours
    (hôpitaux, pompiers) à proximité, et analyse l'état du trafic routier et des crues de rivières.
    Prend en paramètre la requête de guidage/évacuation de l'utilisateur.
    """
    print(f"\n[Master Agent] ➔ Appel de Crisis Navigator avec : '{query}'", file=sys.stderr)
    import crisis_navigator
    res = crisis_navigator.run_agent(query)
    print(f"[Master Agent] ✔ Retour de Crisis Navigator ({len(res)} caractères)", file=sys.stderr)
    return res


@tool
def call_geo_profiler(target_image: str) -> str:
    """Analyse visuellement et techniquement une photographie d'incident pour identifier la localisation géographique
    précise (pays, ville, rue, coordonnées GPS).
    Prend en paramètre le chemin d'accès local vers le fichier image (ex: 'worldguessr_test1.png').
    """
    print(f"\n[Master Agent] ➔ Appel de Geo Profiler avec : '{target_image}'", file=sys.stderr)
    import geo_profiler_agent
    res = geo_profiler_agent.run_agent(target_image)
    print(f"[Master Agent] ✔ Retour de Geo Profiler ({len(res)} caractères)", file=sys.stderr)
    return res


@tool
def call_risk_assessor(query: str) -> str:
    """Réalise un diagnostic complet des risques naturels et environnementaux (séismes, inondations Vigicrues,
    arrêtés de catastrophe naturelle, vigilance météo) pour une commune française.
    Prend en paramètre le nom de la commune ou une question sur la commune.
    """
    print(f"\n[Master Agent] ➔ Appel de Risk Assessor avec : '{query}'", file=sys.stderr)
    import risk_assessor
    res = risk_assessor.run_agent(query)
    print(f"[Master Agent] ✔ Retour de Risk Assessor ({len(res)} caractères)", file=sys.stderr)
    return res


@tool
def call_risk_cascade(query: str) -> str:
    """Évalue une situation d'incident en chaîne pour extraire des métriques terrain, des risques induits et 
    les consignes préfectorales officielles à respecter.
    Prend en paramètre la description textuelle de la situation d'incident (ex: 'forte pluie et montée de rivière à Besançon').
    """
    print(f"\n[Master Agent] ➔ Appel de Risk Cascade avec : '{query}'", file=sys.stderr)
    import risk_cascade
    res = risk_cascade.run_agent(query)
    print(f"[Master Agent] ✔ Retour de Risk Cascade ({len(res)} caractères)", file=sys.stderr)
    return res


def load_system_prompt() -> str:
    """Charge le prompt de l'agent maître depuis le fichier markdown correspondant,
    avec un fallback si le fichier est manquant ou illisible.
    """
    path = ROOT_DIR / ".gemini" / "agents" / "master-agent.md"
    if not path.exists():
        path = ROOT_DIR / "master-agent.md"

    if path.exists():
        try:
            content = path.read_text(encoding="utf-8")
            parts = content.split("---")
            if len(parts) >= 3:
                # Le prompt commence après la fin du second séparateur frontmatter
                return "---".join(parts[2:]).strip()
        except Exception:
            pass
    return """Tu es le "Master Agent" (Superviseur de Crise), l'ordonnateur principal en situation de crise ou de catastrophe naturelle.
Ton but est de coordonner l'action des sous-agents d'urgence spécialisés pour fournir à l'utilisateur des informations de sécurité critiques, fiables et unifiées.
Réponds toujours en français de manière calme et opérationnelle.
"""


def run_agent(query: str) -> str:
    """Initialise et exécute le workflow de l'agent maître."""
    model_name = os.environ.get("GEMINI_MODEL", "gemini-1.5-flash")
    model = ChatGoogleGenerativeAI(
        model=model_name,
        temperature=0.1
    )
    
    tools = [call_crisis_navigator, call_geo_profiler, call_risk_assessor, call_risk_cascade]
    system_prompt = load_system_prompt()
    
    # Création de l'agent ReAct LangGraph
    app = create_react_agent(model, tools, prompt=system_prompt)
    
    inputs = {"messages": [("user", query)]}
    result = app.invoke(inputs, config={"recursion_limit": 50})
    
    # Récupération du message final
    last_message = result["messages"][-1]
    return last_message.content


def main() -> int:
    import argparse
    parser = argparse.ArgumentParser(description="Master Agent — Superviseur d'Urgence Multi-Agents")
    parser.add_argument("query", type=str, nargs="?", help="Requête globale de l'utilisateur ou situation d'incident")
    args = parser.parse_args()
    
    if not args.query:
        print("Erreur : Veuillez spécifier une requête.", file=sys.stderr)
        print("Usage : python3 master_agent.py \"<requête>\"", file=sys.stderr)
        return 1
        
    try:
        response = run_agent(args.query)
        print(response)
        return 0
    except Exception as e:
        print(f"Erreur lors de l'exécution de l'agent maître : {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
