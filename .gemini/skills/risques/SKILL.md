---
name: risques_sismiques
description: >
  Récupère le niveau de risque sismique officiel d'une commune française à partir de son code INSEE.
  À utiliser pour évaluer la dangerosité d'une zone géographique, "quel est le risque sismique", "tremblement de terre".
allowed-tools: 
  - Bash(python3 *)
---

# Instructions pour l'Agent

Utilise cet outil pour connaître la sismicité d'une commune. Tu dois ABSOLUMENT fournir le code INSEE de la commune (et non son nom). Si tu n'as pas le code INSEE, utilise d'abord l'outil `geo_insee_code`.

```bash
python3 ~/.gemini/skills/risques/sismique.py "CODE_INSEE"
```
