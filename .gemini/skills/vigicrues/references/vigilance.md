# Niveaux de vigilance crues — Interprétation opérationnelle

## Échelle de vigilance Vigicrues

| Niveau | Couleur | Signification | Action recommandée |
|---|---|---|---|
| 1 | Vert | Pas de vigilance particulière | Surveillance normale |
| 2 | Jaune | Risque de crue ou de montée rapide des eaux | Vigilance accrue, suivi régulier |
| 3 | Orange | Risque de crue importante pouvant avoir un impact significatif | Mobilisation des services, information populations riveraines |
| 4 | Rouge | Risque de crue exceptionnelle — menace directe et généralisée | Activation du plan ORSEC, évacuations possibles |

**Source :** SCHAPI / Service Central Vigicrues — Ministère de la Transition Écologique.

---

## Interprétation en situation d'urgence

### Niveau 1 — Vert
Situation normale. La hauteur d'eau est dans les valeurs habituelles.
Aucune restriction de circulation fluviale ou routière attendue.

### Niveau 2 — Jaune
Montée des eaux possible. Les zones basses peuvent être touchées.
Points de vigilance : sous-sols, caves, routes en zones inondables.
Les secours doivent être informés mais la mobilisation n'est pas encore requise.

### Niveau 3 — Orange
Crue significative. Des débordements sont probables sur les secteurs les plus exposés.
Impact possible sur : routes, voies ferrées, réseaux (électricité, eau potable).
Les plans communaux de sauvegarde (PCS) doivent être activés.
Coordination préfectorale recommandée.

### Niveau 4 — Rouge
Crue exceptionnelle ou catastrophique. Menace pour les personnes et les biens à grande échelle.
Déclenchement du plan ORSEC départemental probable.
Coordination nationale possible (COZ, COGIC).
Priorité : mise en sécurité des personnes, coupure des réseaux à risque.

---

## Hauteur d'eau : valeurs de référence

La hauteur d'eau (`ResObsHydro`, en mètres) est relative au zéro de la station — elle n'est pas comparable entre stations. Ce qui compte, c'est la tendance (montée/descente) et le dépassement des seuils historiques propres à chaque station.

Pour connaître les seuils d'alerte propres à une station :
`https://www.vigicrues.gouv.fr/station/<CdStationVigiCru>/`

---

## Territoires de vigilance (SPC)

Les territoires correspondent aux Services de Prévision des Crues (SPC) régionaux.

| Code | Nom SPC | Région approximative |
|---|---|---|
| 1 | SPC Garonne-Tarn-Lot | Sud-Ouest |
| 2 | SPC Loire-Cher-Indre | Centre-Ouest |
| 3 | SPC Maine-Loire-Aval | Pays de la Loire |
| 4 | SPC Bretagne-Maine | Bretagne |
| 5 | SPC Normandie | Normandie |
| 6 | SPC Île-de-France | Île-de-France |
| 7 | SPC Seine-Amont | Bourgogne/Grand-Est |
| 8 | SPC Seine-Amont-Marne-Aube | Grand-Est |
| 9 | SPC Artois-Picardie | Hauts-de-France |
| 10 | SPC Rhin-Sarre | Alsace |
| 11 | SPC Rhône-Saône | Auvergne-Rhône-Alpes |
| 12 | SPC Méditerranée-Ouest | Occitanie |
| 13 | SPC Grand-Delta | PACA |

La liste complète est disponible via l'API : `https://www.vigicrues.gouv.fr/services/v1.1/TerEntVigiCru.json`

---

## Interprétation de la sortie JSON du skill

```json
{
  "niveau_vigilance_max": 3,
  "couleur_vigilance_max": "Orange",
  "stations": [
    {
      "nom": "La Loire à Orléans",
      "distance_km": 4.2,
      "observation": {
        "hauteur_m": 3.85,
        "date_obs": "2024-05-21T14:00:00+02:00",
        "disponible": true
      },
      "vigilance": {
        "niveau_vigilance": 3,
        "couleur": "Orange",
        "disponible": true
      }
    }
  ]
}
```

`niveau_vigilance_max` = niveau le plus élevé parmi toutes les stations dans le rayon.
C'est la valeur à communiquer en premier au poste de commandement.
