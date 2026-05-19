"""
pollutants.py — Table incident → polluants prioritaires + seuils réglementaires

Valeur ajoutée principale du skill : savoir QUOI regarder selon le type d'incident.

IMPORTANT : NH3 et H2S sont absents des données LCSQA (flux E2 réglementé).
Ils sont listés dans les tables métier pour signaler leur pertinence,
mais la mesure retournée sera null si absente de la source.

Seuils réglementaires :
  - Arrêté du 26 août 2011 (transposition directive 2008/50/CE)
  - Guidelines OMS 2021 (AQG Global Air Quality Guidelines)
"""

import sys

# ---------------------------------------------------------------------------
# Polluants disponibles dans le jeu de données LCSQA
# ---------------------------------------------------------------------------
AVAILABLE_IN_LCSQA = {"O3", "NO2", "SO2", "PM10", "PM2.5", "CO"}

# Polluants pertinents par type d'incident (justification dans references/pollutants_table.md)
INCIDENT_POLLUTANTS: dict[str, list[str]] = {
    "incendie_foret": [
        "CO",     # Combustion incomplète de biomasse (bois, litière) — marqueur primaire
        "PM2.5",  # Particules fines de fumée — risque respiratoire majeur
        "PM10",   # Particules grossières
        "NO2",    # Oxydes d'azote issus de la combustion à haute température
        "O3",     # Précurseur produit par réaction photochimique des NOx + COV
    ],
    "incendie_industriel": [
        "SO2",    # Soufre dans les hydrocarbures, caoutchoucs, matières plastiques
        "NO2",    # Combustion matières industrielles
        "PM2.5",  # Suies et particules ultrafines de synthèse
        "CO",     # Combustion incomplète d'hydrocarbures
        "PM10",   # Particules grossières
        # "H2S"  — pertinent si produits chimiques soufrés, mais hors LCSQA
    ],
    "accident_chimique": [
        "SO2",    # Acide sulfurique, sulfure de carbone, composés soufrés
        "NO2",    # Acide nitrique, engrais azotés
        "CO",     # Gaz de synthèse, solvants
        # "NH3"  — ammoniac (engrais, réfrigérants) — hors LCSQA réglementé
        # "H2S"  — sulfure d'hydrogène (raffinage, égouts) — hors LCSQA réglementé
    ],
    "explosion": [
        "CO",     # Déflagration, gaz de ville, BLEVE
        "NO2",    # Explosifs nitrés (TNT, ANFO) → panache NO2/NO
        "PM10",   # Poussières de structure et débris
        "SO2",    # Si matières souffrées impliquées
    ],
}

# Polluants de base si le type d'incident est inconnu
DEFAULT_POLLUTANTS = ["PM2.5", "PM10", "NO2", "CO"]

# ---------------------------------------------------------------------------
# Seuils réglementaires français et OMS
# ---------------------------------------------------------------------------
# Structure : polluant -> { seuil_info_fr, seuil_alerte_fr, seuil_oms, periode, unite }
#
# Seuil information FR : déclenche une recommandation aux personnes sensibles
# Seuil alerte FR      : déclenche des mesures obligatoires (réduction trafic, etc.)
# Seuil OMS 2021       : valeur guide pour la santé
#
THRESHOLDS: dict[str, dict] = {
    "PM2.5": {
        "seuil_info_fr":   50,   # µg/m³ — moyenne journalière
        "seuil_alerte_fr": 80,   # µg/m³ — moyenne horaire (arrêté 2011)
        "seuil_oms":       15,   # µg/m³ — moyenne 24h (OMS 2021)
        "periode":         "horaire",
        "unite":           "µg/m³",
    },
    "PM10": {
        "seuil_info_fr":   50,
        "seuil_alerte_fr": 125,
        "seuil_oms":       45,
        "periode":         "horaire",
        "unite":           "µg/m³",
    },
    "NO2": {
        "seuil_info_fr":   200,
        "seuil_alerte_fr": 400,
        "seuil_oms":       25,
        "periode":         "horaire",
        "unite":           "µg/m³",
    },
    "SO2": {
        "seuil_info_fr":   300,
        "seuil_alerte_fr": 500,
        "seuil_oms":       40,   # µg/m³ — 24h
        "periode":         "horaire",
        "unite":           "µg/m³",
    },
    "O3": {
        "seuil_info_fr":   180,
        "seuil_alerte_fr": 240,
        "seuil_oms":       100,  # µg/m³ — 8h
        "periode":         "horaire",
        "unite":           "µg/m³",
    },
    "CO": {
        "seuil_info_fr":   None,   # Pas de seuil d'information réglementaire horaire
        "seuil_alerte_fr": 10_000, # µg/m³ — équivalent 10 mg/m³
        "seuil_oms":       4_000,  # µg/m³ — moyenne 24h (OMS 2021)
        "periode":         "horaire",
        "unite":           "µg/m³",
    },
}


def get_pollutants_for_incident(incident_type: str) -> list[str]:
    """
    Retourne la liste des polluants à surveiller pour un type d'incident.
    Si le type est inconnu, log un warning et retourne DEFAULT_POLLUTANTS.
    """
    polluants = INCIDENT_POLLUTANTS.get(incident_type)
    if polluants is None:
        print(
            f"[pollutants] Type d'incident inconnu : '{incident_type}'. "
            f"Types disponibles : {list(INCIDENT_POLLUTANTS.keys())}. "
            f"Utilisation des polluants par défaut : {DEFAULT_POLLUTANTS}.",
            file=sys.stderr,
        )
        return DEFAULT_POLLUTANTS
    # Ne garder que les polluants disponibles dans LCSQA pour la requête réseau
    # Les absents (NH3, H2S) seront mentionnés dans la sortie comme non disponibles
    return polluants


def enrich_measure_with_thresholds(polluant: str, valeur: float) -> dict:
    """
    Prend une mesure brute et ajoute les seuils + flags de dépassement.

    Retourne un dict compatible avec le format de sortie JSON de main.py.
    """
    t = THRESHOLDS.get(polluant, {})
    seuil_alerte = t.get("seuil_alerte_fr")
    seuil_info   = t.get("seuil_info_fr")
    seuil_oms    = t.get("seuil_oms")

    return {
        "valeur":         round(valeur, 2),
        "unite":          t.get("unite", "µg/m³"),
        "seuil_info_fr":  seuil_info,
        "seuil_alerte_fr": seuil_alerte,
        "seuil_oms":      seuil_oms,
        "depasse_alerte": (seuil_alerte is not None and valeur >= seuil_alerte),
        "depasse_info":   (seuil_info is not None and valeur >= seuil_info),
        "depasse_oms":    (seuil_oms is not None and valeur >= seuil_oms),
    }


def get_unavailable_pollutants(incident_type: str) -> list[str]:
    """
    Retourne les polluants pertinents pour cet incident mais absents du jeu LCSQA.
    Utilisé pour informer l'opérateur de ce qui ne peut pas être mesuré via cette source.
    """
    all_relevant = INCIDENT_POLLUTANTS.get(incident_type, DEFAULT_POLLUTANTS)
    return [p for p in all_relevant if p not in AVAILABLE_IN_LCSQA]
