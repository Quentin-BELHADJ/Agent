"""
stations.py — Sélection des stations de mesure les plus proches d'un point GPS

Utilise la formule haversine (stdlib math uniquement, pas de geopy/shapely).
"""

import math
import sys
from typing import Optional


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Distance en kilomètres entre deux points GPS (WGS84).
    Formule haversine — précision suffisante pour <1 000 km.
    """
    R = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))


def find_nearest_stations(
    stations: dict,
    lat: float,
    lon: float,
    radius_km: float = 30.0,
    max_stations: int = 5,
    required_pollutants: Optional[list] = None,
) -> list:
    """
    Retourne les stations dans le rayon donné, triées par distance croissante.

    Paramètres :
        stations          : dict station_id -> données (issu de fetcher.get_measures)
        lat, lon          : coordonnées GPS de l'incident
        radius_km         : rayon de recherche en km (défaut 30)
        max_stations      : nombre maximum de stations à retourner (défaut 5)
        required_pollutants : si fourni, inclure uniquement les stations mesurant
                              au moins UN de ces polluants

    Retourne :
        liste de dicts { station_id, nom, commune, departement,
                         latitude, longitude, distance_km, mesures }
    """
    if not (-90 <= lat <= 90 and -180 <= lon <= 180):
        raise ValueError(f"Coordonnées GPS invalides : lat={lat}, lon={lon}")

    results = []

    for sid, s in stations.items():
        slat = s.get("latitude")
        slon = s.get("longitude")

        if slat is None or slon is None:
            continue  # station sans coordonnées GPS — ignorer

        try:
            dist = haversine_km(lat, lon, slat, slon)
        except Exception as e:
            print(f"[stations] Erreur calcul distance pour {sid} : {e}", file=sys.stderr)
            continue

        if dist > radius_km:
            continue

        mesures = s.get("mesures", {})

        # Filtre polluants si demandé
        if required_pollutants:
            mesures_filtrees = {p: v for p, v in mesures.items() if p in required_pollutants}
            if not mesures_filtrees:
                continue  # station ne mesure aucun polluant pertinent
        else:
            mesures_filtrees = mesures

        results.append({
            "station_id":  sid,
            "nom":         s.get("nom", sid),
            "commune":     s.get("commune", ""),
            "departement": s.get("departement", ""),
            "latitude":    slat,
            "longitude":   slon,
            "distance_km": round(dist, 2),
            "mesures":     mesures_filtrees,
        })

    # Tri par distance croissante, limité à max_stations
    results.sort(key=lambda x: x["distance_km"])
    return results[:max_stations]
