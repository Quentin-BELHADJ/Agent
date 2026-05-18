---
name: geoint_exif_extractor
description: Extrait les métadonnées cachées (EXIF) et les coordonnées GPS d'une photographie.
---

# Instructions pour l'Agent

Ceci est un outil spécialisé dans l'extraction de métadonnées géospatiales pour des enquêtes GEOINT. 
Son rôle est d'analyser les fichiers images fournis par l'utilisateur pour y trouver des traces GPS, des dates ou des modèles d'appareils photo.

## Comment agir :
Lorsque l'utilisateur te demande d'analyser une image pour trouver sa localisation, ou s'il te demande d'extraire des métadonnées, tu DOIS :
1. Identifier le chemin du fichier image fourni par l'utilisateur.
2. Utiliser ton outil d'exécution de commande (shell) pour lancer le script Python suivant :
   `python extract_exif.py "<chemin_vers_image>"`
3. Analyser le JSON renvoyé par le script.

## Traitement de la réponse :
- Si `has_gps` est `true`, annonce immédiatement à l'utilisateur que des coordonnées directes ont été trouvées et donne-lui la latitude, la longitude, ainsi que le lien Google Maps.
- Si `status` est `error` ou si `has_gps` est `false`, informe l'utilisateur que l'image a été nettoyée de ses métadonnées géographiques et propose-lui de passer à l'analyse visuelle (Vision).