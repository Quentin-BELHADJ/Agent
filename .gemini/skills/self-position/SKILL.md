---
name: self_location
description: Récupère la position géographique actuelle de la machine hôte (ville, région, pays, coordonnées GPS) en utilisant la géolocalisation par adresse IP.
---

# Mode d'emploi de la compétence (Skill)

Ce workflow permet d'obtenir la position physique actuelle de la machine locale. À utiliser lorsque l'utilisateur demande sa position ou pour contextualiser une recherche géographique.

## Procédure d'exécution :
1. Exécute la commande suivante avec l'outil `run_shell_command` :
   `python self_location.py`
2. Le script retournera un objet contenant la ville, la région, le pays, la latitude et la longitude.
3. Analyse ce retour :
   - **En cas de succès :** Utilise ces données pour répondre à la demande ou pour orienter tes autres recherches autour de cette zone (triangulation locale).
   - **En cas d'erreur ou de `None` :** Informe l'utilisateur que le service de géolocalisation IP est bloqué (potentiellement par un pare-feu ou un VPN) ou inaccessible.

# Point d'attention
La position retourné est calculé à partir de l'adresse ip donc c'est très imprecis. Cela donne cependant une approximation de la position actuel. Ne jamais prendre la position en tant que source sûr.