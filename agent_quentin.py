import json
import sys

from langchain_core.tools import tool
from langchain_core.documents import Document
from langchain_core.vectorstores import InMemoryVectorStore
from langgraph.prebuilt import create_react_agent

# Imports internes stricts
try:
    from _lib.llm import get_llm
    from _lib.embeddings import get_embeddings
except ImportError:
    print("Attention: _lib non trouvé. Utilisation de mocks pour LLM et Embeddings.", file=sys.stderr)
    from langchain_core.language_models.fake import FakeListLLM
    from langchain_core.embeddings.fake import FakeEmbeddings
    def get_llm(temperature=0):
        # Fake responses that mimic the tool calling loop
        return FakeListLLM(responses=[
            "Voici la réponse mockée de l'Analyste des Risques Cascades suite à l'incident."
        ])
    def get_embeddings():
        return FakeEmbeddings(size=1536)

# --- 1. Outils Métier (Skills) ---

@tool
def geo(nom_commune: str) -> str:
    """Retourne le code INSEE d'une commune à partir de son nom."""
    # Mock pour les tests
    return json.dumps({"nom": nom_commune, "code_insee": "25056"})

@tool
def vigicrues(code_insee: str) -> str:
    """Retourne les hauteurs d'eau et niveaux d'alerte pour un code INSEE."""
    # Mock pour les tests
    return json.dumps({"code_insee": code_insee, "niveau_alerte": "Rouge", "hauteur_eau": "7.5m", "tendance": "en forte hausse"})

@tool
def risques(code_insee: str) -> str:
    """Retourne le niveau de risque sismique pour un code INSEE."""
    # Mock pour les tests
    return json.dumps({"code_insee": code_insee, "risque_sismique": "Moyen (Niveau 3)"})


# --- 2. Outil RAG (Retriever) ---

# Création et peuplement de la base vectorielle en mémoire
_documents = [
    Document(
        page_content="Procédure d'évacuation inondation zone rouge : 1. Évacuer immédiatement les zones inondables proches des cours d'eau. 2. Couper l'électricité et le gaz. 3. Rejoindre les points de rassemblement situés sur les hauteurs (hors de portée des eaux).",
        metadata={"source": "directive_inondation"}
    ),
    Document(
        page_content="Mise à l'abri séisme : 1. S'abriter sous un meuble solide (table, bureau). 2. S'éloigner des fenêtres et des objets susceptibles de tomber. 3. Ne pas sortir des bâtiments pendant les secousses. 4. Couper le gaz.",
        metadata={"source": "directive_seisme"}
    ),
    Document(
        page_content="Alerte tempête majeure : 1. Rester à l'intérieur. 2. Fermer toutes les portes, fenêtres et volets. 3. Limiter tous les déplacements non essentiels. 4. Prévoir des réserves d'eau et de nourriture.",
        metadata={"source": "directive_tempete"}
    )
]

vector_store = InMemoryVectorStore.from_documents(_documents, get_embeddings())

@tool
def rechercher_procedures(requete: str) -> str:
    """Effectue une recherche de similarité pour obtenir les consignes et procédures préfectorales."""
    resultats = vector_store.similarity_search(requete, k=1)
    if not resultats:
        return "Aucune procédure correspondante trouvée."
    return "\n\n".join([doc.page_content for doc in resultats])


# --- 3. Configuration de l'Agent ---

# Liste des outils à fournir à l'agent
tools = [geo, vigicrues, risques, rechercher_procedures]

# Prompt système
system_prompt = """Tu es un Analyste des Risques Cascades. Pour toute requête : 
1) Obtiens le code INSEE via `geo`. 
2) Évalue la situation via `vigicrues` et `risques`. 
3) SI un danger est détecté, tu DOIS appeler `rechercher_procedures` pour obtenir les consignes préfectorales exactes. Ne génère pas de consignes toi-même. 
Formate ta réponse finale avec les métriques terrain, les risques induits, et les directives officielles."""

# Instanciation de l'agent (on renomme l'alias si nécessaire, ici create_react_agent correspond à create_agent dans LangGraph)
agent = create_react_agent(
    model=get_llm(temperature=0),
    tools=tools,
    state_modifier=system_prompt
)


# --- 4. Exécution ---

def run_agent(incident: str) -> str:
    """Lance l'agent avec l'incident donné et retourne la réponse finale."""
    resultat = agent.invoke({"messages": [("user", incident)]})
    return resultat["messages"][-1].content

if __name__ == "__main__":
    incident_test = "Il pleut énormément sur Besançon depuis 3 jours, la rivière monte."
    print(f"[{incident_test}]")
    print("Lancement de l'agent...\n")
    try:
        reponse = run_agent(incident_test)
        print("--- RÉPONSE FINALE ---")
        print(reponse)
    except Exception as e:
        print(f"Erreur lors de l'exécution de l'agent : {e}", file=sys.stderr)
