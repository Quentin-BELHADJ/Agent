---
name: self_location
description: Récupère la position géographique actuelle de la machine hôte (ville, région, pays, coordonnées GPS) en utilisant la géolocalisation par adresse IP.
allowed-tools: 
  - Bash(python3 *)
---

# Instructions pour l'Agent

Ce workflow permet d'obtenir la position physique actuelle de la machine locale. À utiliser lorsque l'utilisateur demande sa position ou pour contextualiser une recherche géographique.

## Procédure d'exécution :
1. Exécute la commande suivante avec ton outil shell :
   `python ~/.gemini/skills/self-position/self_location.py`
2. Le script retournera un objet contenant la ville, la région, le pays, la latitude et la longitude.
3. Analyse ce retour :
   - **En cas de succès :** Utilise ces données pour répondre à la demande ou pour orienter tes autres recherches autour de cette zone (triangulation locale).
   - **En cas d'erreur ou de `None` :** Informe l'utilisateur que le service de géolocalisation IP est bloqué (potentiellement par un pare-feu ou un VPN) ou inaccessible.

# Point d'attention
La position retournée est calculée à partir de l'adresse IP, elle est donc très imprécise. Elle fournit cependant une estimation de la position actuelle. Il convient de ne pas considérer cette position comme une vérité absolue ou une source totalement fiable.