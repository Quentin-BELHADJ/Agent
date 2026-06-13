#!/usr/bin/env python3
"""
risk_assessor.py — Implémentation de l'Agent d'Évaluation Environnementale de Zone (Risk Assessor).
Coordonné avec LangChain et LangGraph.

Produit un rapport de vulnérabilité et de risques naturels (sismique, inondation,
alertes/arrêtés) pour une commune française, en orchestrant les compétences locales
du projet (geo, risques, vigicrues) et une recherche web.
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
def geo_insee_code(nom_commune: str) -> str:
    """Récupère le code INSEE officiel d'une commune française à partir de son nom.
    Étape indispensable avant d'interroger les bases de données de risques (sismique, etc.).

    Args:
        nom_commune: le nom de la commune (ex: 'Besançon', 'Belfort').
    """
    script_path = SKILLS_DIR / "geo" / "commune.py"
    return run_skill(
        [sys.executable, str(script_path), nom_commune],
        error_message="Une erreur est survenue lors de la récupération du code INSEE."
    )


@tool
def seismic_risks(code_insee: str) -> str:
    """Détermine le niveau de risque (aléa) sismique officiel d'une commune française.
    Nécessite le code INSEE de la commune, et non son nom.

    Args:
        code_insee: le code INSEE de la commune (obtenu via `geo_insee_code`).
    """
    script_path = SKILLS_DIR / "risques" / "sismique.py"
    return run_skill(
        [sys.executable, str(script_path), code_insee],
        error_message="Une erreur est survenue lors de l'évaluation sismique."
    )


@tool
def vigicrues(lat: float, lon: float, radius: Optional[float] = 30.0, max_results: Optional[int] = 5) -> str:
    """Interroge les stations hydrométriques (hauteurs d'eau et débits des rivières) autour
    d'un point GPS pour évaluer les risques d'inondation/crue.

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


@tool
def web_search(query: str) -> str:
    """Recherche sur le web les dernières informations officielles concernant une commune :
    arrêtés de 'Catastrophe Naturelle', vigilances météo (orange/rouge) en cours, etc.

    Args:
        query: la requête de recherche (ex: 'arrêté catastrophe naturelle Besançon 2026').
    """
    script_path = SKILLS_DIR / "geoint-search" / "search_web.py"
    return run_skill(
        [sys.executable, str(script_path), query],
        error_message="Une erreur est survenue lors de la recherche web."
    )


def load_system_prompt() -> str:
    """Charge le prompt de l'agent depuis le fichier markdown correspondant,
    avec un fallback si le fichier est manquant ou illisible.
    """
    path = BASE_DIR / ".gemini" / "agents" / "risk-assessor.md"
    if not path.exists():
        path = BASE_DIR / "risk-assessor.md"

    if path.exists():
        try:
            content = path.read_text(encoding="utf-8")
            parts = content.split("---")
            if len(parts) >= 3:
                # Le prompt commence après la fin du second séparateur frontmatter
                return "---".join(parts[2:]).strip()
        except Exception:
            pass
    return """Tu es "Risk Assessor", un expert en évaluation des risques environnementaux et
naturels en France. Ton rôle est de fournir un diagnostic rapide et précis de la vulnérabilité
d'une commune face à des événements majeurs (tempêtes, séismes, inondations).

Méthodologie : 1) Obtiens le code INSEE via `geo_insee_code`. 2) Évalue le risque sismique via
`seismic_risks` avec ce code INSEE. 3) Vérifie l'état hydrologique via `vigicrues`. 4) Recherche
les derniers arrêtés et alertes via `web_search`.

Structure ton rapport : Identification (commune, département, INSEE), Risque Sismique, Risque
Inondation (Vigicrues), Alertes et Arrêtés (Web), Synthèse de Vulnérabilité.
Réponds toujours en français de manière calme et opérationnelle.
"""


def run_agent(query: str) -> str:
    """Initialise et exécute le workflow de l'agent Risk Assessor."""
    model = get_llm(temperature=0.1)

    tools = [geo_insee_code, seismic_risks, vigicrues, web_search]
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
        query = "Besançon"
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
