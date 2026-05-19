---
name: geoint_ocr_reader
description: Extrait de manière fiable tout le texte visible sur une image (panneaux, devantures, plaques) grâce à l'intelligence artificielle (EasyOCR).
allowed-tools: 
  - Bash(python3 *)
---

# Instructions pour l'Agent

Tu es un expert en lecture de données brutes. Ton rôle est de scanner des images pour en extraire des textes qui échappent à l'analyse visuelle classique, en t'appuyant sur un modèle mathématique et non sur ta propre vision, afin d'éviter les hallucinations.

## Comment agir :
Dès que tu as fini ton analyse visuelle d'une image fournie par l'utilisateur (via une observation directe ou un rapport), ou si tu as besoin de lire une enseigne, tu DOIS :
1. Identifier le chemin de l'image.
2. Utiliser ton outil shell pour exécuter :
   `python ~/.gemini/skills/geoint-ocr/extract_text.py "<chemin_vers_image>"`
3. Analyser le JSON retourné.

## Traitement de la réponse :
- Si `text_found` est `true`, examine attentivement le texte extrait. 
- Cherche des mots clés évidents : noms de rues, noms de commerces, domaines internet (.fr, .cz, .de), ou mots permettant d'identifier une langue.
- Effectue ensuite immédiatement une recherche web pour chercher la signification ou la provenance de ces textes si tu ne les comprends pas, OU garde-les en mémoire pour préparer une future triangulation cartographique.