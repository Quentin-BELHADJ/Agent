# Documentation des Agents et Skills (Projet Urgence)

Ce dépôt contient le code d'un projet universitaire portant sur les agents intelligents. Nous avons choisi de traiter le sujet de la gestion de crise et de l'aide à la décision lors de catastrophes naturelles (inondations, séismes, planification d'itinéraires d'évacuation d'urgence et localisation d'images d'incidents par GEOINT).

Ce document présente l'ensemble des compétences (skills) et des agents spécialisés conçus pour Gemini CLI.

---

## Compétences (Skills)

### Compétences GEOINT (Géospatial et OSINT)
- **geoint_exif_extractor (geoint-exif)** : Extrait les métadonnées cachées (EXIF) et les coordonnées GPS potentielles d'une photographie.
- **geoint_vision_analyzer (geoint-vision)** : Effectue une analyse visuelle experte d'une image pour en extraire des données géographiques brutes (infrastructures, architecture, environnement, climat) sans déduction hâtive.
- **geoint_ocr_reader (geoint-ocr)** : Extrait mathématiquement tout texte visible sur une image à l'aide de l'IA, pour lire des panneaux ou devantures.
- **geoint_web_search (geoint-search)** : Lance des requêtes de vérification sur le web pour recouper et valider les indices géographiques trouvés lors de l'analyse visuelle ou textuelle.
- **geoint_map_triangulator (geoint-map)** : Utilise les données cartographiques (OpenStreetMap) pour trianguler des coordonnées GPS exactes en croisant un pays, une rue et un éventuel point d'intérêt.

### Compétences de Localisation & Proximité
- **self_location (self-position)** : Détermine la position géographique actuelle (ville, pays, GPS) de la machine hôte via géolocalisation IP.
- **geo_insee_code (geo)** : Récupère le code INSEE officiel d'une commune française, étape souvent nécessaire avant d'interroger les bases de données gouvernementales.
- **proximity-search (proximity)** : Effectue des recherches précises de points d'intérêt (POI) locaux via OpenStreetMap (ex: hôpitaux, pharmacies, casernes de pompiers, abris).

### Compétences d'Urgence, Trafic et Risques
- **seismic_risks (risques)** : Détermine le niveau de risque sismique officiel d'une commune française en utilisant son code INSEE.
- **vigicrues (vigicrues)** : Évalue les risques d'inondation en interrogeant les données de stations hydrométriques (hauteur d'eau, débit) dans un rayon donné autour d'un incident.
- **trafic (trafic)** : Scrape et interroge les données de trafic officielles (bouchons, accidents, chantiers) pour une évaluation en temps réel de l'encombrement des routes.

### Compétences Utilitaires
- **quick-map (quick-map)** : Permet de générer rapidement des schémas de crise (format SVG) en s'appuyant sur une description textuelle (Mermaid minimaliste).

---

## Agents

Tous les agents du projet sont implémentés avec LangGraph sous forme d'agents ReAct autonomes. Leurs instructions systèmes (prompts) sont définies dans des fichiers Markdown associés sous `.gemini/agents/`.

### Orchestrateur Principal (master_agent.py / master-agent.md)
L'orchestrateur superviseur du projet. Il reçoit la requête globale de l'utilisateur, planifie le plan d'action de haut niveau, et délègue les tâches spécialisées aux autres agents en les appelant comme des outils.

### Guide d'Évacuation d'Urgence (crisis_navigator_agent.py / crisis-navigator.md)
Agent chargé de la planification d'itinéraires sûrs. Il détermine la position de départ (par IP via `self_location` si nécessaire), trouve la destination de secours la plus proche (`proximity`), et vérifie l'état hydrologique (`vigicrues`) et routier (`trafic`) pour proposer un trajet sécurisé.

### Geo-Profiler (geo_profiler_agent.py / geo-profiler.md)
Expert en investigation OSINT (Open Source Intelligence) et GEOINT (Geospatial Intelligence). Cet agent est spécialisé dans la localisation d'images et l'extraction de coordonnées géographiques précises. Il suit une méthodologie stricte en 5 étapes (l'Entonnoir GEOINT) :
1. Extraction de l'ADN du fichier (EXIF via `geoint_exif_extractor`).
2. Observation de l'environnement (Vision via `geoint_vision_analyzer`).
3. Extraction de texte (OCR via `geoint_ocr_reader`).
4. Vérification des faits (Web Search via `geoint_web_search`).
5. Triangulation finale (Map via `geoint_map_triangulator`).

### Évaluateur Environnemental (risk_assessor_agent.py / risk-assessor.md)
Génère des diagnostics de vulnérabilité et de risques naturels pour une commune française. Il récupère le code INSEE de la commune (`geo_insee_code`), évalue l'aléa sismique (`seismic_risks`), interroge les stations de crue (`vigicrues`) et cherche les arrêtés de catastrophe naturelle en cours sur le web.

### Analyste des Risques Cascades (risk_cascade_agent.py / risk-cascade.md)
Agent RAG agentique capable d'anticiper les risques en chaîne à partir d'un incident. Il croise les données géographiques et environnementales (INSEE, crues, séismes) et interroge de manière autonome une base de connaissances vectorielle locale en mémoire pour extraire et restituer les consignes préfectorales officielles.

**Comment exécuter les agents en ligne de commande :**
Les scripts des agents peuvent être exécutés individuellement pour tester leur comportement :
```bash
# Lancer l'orchestrateur principal
python master_agent.py "Votre requête d'assistance globale"

# Lancer l'agent de guidage et d'évacuation
python crisis_navigator_agent.py "Trouve l'hôpital le plus proche de ma position"

# Lancer l'agent d'investigation d'image (GEOINT)
python geo_profiler_agent.py test_images/photo_with_exif.jpg

# Lancer l'agent d'évaluation des risques d'une commune
python risk_assessor_agent.py "Besançon"

# Lancer l'agent d'analyse de risques cascades (RAG)
python risk_cascade_agent.py
```
