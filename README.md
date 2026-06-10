# Documentation des Agents et Skills (Projet Urgence)

Ce document recense l'ensemble des agents et des compétences (skills) disponibles dans le projet de plugin d'assistance en situation d'urgence, conçu pour Gemini CLI.

## 🤖 Agents

### Geo-Profiler (`geo-profiler.md`)
Expert en investigation OSINT (Open Source Intelligence) et GEOINT (Geospatial Intelligence). Cet agent est spécialisé dans la localisation d'images et l'extraction de coordonnées géographiques précises. Il suit une méthodologie stricte (l'Entonnoir GEOINT) en 5 étapes pour prouver une localisation sans jamais halluciner :
1. Extraction de l'ADN du fichier (EXIF).
2. Observation de l'environnement (Vision).
3. Extraction de texte (OCR).
4. Vérification des faits (Web Search).
5. Triangulation finale (Map).

### Analyste des Risques Cascades (`agent_quentin.py`)
Agent basé sur l'architecture RAG Agentique (via LangGraph) capable d'anticiper les risques d'urgence en chaîne.
Il évalue une situation d'incident donnée en croisant plusieurs sources de données (code INSEE, risques de crues, risques sismiques) et interroge de manière autonome une base de connaissances vectorielle de directives préfectorales si un danger est détecté.

**Comment l'utiliser :**
Le script peut être exécuté directement en ligne de commande pour tester son fonctionnement sur un incident.
```bash
python agent_quentin.py
```
Le script affichera le raisonnement et la réponse finale de l'agent face à l'incident configuré par défaut (ex: *"Il pleut énormément sur Besançon depuis 3 jours, la rivière monte"*).

---

## 🛠️ Compétences (Skills)

### 🌍 Compétences GEOINT (Géospatial et OSINT)
- **geoint_exif_extractor (`geoint-exif`)** : Extrait les métadonnées cachées (EXIF) et les coordonnées GPS potentielles d'une photographie.
- **geoint_vision_analyzer (`geoint-vision`)** : Effectue une analyse visuelle experte d'une image pour en extraire des données géographiques brutes (infrastructures, architecture, environnement, climat) sans déduction hâtive.
- **geoint_ocr_reader (`geoint-ocr`)** : Extrait mathématiquement tout texte visible sur une image à l'aide de l'IA, pour lire des panneaux ou devantures.
- **geoint_web_search (`geoint-search`)** : Lance des requêtes de vérification sur le web pour recouper et valider les indices géographiques trouvés lors de l'analyse visuelle ou textuelle.
- **geoint_map_triangulator (`geoint-map`)** : Utilise les données cartographiques (OpenStreetMap) pour trianguler des coordonnées GPS exactes en croisant un pays, une rue et un éventuel point d'intérêt.

### 📍 Compétences de Localisation & Proximité
- **self_location (`self-position`)** : Détermine la position géographique actuelle (ville, pays, GPS) de la machine hôte via géolocalisation IP.
- **geo_insee_code (`geo`)** : Récupère le code INSEE officiel d'une commune française, étape souvent nécessaire avant d'interroger les bases de données gouvernementales.
- **proximity-search (`proximity`)** : Effectue des recherches précises de points d'intérêt (POI) locaux via OpenStreetMap (ex: hôpitaux, pharmacies, casernes de pompiers, abris).

### 🚨 Compétences d'Urgence, Trafic et Risques
- **risques_sismiques (`risques`)** : Détermine le niveau de risque sismique officiel d'une commune française en utilisant son code INSEE.
- **vigicrues (`vigicrues`)** : Évalue les risques d'inondation en interrogeant les données de stations hydrométriques (hauteur d'eau, débit) dans un rayon donné autour d'un incident.
- **trafic (`trafic`)** : Scrape et interroge les données de trafic officielles (bouchons, accidents, chantiers) pour une analyse de l'encombrement des routes.

### 📊 Compétences Utilitaires
- **quick-map (`quick-map`)** : Permet de générer rapidement des schémas de crise (format SVG) en s'appuyant sur une description textuelle (Mermaid minimaliste).
