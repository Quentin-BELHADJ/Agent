---
name: trafic-bison-fute
description: >
  Interroger les bouchons, ralentissements et chantiers en temps réel via Bison Futé TIPI. 
  Trigger when user asks "trafic A8", "bouchons Nice", "travaux", "état des routes", 
  ou mentionne un département (ex: 06, 11) ou un axe (ex: A61, RN10).
allowed-tools: 
  - Bash(python3 *)
  - Read
---

# Skill Trafic

Pour obtenir les alertes en temps réel, exécute le script avec le département ou l'axe concerné :

```bash
python3 ${CLAUDE_SKILL_DIR}/trafic.py "$ARGUMENTS"