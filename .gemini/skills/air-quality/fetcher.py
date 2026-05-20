"""
fetcher.py — Téléchargement et cache des données LCSQA (data.gouv.fr)

Source : bucket S3 INERIS via data.gouv.fr
Format : CSV flux E2 (séparateur point-virgule, encodage UTF-8)
Mise à jour : toutes les heures
Cache local : cache/measures_latest.json (durée 60 min)

Colonnes connues du flux E2 LCSQA :
  station_id (code EoI FR), nom_station, commune, departement,
  type_zone (urbain/periurbain/rural), type_station (fond/trafic/industriel),
  influence, longitude, latitude,
  polluant (O3, NO2, SO2, PM10, PM2.5, CO),
  valeur (µg/m³), date_debut, date_fin, validite

NH3 et H2S ne sont PAS dans ce jeu de données (non réglementés au sens directive 2008/50/CE).
"""

import csv
import json
import logging
import sys
import re
import time
from io import StringIO
from pathlib import Path

import requests

logger = logging.getLogger(__name__)

# URL directe du fichier CSV temps réel (mis à jour le 11/09/2025)
# Source : https://www.data.gouv.fr/datasets/donnees-temps-reel-de-mesure-des-concentrations-de-polluants-atmospheriques-reglementes-1
DATAGOUV_CSV_URL = "https://www.data.gouv.fr/api/1/datasets/r/157ceed4-ce03-4c7d-9cd7-ae60ea07417b"

# Fallback : URL directe du bucket S3 si la redirection data.gouv échoue
BUCKET_BASE_URL = (
    "https://object.infra.data.gouv.fr/ineris-prod/"
    "lcsqa/concentrations-de-polluants-atmospheriques-reglementes/temps-reel/"
)

CACHE_DIR = Path(__file__).parent / "cache"
CACHE_FILE = CACHE_DIR / "measures_latest.json"
CACHE_MAX_AGE_MINUTES = 60

REQUEST_TIMEOUT = 30  # secondes


def _cache_age_minutes() -> float:
    """Retourne l'âge du cache en minutes. Infini si pas de cache."""
    if not CACHE_FILE.exists():
        return float("inf")
    return (time.time() - CACHE_FILE.stat().st_mtime) / 60


def _load_cache() -> dict:
    try:
        return json.loads(CACHE_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as e:
        logger.warning("Cache corrompu ou illisible : %s", e)
        return {}


def _save_cache(data: dict) -> None:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    CACHE_FILE.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")


def _parse_csv(raw_text: str) -> dict:
    """
    Parse le CSV flux E2 LCSQA.
    Retourne un dict indexé par station_id, chaque station contenant
    ses métadonnées et ses mesures les plus récentes par polluant.

    Le format E2 peut varier légèrement selon les exports LCSQA.
    On tente de détecter les colonnes clés de façon robuste.
    """
    reader = csv.DictReader(StringIO(raw_text), delimiter=";")
    fieldnames = reader.fieldnames or []

    # Normalisation des noms de colonnes (minuscules, sans espaces)
    col_map = {f.strip().lower(): f for f in fieldnames}

    # Colonnes attendues avec fallbacks
    def find_col(*candidates):
        for c in candidates:
            if c in col_map:
                return col_map[c]
        return None

    col_station_id  = find_col("station_id", "code_station", "eoi_code", "station")
    col_nom         = find_col("nom_station", "nom", "station_name", "libelle_station")
    col_lat         = find_col("latitude", "lat")
    col_lon         = find_col("longitude", "lon", "long")
    col_polluant    = find_col("polluant", "pollutant", "code_polluant", "parametre")
    col_valeur      = find_col("valeur", "value", "concentration", "valeur_brute")
    col_validite    = find_col("validite", "validity", "statut_valid")
    col_date        = find_col("date_debut", "date_heure_debut", "start_time", "date_fin", "date")
    col_commune     = find_col("commune", "city", "ville")
    col_dept        = find_col("departement", "dept", "code_dept")

    missing = [n for n, c in [
        ("station_id", col_station_id),
        ("latitude",   col_lat),
        ("longitude",  col_lon),
        ("polluant",   col_polluant),
        ("valeur",     col_valeur),
    ] if c is None]

    if missing:
        print(
            f"[fetcher] AVERTISSEMENT : colonnes manquantes dans le CSV : {missing}. "
            f"Colonnes disponibles : {list(col_map.keys())}",
            file=sys.stderr,
        )

    stations: dict = {}

    for row in reader:
        sid = row.get(col_station_id, "").strip() if col_station_id else ""
        if not sid:
            continue

        # Validité : ignorer les mesures invalides (validite == -1 dans le flux E2)
        validite = row.get(col_validite, "1").strip() if col_validite else "1"
        if validite == "-1":
            continue

        # Valeur numérique
        raw_val = row.get(col_valeur, "").strip() if col_valeur else ""
        try:
            valeur = float(raw_val.replace(",", "."))
        except ValueError:
            continue  # mesure sans valeur

        # Coordonnées GPS
        try:
            lat = float(row.get(col_lat, "").replace(",", ".")) if col_lat else None
            lon = float(row.get(col_lon, "").replace(",", ".")) if col_lon else None
        except (ValueError, AttributeError):
            lat = lon = None

        polluant = row.get(col_polluant, "").strip().upper() if col_polluant else ""
        if not polluant:
            continue

        if sid not in stations:
            stations[sid] = {
                "station_id": sid,
                "nom":        row.get(col_nom, sid).strip() if col_nom else sid,
                "commune":    row.get(col_commune, "").strip() if col_commune else "",
                "departement":row.get(col_dept, "").strip() if col_dept else "",
                "latitude":   lat,
                "longitude":  lon,
                "mesures":    {},
            }
        elif lat and stations[sid]["latitude"] is None:
            stations[sid]["latitude"] = lat
            stations[sid]["longitude"] = lon

        stations[sid]["mesures"][polluant] = {
            "valeur": valeur,
            "unite":  "µg/m³",
            "date":   row.get(col_date, "").strip() if col_date else "",
        }

    return {
        "fetched_at": time.time(),
        "nb_stations": len(stations),
        "stations": stations,
    }

def _download_csv() -> str:
    today = date.today()
    base = (
        "https://object.infra.data.gouv.fr/ineris-prod/lcsqa/"
        "concentrations-de-polluants-atmospheriques-reglementes/temps-reel/fr/"
    )
    # Essaye aujourd'hui, puis hier si 404 (données parfois publiées avec délai)
    for delta in range(3):
        d = today.replace(day=today.day - delta) if delta == 0 else (
            date.fromordinal(today.toordinal() - delta)
        )
        url = f"{base}{d.year}/FR_E2_{d.isoformat()}.csv"
        print(f"[fetcher] Tentative : {url}", file=sys.stderr)
        resp = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=30)
        if resp.status_code == 200:
            resp.encoding = resp.apparent_encoding or "utf-8"
            return resp.text
        print(f"[fetcher] {resp.status_code} pour {url}", file=sys.stderr)
    
    raise requests.RequestException("Aucun fichier CSV trouvé pour les 3 derniers jours.")


def get_measures(force_refresh: bool = False) -> dict:
    age = _cache_age_minutes()

    if not force_refresh and age < CACHE_MAX_AGE_MINUTES:
        data = _load_cache()
        if data:
            data["cache_age_minutes"] = round(age, 1)
            data["from_cache"] = True
            return data

    try:
        raw = _download_csv()
        data = _parse_csv(raw)
        _save_cache(data)
        data["cache_age_minutes"] = 0.0
        data["from_cache"] = False
        logger.info("Données LCSQA téléchargées : %d stations", data["nb_stations"])
        return data

    except requests.RequestException as e:
        print(f"[fetcher] Erreur réseau : {e}", file=sys.stderr)

        # CORRECTION : si force_refresh, on ne masque pas l'échec
        if force_refresh:
            raise RuntimeError(
                f"Téléchargement forcé échoué : {e}"
            ) from e

        # Fallback cache périmé (seulement en mode normal)
        stale = _load_cache()
        if stale:
            print(
                f"[fetcher] Utilisation du cache périmé ({round(age, 1)} min).",
                file=sys.stderr,
            )
            stale["cache_age_minutes"] = round(age, 1)
            stale["from_cache"] = True
            stale["stale"] = True
            return stale

        raise RuntimeError(
            "Impossible de récupérer les données LCSQA et aucun cache disponible."
        ) from e


def refresh_cache() -> dict:
    """Force le re-téléchargement et met à jour le cache."""
    return get_measures(force_refresh=True)
