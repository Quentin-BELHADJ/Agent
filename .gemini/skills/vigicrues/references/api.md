# API Vigicrues — Documentation des endpoints

## Accès

Aucune clé API requise. Toutes les URLs sont publiques.
Licence : Licence Ouverte / Open Licence v2.0 (Etalab).

---

## Endpoint 1 : Liste des stations de vigilance crues

**URL :** `http://www.vigicrues.gouv.fr/services/v1.1/StaEntVigiCru.json`  
**Méthode :** GET  
**Paramètres :** aucun (retourne toutes les stations)  
**Mise à jour :** quotidienne (les stations bougent rarement)  
**Taille de réponse :** ~500 Ko (environ 1 700 stations)

### Structure de réponse

```json
{
  "EntVigiCru": {
    "StaEntVigiCru": [
      {
        "CdStationVigiCru": "O200001001",
        "LbStationVigiCru": "La Seine à Paris",
        "LbCoursEauVigiCru": "La Seine",
        "CoordStationVigiCru": {
          "LatStationVigiCru": "48.8534",
          "LonStationVigiCru": "2.3488"
        },
        "PereBoitEntVigiCru": {
          "CdEntVigiCru": "8",
          "LbEntVigiCru": "SPC Seine-Amont-Marne-Aube"
        }
      }
    ]
  }
}
```

### Champs utilisés

| Champ brut | Champ normalisé | Description |
|---|---|---|
| `CdStationVigiCru` | `code` | Identifiant unique de la station |
| `LbStationVigiCru` | `nom` | Nom de la station |
| `LbCoursEauVigiCru` | `cours_eau` | Nom du cours d'eau |
| `LatStationVigiCru` | `lat` | Latitude WGS84 (string à convertir en float) |
| `LonStationVigiCru` | `lon` | Longitude WGS84 (string à convertir en float) |
| `CdEntVigiCru` | `territoire_code` | Code du territoire de vigilance parent |
| `LbEntVigiCru` | `territoire_nom` | Nom du SPC responsable |

---

## Endpoint 2 : Observations temps réel

**URL :** `https://www.vigicrues.gouv.fr/services/observations.json/index.php`  
**Méthode :** GET  
**Paramètre requis :** `CdStationHydro=<code_station>`  
**Paramètre optionnel :** `FormatDate=iso` (recommandé)  
**Mise à jour :** toutes les heures environ

### Exemple

```
GET https://www.vigicrues.gouv.fr/services/observations.json/index.php?CdStationHydro=O200001001&FormatDate=iso
```

### Structure de réponse

```json
{
  "Serie": {
    "ObssHydro": [
      {
        "DtObsHydro": "2024-05-21T14:00:00+02:00",
        "ResObsHydro": 1.42
      },
      {
        "DtObsHydro": "2024-05-21T13:00:00+02:00",
        "ResObsHydro": 1.39
      }
    ]
  }
}
```

`ResObsHydro` est la hauteur en mètres. La liste est triée du plus récent au plus ancien.  
Les 30 derniers jours de données non expertisées sont disponibles.

---

## Endpoint 3 : Bulletin de vigilance crues

**URL :** `https://www.vigicrues.gouv.fr/services/bulletin.json`  
**Méthode :** GET  
**Paramètre requis :** `CdEntVigiCru=<code_territoire>`  
**Mise à jour :** à chaque changement de niveau (potentiellement plusieurs fois par jour en crue)

### Exemple

```
GET https://www.vigicrues.gouv.fr/services/bulletin.json?CdEntVigiCru=8
```

### Structure de réponse (simplifiée)

```json
{
  "VigiCru": {
    "NivSituVigiCru": 2,
    "LbSituVigiCru": "Vigilance jaune",
    "DateHeureSituVigiCru": "2024-05-21T12:00:00+02:00"
  }
}
```

`NivSituVigiCru` : niveau entier de 1 à 4.

---

## Stratégie de cache

- **Stations** (`StaEntVigiCru`) : TTL 6 heures. Les stations bougent rarement.
- **Observations** : pas de cache — données temps réel, appelées à chaque `incident`.
- **Bulletin** : pas de cache — niveau de vigilance peut changer rapidement en crue.

---

## Codes d'erreur courants

| Code HTTP | Cause probable | Action |
|---|---|---|
| 403 | IP bloquée ou User-Agent refusé | Ajouter un User-Agent standard |
| 404 | Code station ou territoire invalide | Vérifier le code dans le cache |
| 503 | API indisponible temporairement | Réessayer après 5 minutes |
| Timeout | Réseau lent ou API surchargée | Augmenter `TIMEOUT` dans `fetcher.py` |

---

## Sources

- Documentation officielle : `https://www.vigicrues.gouv.fr/services/v1.1`
- FAQ Vigicrues : `https://www.vigicrues.gouv.fr/categorie/1`
- Fiche data.gouv.fr : `https://www.data.gouv.fr/datasets/vigicrues`
