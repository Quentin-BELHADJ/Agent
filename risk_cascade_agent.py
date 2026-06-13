import json
import sys
import os
from pathlib import Path

# Récupère le répertoire de base de manière dynamique
BASE_DIR = Path(__file__).resolve().parent


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

from langchain_core.tools import tool
from langchain_core.documents import Document
from langchain_core.vectorstores import InMemoryVectorStore
from langgraph.prebuilt import create_react_agent

# Imports internes stricts
try:
    from llm import get_llm
    
    def get_embeddings():
        """
        Retourne le modèle d'embeddings configuré de manière agnostique.
        Supporte 'google', 'openai', ou 'ollama' via LLM_PROVIDER.
        """
        import os
        from langchain_google_genai import GoogleGenerativeAIEmbeddings
        from langchain_openai import OpenAIEmbeddings
        
        provider = os.environ.get("LLM_PROVIDER", "google").lower()
        embedding_model = os.environ.get("LLM_EMBEDDING_MODEL", "text-embedding-004")
        api_key = os.environ.get("LLM_API_KEY")
        api_base = os.environ.get("LLM_API_BASE")
        
        if provider in ("openai", "ollama"):
            return OpenAIEmbeddings(
                model=embedding_model,
                openai_api_key=api_key or "ollama",
                openai_api_base=api_base
            )
        else:
            return GoogleGenerativeAIEmbeddings(
                model=embedding_model,
                google_api_key=api_key
            )
except ImportError:
    print("Attention: helpers de la racine non trouvés. Utilisation de mocks pour LLM et Embeddings.", file=sys.stderr)
    from langchain_core.language_models.chat_models import SimpleChatModel
    from langchain_core.embeddings.fake import FakeEmbeddings
    
    class FakeChatModel(SimpleChatModel):
        def _call(self, messages, stop=None, run_manager=None, **kwargs):
            return "Voici la réponse mockée de l'Analyste des Risques Cascades suite à l'incident."
            
        @property
        def _llm_type(self) -> str:
            return "fake-chat-model"
            
        def bind_tools(self, tools, **kwargs):
            # Les agents de langgraph appellent bind_tools sur le modèle.
            # Nous renvoyons simplement self pour le mock.
            return self

    def get_llm(temperature=0):
        return FakeChatModel()
        
    def get_embeddings():
        return FakeEmbeddings(size=1536)

# --- 1. Outils Métier (Skills) ---

@tool
def get_insee_code(nom_commune: str) -> str:
    """Retourne le code INSEE d'une commune à partir de son nom."""
    # Mock pour les tests
    return json.dumps({"nom": nom_commune, "code_insee": "25056"})

@tool
def vigicrues(code_insee: str) -> str:
    """Retourne les hauteurs d'eau et niveaux d'alerte pour un code INSEE."""
    # Mock pour les tests
    return json.dumps({"code_insee": code_insee, "niveau_alerte": "Rouge", "hauteur_eau": "7.5m", "tendance": "en forte hausse"})

@tool
def get_seismic_risks(code_insee: str) -> str:
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

vector_store = None
vector_store_error = False

def get_vector_store():
    global vector_store, vector_store_error
    if vector_store is None and not vector_store_error:
        try:
            vector_store = InMemoryVectorStore.from_documents(_documents, get_embeddings())
        except Exception:
            vector_store_error = True
    return vector_store

@tool
def search_procedures(requete: str) -> str:
    """Effectue une recherche de similarité pour obtenir les consignes et procédures préfectorales."""
    vs = get_vector_store()
    if vs is not None:
        try:
            resultats = vs.similarity_search(requete, k=1)
            if resultats:
                return "\n\n".join([doc.page_content for doc in resultats])
        except Exception:
            pass
            
    # Recherche textuelle de secours par correspondance de mots-clés
    best_doc = None
    best_score = -1
    requete_words = set(requete.lower().split())
    for doc in _documents:
        doc_words = set(doc.page_content.lower().split())
        intersection = len(requete_words.intersection(doc_words))
        if intersection > best_score:
            best_score = intersection
            best_doc = doc
            
    if best_doc and best_score > 0:
        return best_doc.page_content
    return "Aucune procédure correspondante trouvée."


# --- 3. Configuration de l'Agent ---

# Liste des outils à fournir à l'agent
tools = [get_insee_code, vigicrues, get_seismic_risks, search_procedures]

def load_system_prompt() -> str:
    """Charge le prompt de l'agent depuis le fichier markdown correspondant,
    avec un fallback si le fichier est manquant ou illisible.
    """
    path = BASE_DIR / ".gemini" / "agents" / "risk-cascade.md"
    if not path.exists():
        path = BASE_DIR / "risk-cascade.md"

    if path.exists():
        try:
            content = path.read_text(encoding="utf-8")
            parts = content.split("---")
            if len(parts) >= 3:
                # Le prompt commence après la fin du second séparateur frontmatter
                return "---".join(parts[2:]).strip()
        except Exception:
            pass
    return """Tu es un Analyste des Risques Cascades. Pour toute requête : 
1) Obtiens le code INSEE via `get_insee_code`. 
2) Évalue la situation via `vigicrues` et `get_seismic_risks`. 
3) SI un danger est détecté, tu DOIS appeler `search_procedures` pour obtenir les consignes préfectorales exactes. Ne génère pas de consignes toi-même. 
Formate ta réponse finale avec les métriques terrain, les risques induits, et les directives officielles."""

# Instanciation différée pour éviter les appels API au chargement du module
agent = None

def get_agent():
    global agent
    if agent is None:
        agent = create_react_agent(
            model=get_llm(temperature=0),
            tools=tools,
            prompt=load_system_prompt()
        )
    return agent


# --- 4. Exécution ---

def run_agent(incident: str) -> str:
    """Lance l'agent avec l'incident donné et retourne la réponse finale."""
    current_agent = get_agent()
    resultat = current_agent.invoke({"messages": [("user", incident)]}, config={"recursion_limit": 50})
    return resultat["messages"][-1].content

def main() -> int:
    incident = sys.argv[1] if len(sys.argv) > 1 else None
    if not incident:
        incident = "Il pleut énormément sur Besançon depuis 3 jours, la rivière monte."
        print(f"Aucune description d'incident fournie. Lancement du cas de test par défaut :", file=sys.stderr)
        print(f"'{incident}'\n", file=sys.stderr)
        
    try:
        reponse = run_agent(incident)
        print("--- RÉPONSE FINALE ---")
        print(reponse)
        return 0
    except Exception as e:
        print(f"Erreur lors de l'exécution de l'agent : {e}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())
