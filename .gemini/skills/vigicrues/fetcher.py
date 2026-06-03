"""
fetcher.py — interroge l'API HubEau Hydrométrie v2 (Service Central Vigicrues).

Endpoints utilisés (sans clé API, Licence Ouverte v2.0) :
  Stations proches  : GET /api/v2/hydrometrie/referentiel/stations
  Observations H    : GET /api/v2/hydrometrie/observations_tr  (grandeur_hydro=H)
  Observations Q    : GET /api/v2/hydrometrie/observations_tr  (grandeur_hydro=Q)

L'API HubEau remplace l'ancienne API Vigicrues v1.1 (désactivée).
Elle intègre un filtre géospatial natif (latitude/longitude/distance),
ce qui supprime le besoin de cache local et de calcul haversine côté client.

Unités retournées par l'API :
  resultat_obs pour H (hauteur) : millimètres  → diviser par 1000 pour obtenir des mètres
  resultat_obs pour Q (débit)   : litres/s     → diviser par 1000 pour obtenir des m³/s
"""

import json

import requests

BASE_URL = "https://hubeau.eaufrance.fr/api/v2/hydrometrie"
TIMEOUT = 15  # secondes


def fetch_stations_nearby(lat: float, lon: float, radius_km: int, max_results: int) -> dict:
    """
    Retourne les stations hydrométriques dans le rayon autour du point GPS.

    Le filtre géospatial est délégué à l'API — pas de haversine côté client.

    Structure retournée :
    {
        "stations": [
            {
                "code_station": "F449000601",
                "nom": "La Seine à Corbeil-Essonnes",
                "cours_eau": "La Seine",
                "lat": 48.613738123,
                "lon": 2.484841533,
                "commune": "CORBEIL-ESSONNES",
                "departement": "91"
            },
            ...
        ],
        "nb_stations": 5
    }

    Lève RuntimeError si l'API est injoignable ou renvoie une erreur.
    """
    params = {
        "latitude": lat,
        "longitude": lon,
        "distance": radius_km,
        "size": max_results,
        "format": "json",
        "fields": (
            "code_station,libelle_station,libelle_cours_eau,"
            "latitude_station,longitude_station,"
            "libelle_commune,code_departement"
        ),
    }
    try:
        resp = requests.get(f"{BASE_URL}/referentiel/stations", params=params, timeout=TIMEOUT)
        resp.raise_for_status()
        data = resp.json()
    except requests.RequestException as e:
        raise RuntimeError(f"Impossible de joindre HubEau (stations) : {e}") from e
    except json.JSONDecodeError as e:
        raise RuntimeError(f"Réponse non-JSON de HubEau (stations) : {e}") from e

    raw_list = data.get("data", [])
    if not raw_list:
        return {"stations": [], "nb_stations": 0}

    stations = [
        {
            "code_station": s.get("code_station", ""),
            "nom": s.get("libelle_station", ""),
            "cours_eau": s.get("libelle_cours_eau", ""),
            "lat": s.get("latitude_station"),
            "lon": s.get("longitude_station"),
            "commune": s.get("libelle_commune", ""),
            "departement": s.get("code_departement", ""),
        }
        for s in raw_list
        if s.get("code_station")
    ]

    return {"stations": stations, "nb_stations": len(stations)}


def fetch_latest_observation(code_station: str) -> dict:
    """
    Récupère la dernière hauteur d'eau (H) et le dernier débit (Q) d'une station.

    resultat_obs H est en mm  → converti en mètres.
    resultat_obs Q est en l/s → converti en m³/s.

    Retourne :
    {
        "hauteur_m": 1.743,
        "debit_m3s": 0.312,
        "date_obs": "2026-05-20T22:00:00Z",
        "disponible": true
    }
    """
    hauteur = _fetch_obs(code_station, "H")
    debit = _fetch_obs(code_station, "Q")

    if not hauteur["disponible"] and not debit["disponible"]:
        return {"disponible": False, "hauteur_m": None, "debit_m3s": None, "date_obs": None}

    date_obs = hauteur.get("date_obs") or debit.get("date_obs")

    hauteur_m = None
    if hauteur["disponible"] and hauteur["valeur_brute"] is not None:
        hauteur_m = round(hauteur["valeur_brute"] / 1000, 3)  # mm → m

    debit_m3s = None
    if debit["disponible"] and debit["valeur_brute"] is not None:
        debit_m3s = round(debit["valeur_brute"] / 1000, 3)  # l/s → m³/s

    return {
        "disponible": True,
        "hauteur_m": hauteur_m,
        "debit_m3s": debit_m3s,
        "date_obs": date_obs,
    }


def _fetch_obs(code_station: str, grandeur: str) -> dict:
    """Appel interne : dernière observation d'une grandeur (H ou Q) pour une station."""
    params = {
        "code_entite": code_station,
        "grandeur_hydro": grandeur,
        "size": 1,
        "format": "json",
        "fields": "date_obs,resultat_obs",
    }
    try:
        resp = requests.get(
            f"{BASE_URL}/observations_tr", params=params, timeout=TIMEOUT
        )
        resp.raise_for_status()
        data = resp.json()
        obs_list = data.get("data", [])
        if not obs_list:
            return {"disponible": False, "valeur_brute": None, "date_obs": None}
        latest = obs_list[0]
        return {
            "disponible": True,
            "valeur_brute": latest.get("resultat_obs"),
            "date_obs": latest.get("date_obs"),
        }
    except (requests.RequestException, json.JSONDecodeError, KeyError):
        return {"disponible": False, "valeur_brute": None, "date_obs": None}
