---
name: vigicrues
description: >
  À utiliser lorsque l'utilisateur pose des questions sur le risque d'inondation, les niveaux d'eau des rivières, les alertes de crue ou la vigilance crues à proximité d'un incident ou d'un point GPS.
  Mots-clés : crue, inondation, vigilance, rivière, fleuve, hauteur d'eau, débit, station hydrométrique.
allowed-tools: 
  - Bash(python3 *)
---

# Instructions pour l'Agent

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

**Règles importantes :**
- Si le script retourne `status: error`, signale l'erreur à l'utilisateur telle quelle. Ne pas compenser par une recherche web.
- Si aucune station n'est trouvée (`status: no_stations`), suggère d'augmenter `--radius` et relance. Ne pas chercher sur le web.
- Le script gère déjà les retries réseau en interne. Ne pas relancer manuellement plus d'une fois.

Pour le niveau de vigilance officiel : https://www.vigicrues.gouv.fr
Pour le détail des endpoints, voir `references/api.md`.
Pour l'interprétation opérationnelle, voir `references/vigilance.md`.
