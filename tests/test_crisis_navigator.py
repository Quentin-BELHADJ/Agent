import sys
from unittest import mock
from pathlib import Path

# Ajout du dossier racine et du dossier agents au PYTHONPATH
ROOT_DIR = Path(__file__).resolve().parents[1]
AGENTS_DIR = ROOT_DIR / ".gemini" / "agents"
sys.path.insert(0, str(AGENTS_DIR))

import crisis_navigator  # noqa: E402



def test_load_system_prompt():
    # Test avec fichier inexistant (fallback)
    with mock.patch("pathlib.Path.exists", return_value=False):
        prompt = crisis_navigator.load_system_prompt()
        assert "Crisis Navigator" in prompt
        assert "français" in prompt

    # Test avec le vrai fichier markdown
    prompt = crisis_navigator.load_system_prompt()
    assert "Crisis Navigator" in prompt
    assert "Rôle et Identité" in prompt


@mock.patch("subprocess.run")
def test_self_location_tool(mock_run):
    mock_run.return_value = mock.Mock(
        returncode=0,
        stdout='{"ville": "Paris", "latitude": 48.85, "longitude": 2.35}',
        stderr=""
    )
    
    # Invocation via l'outil LangChain
    res = crisis_navigator.self_location.invoke({})
    assert "Paris" in res
    mock_run.assert_called_once()


@mock.patch("subprocess.run")
def test_proximity_search_tool(mock_run):
    mock_run.return_value = mock.Mock(
        returncode=0,
        stdout='{"status": "success", "resultats": []}',
        stderr=""
    )
    res = crisis_navigator.proximity_search.invoke({
        "tag_key": "amenity",
        "tag_value": "hospital",
        "location_hint": "Besançon"
    })
    assert "success" in res
    
    args = mock_run.call_args[0][0]
    assert "find_nearby.py" in args[1]
    assert "amenity" in args
    assert "hospital" in args
    assert "Besançon" in args


@mock.patch("subprocess.run")
def test_trafic_bison_fute_tool(mock_run):
    mock_run.return_value = mock.Mock(
        returncode=0,
        stdout='{"status": "success", "alertes": []}',
        stderr=""
    )
    res = crisis_navigator.trafic_bison_fute.invoke({
        "type_info": "bouchons",
        "location_or_route": "A6"
    })
    assert "success" in res
    
    args = mock_run.call_args[0][0]
    assert "trafic.py" in args[1]
    assert "bouchons" in args
    assert "A6" in args


@mock.patch("subprocess.run")
def test_vigicrues_tool(mock_run):
    mock_run.return_value = mock.Mock(
        returncode=0,
        stdout='{"status": "ok", "stations": []}',
        stderr=""
    )
    res = crisis_navigator.vigicrues.invoke({
        "lat": 48.85,
        "lon": 2.35,
        "radius": 15.0,
        "max_results": 3
    })
    assert "ok" in res
    
    args = mock_run.call_args[0][0]
    assert "main.py" in args[1]
    assert "--lat" in args
    assert "48.85" in args
    assert "--lon" in args
    assert "2.35" in args
    assert "--radius" in args
    assert "15.0" in args
    assert "--max" in args
    assert "3" in args


@mock.patch("crisis_navigator.create_react_agent")
@mock.patch("crisis_navigator.ChatGoogleGenerativeAI")
def test_run_agent(mock_chat, mock_create_agent):
    mock_app = mock.Mock()
    mock_app.invoke.return_value = {
        "messages": [
            mock.Mock(content="User query"),
            mock.Mock(content="🚨 **ÉVALUATION DE LA SITUATION :** Évacuation initiée.")
        ]
    }
    mock_create_agent.return_value = mock_app
    
    response = crisis_navigator.run_agent("Je dois évacuer d'urgence vers l'hôpital le plus proche.")
    assert "🚨 **ÉVALUATION DE LA SITUATION :** Évacuation initiée." in response
    mock_create_agent.assert_called_once()
    mock_app.invoke.assert_called_once()
