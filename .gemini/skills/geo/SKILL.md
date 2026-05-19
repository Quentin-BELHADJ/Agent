---
name: geo_insee_code
description: >
  Récupère le code INSEE officiel d'une commune française.
  À utiliser avant d'interroger des bases de données gouvernementales qui requièrent un code INSEE (comme les risques naturels).
allowed-tools: 
  - Bash(python3 *)
---

# Instructions pour l'Agent

Utilise cet outil lorsque tu as besoin du code INSEE d'une commune française.

```bash
python3 ~/.gemini/skills/geo/commune.py "NOM_DE_LA_COMMUNE"
```
