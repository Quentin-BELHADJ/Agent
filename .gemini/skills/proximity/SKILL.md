---
name: proximity-search
description: >
  Recherche des lieux ou équipements (hôpitaux, pharmacies, restaurants) à proximité d'un lieu 
  ou de l'utilisateur. Trigger when user asks "le plus proche", "autour de moi", "où est l'hôpital".
allowed-tools: 
  - Bash(python3 *)
---

# Skill Proximité

Pour trouver un lieu, utilise le script avec le type de lieu et la localisation :
```bash
python3 ${CLAUDE_SKILL_DIR}/find_nearby.py --type "$TYPE" --location "$LOCATION"