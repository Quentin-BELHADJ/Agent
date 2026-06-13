import os
from dotenv import load_dotenv
from pathlib import Path
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI

# Charge le fichier .env
ROOT_DIR = Path(__file__).resolve().parent
env_path = ROOT_DIR / ".env"
load_dotenv(dotenv_path=env_path)

def get_llm(temperature=0.1):
    """
    Retourne l'instance de LLM configurée de manière agnostique.
    Supporte 'google', 'openai', ou 'ollama' via LLM_PROVIDER.
    """
    provider = os.environ.get("LLM_PROVIDER", "google").lower()
    model_name = os.environ.get("LLM_MODEL", "gemini-3.5-flash")
    api_key = os.environ.get("LLM_API_KEY")
    api_base = os.environ.get("LLM_API_BASE")
    
    if provider in ("openai", "ollama"):
        return ChatOpenAI(
            model_name=model_name,
            openai_api_key=api_key or "ollama",
            openai_api_base=api_base,
            temperature=temperature
        )
    else:
        # Par défaut : Google Gemini
        return ChatGoogleGenerativeAI(
            model=model_name,
            google_api_key=api_key,
            temperature=temperature
        )
