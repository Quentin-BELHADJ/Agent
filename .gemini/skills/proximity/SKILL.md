---
name: proximity-search
description: >
  Recherche précise de POI (points d'intérêt) via OpenStreetMap. 
  À utiliser pour "hopital", "McDo", "garage", "abri", "supermarché", etc.
allowed-tools: 
  - Bash(python3 *)
---

# Skill Proximité Universel

Pour chaque demande, choisis le tag OSM le plus approprié :
- Restauration : `amenity=restaurant` ou `amenity=fast_food` (pour McDo)
- Santé : `amenity=hospital`, `amenity=pharmacy` ou `amenity=doctors`
- Commerce : `shop=supermarket`, `shop=bakery`
- Urgence : `amenity=police`, `amenity=fire_station`
- Loisirs : `leisure=park`, `tourism=hotel`

```bash
python3 ${CLAUDE_SKILL_DIR}/find_nearby.py "$TAG_KEY" "$TAG_VALUE" "$LOCATION"