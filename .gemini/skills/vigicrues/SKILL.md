---
name: vigicrues
description: Trigger when user asks about flood risk, river water levels, flood alerts, or vigilance crues near an incident or GPS point. Keywords: crue, inondation, vigilance, rivière, fleuve, hauteur d'eau, débit, station hydrométrique, flood, water level, overflow, submersion, HubEau. Use for emergency assessment of flood risk around a location.
---

# Skill 'vigicrues'

Pour interroger les hauteurs d'eau autour d'un point GPS d'incident :

```bash
cd "${SKILL_DIR}" && python3 main.py incident --lat <LAT> --lon <LON> --radius <KM>
```

Exemple :
```bash
cd "${SKILL_DIR}" && python3 main.py incident --lat 48.85 --lon 2.35 --radius 30
```

La sortie est du JSON. Reformate-la en langage naturel avant de répondre.
La hauteur (`hauteur_m`) est en mètres, relative au zéro de chaque station.
Le débit (`debit_m3s`) est en m³/s.
Pour le niveau de vigilance officiel : https://www.vigicrues.gouv.fr
Pour le détail des endpoints, voir `references/api.md`.
Pour l'interprétation opérationnelle, voir `references/vigilance.md`.
