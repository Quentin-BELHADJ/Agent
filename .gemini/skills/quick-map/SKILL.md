---
name: quick-map
description: Génère un schéma Mermaid. Trigger: "schéma", "diagramme", "carte mermaid".
allowed-tools: Bash (python3 *)
---

# Instructions pour l'Agent

RÈGLE ABSOLUE : Tu ne dois JAMAIS afficher le code Mermaid à l'utilisateur ni expliquer le schéma. 

Dès que l'utilisateur demande un schéma, tu dois EXÉCUTER la commande Shell suivante en respectant STRICTEMENT cette syntaxe (utilise des chemins relatifs et ne rajoute aucun guillemet autour de la commande globale) :

`echo "<CODE_MERMAID_MINIMAL>" | python ".gemini/skills/quick-map/visualize.py" --output "schema.svg"`

Contraintes pour <CODE_MERMAID_MINIMAL> :
- Uniquement les nœuds et les liens (ex: A[PC Crise] --> B[Secteur Inonde]).
- RÈGLE DE FORMATAGE : N'utilise AUCUN accent ni caractère spécial dans le texte. Remplace systématiquement les lettres accentuées par leur équivalent sans accent (ex: Hôpital -> Hopital, Inondé -> Inonde, à -> a).
- AUCUN attribut de style (`style`, `fill`, `stroke`).
- AUCUN commentaire (`%%`).
- AUCUN saut de ligne inutile.

Ta seule réponse à l'utilisateur doit être le retour exact du terminal (ex: "OK: schema.svg"). Aucun autre texte n'est autorisé.