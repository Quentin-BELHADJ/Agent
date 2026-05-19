#!/usr/bin/env python3
"""
main.py — Point d'entrée CLI du skill air-quality

Usage :
    python3 main.py incident --lat 47.24 --lon 5.98 --type incendie_industriel
    python3 main.py incident --lat 48.85 --lon 2.35 --type incendie_foret --radius 50
    python3 main.py refresh-cache

Exit codes :
    0 — succès avec données
    1 — erreur (réseau, arguments invalides, cache corrompu)
    2 — aucune station trouvée dans le rayon spécifié
"""

import argparse
import json
import sys
from datetime import datetime, timezone

from fetcher import get_measures, refresh_cache
from pollutants import (
    enrich_measure_with_thresholds,
    get_pollutants_for_incident,
    get_unavailable_pollutants,
    INCIDENT_POLLUTANTS,
    AVAILABLE_IN_LCSQA,
)
from stations import find_nearest_stations


def cmd_incident(args: argparse.Namespace) -> int:
    """Commande principale : analyse qualité de l'air autour d'un incident."""

    # Validation des coordonnées
    if not (-90 <= args.lat <= 90):
        print(f"[main] Latitude invalide : {args.lat}", file=sys.stderr)
        return 1
    if not (-180 <= args.lon <= 180):
        print(f"[main] Longitude invalide : {args.lon}", file=sys.stderr)
        return 1
    if args.radius <= 0 or args.radius > 500:
        print(f"[main] Rayon invalide : {args.radius} km (doit être entre 1 et 500)", file=sys.stderr)
        return 1

    # Chargement des données (cache ou téléchargement)
    try:
        data = get_measures()
    except RuntimeError as e:
        print(f"[main] Erreur données : {e}", file=sys.stderr)
        return 1

    # Polluants à surveiller pour ce type d'incident
    polluants_cibles = get_pollutants_for_incident(args.type)
    # On filtre sur les polluants disponibles dans LCSQA
    polluants_lcsqa = [p for p in polluants_cibles if p in AVAILABLE_IN_LCSQA]
    polluants_indispos = get_unavailable_pollutants(args.type)

    # Sélection des stations proches
    stations_proches = find_nearest_stations(
        stations=data.get("stations", {}),
        lat=args.lat,
        lon=args.lon,
        radius_km=args.radius,
        max_stations=args.max_stations,
        required_pollutants=polluants_lcsqa if polluants_lcsqa else None,
    )

    if not stations_proches:
        result = {
            "incident": {
                "lat": args.lat,
                "lon": args.lon,
                "type": args.type,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
            "stations": [],
            "alerte_globale": False,
            "polluants_en_depassement": [],
            "polluants_non_disponibles_lcsqa": polluants_indispos,
            "message": (
                f"Aucune station trouvée dans un rayon de {args.radius} km. "
                "Augmentez le rayon avec --radius ou vérifiez les coordonnées."
            ),
            "source": "LCSQA / data.gouv.fr",
            "cache_age_minutes": data.get("cache_age_minutes", 0),
            "from_cache": data.get("from_cache", False),
        }
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 2

    # Enrichissement des mesures avec seuils
    stations_enrichies = []
    tous_depassements: list[str] = []

    for station in stations_proches:
        mesures_enrichies = {}
        for polluant, mesure in station["mesures"].items():
            if polluant not in polluants_lcsqa:
                continue  # Ne garder que les polluants pertinents pour l'incident
            enrichi = enrich_measure_with_thresholds(polluant, mesure["valeur"])
            enrichi["date"] = mesure.get("date", "")
            mesures_enrichies[polluant] = enrichi
            if enrichi["depasse_alerte"]:
                if polluant not in tous_depassements:
                    tous_depassements.append(polluant)

        stations_enrichies.append({
            "nom":         station["nom"],
            "station_id":  station["station_id"],
            "commune":     station["commune"],
            "departement": station["departement"],
            "distance_km": station["distance_km"],
            "mesures":     mesures_enrichies,
        })

    result = {
        "incident": {
            "lat":       args.lat,
            "lon":       args.lon,
            "type":      args.type,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
        "stations": stations_enrichies,
        "alerte_globale": len(tous_depassements) > 0,
        "polluants_en_depassement": tous_depassements,
        "polluants_surveilles": polluants_lcsqa,
        "polluants_non_disponibles_lcsqa": polluants_indispos,
        "source": "LCSQA / data.gouv.fr",
        "cache_age_minutes": data.get("cache_age_minutes", 0),
        "from_cache": data.get("from_cache", False),
        "stale": data.get("stale", False),
    }

    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


def cmd_refresh_cache(args: argparse.Namespace) -> int:
    """Force le re-téléchargement du cache LCSQA."""
    try:
        data = refresh_cache()
        print(
            json.dumps({
                "status": "ok",
                "nb_stations": data.get("nb_stations", 0),
                "cache_age_minutes": 0,
                "message": f"Cache mis à jour : {data.get('nb_stations', 0)} stations chargées.",
            }, ensure_ascii=False, indent=2)
        )
        return 0
    except Exception as e:
        print(f"[main] Échec refresh-cache : {e}", file=sys.stderr)
        return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Skill qualité de l'air — analyse en situation d'urgence"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # --- Sous-commande incident ---
    incident_p = subparsers.add_parser(
        "incident",
        help="Analyser la qualité de l'air autour d'un incident",
    )
    incident_p.add_argument("--lat", type=float, required=True, help="Latitude GPS de l'incident")
    incident_p.add_argument("--lon", type=float, required=True, help="Longitude GPS de l'incident")
    incident_p.add_argument(
        "--type",
        required=True,
        choices=list(INCIDENT_POLLUTANTS.keys()) + ["inconnu"],
        help="Type d'incident",
    )
    incident_p.add_argument(
        "--radius",
        type=float,
        default=30.0,
        help="Rayon de recherche en km (défaut : 30)",
    )
    incident_p.add_argument(
        "--max-stations",
        type=int,
        default=5,
        dest="max_stations",
        help="Nombre maximum de stations à retourner (défaut : 5)",
    )
    incident_p.set_defaults(func=cmd_incident)

    # --- Sous-commande refresh-cache ---
    refresh_p = subparsers.add_parser(
        "refresh-cache",
        help="Forcer la mise à jour du cache de données",
    )
    refresh_p.set_defaults(func=cmd_refresh_cache)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    sys.exit(args.func(args))


if __name__ == "__main__":
    main()
