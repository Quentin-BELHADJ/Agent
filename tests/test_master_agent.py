import sys
from unittest import mock
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

import master_agent  # noqa: E402


def test_load_system_prompt():
    # Test avec fichier inexistant (fallback)
    with mock.patch("pathlib.Path.exists", return_value=False):
        prompt = master_agent.load_system_prompt()
        assert "Master Agent" in prompt
        assert "français" in prompt

    # Test avec le vrai fichier markdown
    prompt = master_agent.load_system_prompt()
    assert "Master Agent" in prompt
    assert "Rôle et Identité" in prompt


@mock.patch("crisis_navigator.run_agent")
def test_call_crisis_navigator(mock_run):
    mock_run.return_value = "Itinéraire sécurisé"
    res = master_agent.call_crisis_navigator.invoke({"query": "Besançon"})
    assert res == "Itinéraire sécurisé"
    mock_run.assert_called_once_with("Besançon")


@mock.patch("geo_profiler_agent.run_agent")
def test_call_geo_profiler(mock_run):
    mock_run.return_value = "Localisation déterminée"
    res = master_agent.call_geo_profiler.invoke({"target_image": "image.png"})
    assert res == "Localisation déterminée"
    mock_run.assert_called_once_with("image.png")


@mock.patch("risk_assessor.run_agent")
def test_call_risk_assessor(mock_run):
    mock_run.return_value = "Diagnostic de risques"
    res = master_agent.call_risk_assessor.invoke({"query": "Besançon"})
    assert res == "Diagnostic de risques"
    mock_run.assert_called_once_with("Besançon")


@mock.patch("risk_cascade.run_agent")
def test_call_risk_cascade(mock_run):
    mock_run.return_value = "Analyse en cascade"
    res = master_agent.call_risk_cascade.invoke({"query": "Besançon"})
    assert res == "Analyse en cascade"
    mock_run.assert_called_once_with("Besançon")


@mock.patch("master_agent.create_react_agent")
@mock.patch("master_agent.ChatGoogleGenerativeAI")
def test_run_agent(mock_chat, mock_create_agent):
    mock_app = mock.Mock()
    mock_app.invoke.return_value = {
        "messages": [
            mock.Mock(content="User query"),
            mock.Mock(content="🚨 **SYNTHÈSE DE LA SITUATION** : Incident sous contrôle.")
        ]
    }
    mock_create_agent.return_value = mock_app
    
    response = master_agent.run_agent("Inondation à Besançon, besoin d'aide")
    assert "🚨 **SYNTHÈSE DE LA SITUATION** : Incident sous contrôle." in response
    mock_create_agent.assert_called_once()
    mock_app.invoke.assert_called_once()
