---
name: air-quality
description: Trigger when user asks about air quality, atmospheric pollution, or pollutant concentrations near an incident (incendie, accident chimique, explosion, industrial fire). Keywords: PM2.5, PM10, NO2, SO2, CO, qualité de l'air, polluants atmosphériques, panache, dispersion, AASQA, stations de mesure. Use for emergency assessment of respiratory risk around a GPS point.
---

# Skill 'air-quality'

Pour analyser la qualité de l'air autour d'un incident :
```bash
cd "${SKILL_DIR:-$(dirname "$0")}" && python3 main.py incident --lat <LAT> --lon <LON> --type <TYPE>

```

Types d'incident disponibles : incendie_foret, incendie_industriel, accident_chimique, explosion

Pour forcer la mise à jour du cache :

```bash
cd "${SKILL_DIR:-$(dirname "$0")}" && python3 main.py refresh-cache

```

La sortie est du JSON. Reformate-la en langage naturel avant de répondre.
Pour les seuils réglementaires détaillés, voir `references/thresholds.md`.
Pour la liste complète des polluants par incident, voir `references/pollutants_table.md`.

```
