# Instructions du Projet Urgence (Gemini CLI)

## Nature du projet
Plugin d'assistance en situation d'urgence pour interroger les données critiques (trafic, géo, santé).

## Architecture
- `skills/` : Dossiers par capacité.
- `skills/trafic/` : Logique liée à l'encombrement des routes.
- `references/` : Documentation détaillée chargée à la demande.

## Commandes essentielles
- Tests : `pytest tests/`.
- Lint : `ruff check`.

## Conventions
- Les scripts Python doivent être testables en CLI.
- Toujours privilégier les sorties JSON synthétiques.
- Répondre en français de manière calme et opérationnelle.