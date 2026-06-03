#!/usr/bin/env python3
"""
main.py — Point d'entrée CLI du skill vigicrues.

Usage :
    python3 main.py incident --lat <LAT> --lon <LON> [--radius <KM>] [--max <N>]

Toute la sortie utile va sur stdout en JSON pur.
Les messages d'erreur vont sur stderr.
Exit codes : 0=succès avec données, 1=erreur, 2=aucune station trouvée.
"""

import argparse
import json
import sys
from pathlib import Path

SKILL_DIR = Path(__file__).parent
sys.path.insert(0, str(SKILL_DIR))

from fetcher import fetch_latest_observation, fetch_stations_nearby


def cmd_incident(args: argparse.Namespace) -> int:
    lat, lon = args.lat, args.lon
    radius_km = args.radius
    max_results = args.max

    # 1. Stations proches via HubEau (filtre géospatial côté API)
    try:
        station_data = fetch_stations_nearby(lat, lon, radius_km, max_results)
    except RuntimeError as e:
        print(json.dumps({"status": "error", "message": str(e)}, ensure_ascii=False))
        return 1

    stations = station_data["stations"]

    if not stations:
        result = {
            "status": "no_stations",
            "message": (
                f"Aucune station hydrométrique trouvée dans un rayon de {radius_km} km "
                f"autour de ({lat}, {lon}). "
                "Essayez d'augmenter le rayon avec --radius."
            ),
            "lat": lat,
            "lon": lon,
            "radius_km": radius_km,
        }
        print(json.dumps(result, ensure_ascii=False))
        return 2

    # 2. Observations temps réel pour chaque station
    stations_enriched = []
    for sta in stations:
        obs = fetch_latest_observation(sta["code_station"])
        stations_enriched.append({
            "code_station": sta["code_station"],
            "nom": sta["nom"],
            "cours_eau": sta["cours_eau"],
            "commune": sta["commune"],
            "departement": sta["departement"],
            "lat": sta["lat"],
            "lon": sta["lon"],
            "observation": obs,
        })

    # 3. Hauteur max parmi les stations (indicateur synthétique)
    hauteurs = [
        s["observation"]["hauteur_m"]
        for s in stations_enriched
        if s["observation"]["hauteur_m"] is not None
    ]
    hauteur_max_m = max(hauteurs) if hauteurs else None

    result = {
        "status": "ok",
        "lat": lat,
        "lon": lon,
        "radius_km": radius_km,
        "nb_stations_trouvees": len(stations_enriched),
        "hauteur_max_m": hauteur_max_m,
        "note": (
            "La hauteur est relative au zéro de chaque station (non comparable entre stations). "
            "Consulter vigicrues.gouv.fr pour le niveau de vigilance officiel."
        ),
        "stations": stations_enriched,
    }

    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Skill Vigicrues — hauteurs d'eau en situation d'urgence (via HubEau)"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    p_incident = subparsers.add_parser(
        "incident",
        help="Interroge les stations hydrométriques autour d'un point GPS",
    )
    p_incident.add_argument("--lat", type=float, required=True,
                            help="Latitude WGS84 (ex: 48.85)")
    p_incident.add_argument("--lon", type=float, required=True,
                            help="Longitude WGS84 (ex: 2.35)")
    p_incident.add_argument("--radius", type=float, default=30.0,
                            help="Rayon de recherche en km (défaut: 30)")
    p_incident.add_argument("--max", type=int, default=5,
                            help="Nombre max de stations (défaut: 5)")

    args = parser.parse_args()

    if args.command == "incident":
        return cmd_incident(args)

    print(json.dumps({"status": "error", "message": "Commande inconnue"}), file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
