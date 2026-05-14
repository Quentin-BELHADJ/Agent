---
name: trafic-bison-fute
description: >
  Recherche d'informations routières en temps réel sur Bison Futé (bouchons, accidents, fermetures, chantiers). 
  À utiliser quand l'utilisateur dit : "quel est l'état du trafic", "y a-t-il des bouchons sur l'A8", 
  "est-ce que la RN10 est fermée", "quels sont les travaux dans le 06", "embouteillages", "accès routier".
allowed-tools: 
  - Bash(python3 *)
---

# Skill Trafic Multi-Sources

Pour obtenir une information, utilise le script avec le type d'information adapté :

- `bouchons` : pour les ralentissements et embouteillages.
- `evenements` : pour les routes fermées, accidents, sorties déconseillées.
- `chantiers` : pour les travaux actuels bloquants.
- `previsions` : pour les travaux prévus prochainement.

```bash
python3 ${CLAUDE_SKILL_DIR}/trafic.py "$TYPE" "$MOT_CLE"