# Architecture du skill vigicrues — Justification des choix techniques

## Choix de la source de données

### Source retenue : API HubEau Hydrométrie v2 (Service Central Vigicrues / BRGM)

**URLs :**
- `https://hubeau.eaufrance.fr/api/v2/hydrometrie/referentiel/stations` — référentiel des stations avec filtre géospatial
- `https://hubeau.eaufrance.fr/api/v2/hydrometrie/observations_tr` — observations temps réel (hauteur H, débit Q)

**Pourquoi HubEau et pas l'API Vigicrues v1.1 ?**

L'API Vigicrues v1.1 (`www.vigicrues.gouv.fr/services/v1.1/`) est **désactivée**. Elle retourne désormais une page HTML (redirection 301 HTTP→HTTPS puis réponse HTML) au lieu de JSON. Cette désactivation a été constatée lors du développement (mai 2026) : curl sur l'endpoint renvoie `<!DOCTYPE html>` au lieu du JSON documenté.

HubEau (`hubeau.eaufrance.fr`) est le successeur officiel. Les données sont issues de la même source — la Plate-forme HYDRO Centrale (PHyC), opérée par le Service Central Vigicrues (SCV). HubEau est maintenu par le BRGM, actif, documenté, et mis à jour en juin 2025 (v2 de l'API).

**Pas de clé API requise.** Toutes les URLs sont publiques, sous Licence Ouverte v2.0 (Etalab).

---

## Avantage architectural de HubEau : filtre géospatial natif

L'API HubEau accepte les paramètres `latitude`, `longitude`, `distance` directement dans la requête stations :

```
GET /api/v2/hydrometrie/referentiel/stations?latitude=48.85&longitude=2.35&distance=30&size=5
```

Cela supprime le besoin de :
- Télécharger l'intégralité du référentiel (~1 700 stations)
- Le mettre en cache localement
- Calculer les distances haversine côté client

La version initiale du skill (basée sur Vigicrues v1.1) nécessitait un fichier `stations.py` avec la formule haversine et un cache JSON local TTL 6h. Ces deux composants ont été supprimés. Le code est plus court, plus simple, et sans état local.

---

## Unités de mesure HubEau

Point critique à ne pas ignorer :

| Grandeur | Paramètre API | Unité retournée | Conversion |
|---|---|---|---|
| Hauteur (H) | `grandeur_hydro=H` | millimètres | ÷ 1000 → mètres |
| Débit (Q) | `grandeur_hydro=Q` | litres/seconde | ÷ 1000 → m³/s |

La hauteur retournée est relative au zéro de chaque station (ou parfois au référentiel altimétrique NGF selon la station). Elle n'est **pas comparable entre stations**. Ce qui compte opérationnellement, c'est la tendance (montée/stabilité/baisse) et le niveau de vigilance officiel sur vigicrues.gouv.fr.

---

## Stratégie : pas de cache

Contrairement à la version initiale, ce skill ne maintient aucun cache local.

Raisons :
- Le filtre géospatial HubEau est rapide (< 1s en conditions normales)
- En situation d'urgence, une donnée de hauteur d'eau vieille de 6h est dangereuse
- Supprimer le cache supprime une source de bugs (permissions, corruption, TTL mal géré)

La contrepartie est une dépendance réseau à chaque appel. Si HubEau est indisponible, le skill retourne une erreur explicite (`status: error`) avec un message lisible — jamais de données périmées silencieuses.

---

## Choix d'architecture : skill vs MCP

Ce skill utilise le format skill (SKILL.md + script Python) plutôt qu'un MCP server.

| Critère | MCP | Skill |
|---|---|---|
| Coût tokens idle | ~1 000–2 000 tokens en permanence | ~50 tokens |
| Serveur requis | Oui (port TCP, processus persistant) | Non |
| Déployable sur terminal opérateur | Complexe | `cp -r vigicrues/ ~/.agents/skills/` |
| Testable sans Gemini CLI | Non | `python3 main.py incident --lat 48.85 --lon 2.35` |
| Dépendances | FastMCP + dépendances serveur | `requests` uniquement |

En situation d'urgence, on veut un agent réactif avec un contexte minimal et une infrastructure zéro.

---

## Structure des fichiers

```
vigicrues/
├── SKILL.md               ← déclenchement automatique (< 30 lignes, < 80 tokens description)
├── main.py                ← point d'entrée CLI, argparse, JSON stdout
├── fetcher.py             ← appels HubEau v2, parsing, conversion d'unités
├── requirements.txt       ← requests==2.32.3 uniquement
├── .gitignore             ← __pycache__/
└── references/
    ├── api.md             ← documentation des endpoints HubEau
    ├── vigilance.md       ← niveaux de vigilance et interprétation opérationnelle
    └── architecture.md    ← ce fichier
```

Les fichiers `references/` ne sont chargés en contexte que si Gemini en a explicitement besoin. Leur coût tokens au repos est zéro.

---

## Alignement avec le critère du projet

> "Si un skill ne sert qu'en exploration de fond, il n'a rien à faire dans ce plugin. Seules les capacités mobilisables en urgence ont leur place." — C. Guyeux

Ce skill répond directement à la question opérationnelle : **"Y a-t-il un risque d'inondation autour de ce point d'incident ?"**

Cas d'usage concrets :
- Incendie en zone inondable : les pompiers peuvent-ils accéder par les routes riveraines ?
- Accident industriel en bord de rivière : risque de dispersion fluviale accrue par la crue ?
- Évacuation de population : les axes de repli sont-ils menacés par la montée des eaux ?
