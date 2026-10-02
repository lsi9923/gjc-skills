---
name: argo-vault
description: "Connect GJC agents with Argo AI Company vault memory for bi-directional [[wiki-linking]] notes, conversation handovers, persona cards, and company knowledge graph."
---

# Argo AI Company Vault Memory & Personas

## Overview
Argo organizes AI companies around folder-unit memory (vault) and specialist personas.
GJC agents interact with Argo vaults to persist durable company knowledge, retrieve past turn context, and update the auto-linking knowledge graph.

## Commands
- `argo-vault-bridge write-note <slug> <title> <content> [tags]`: Creates a markdown note with auto-detected `[[wiki-links]]`.
- `argo-vault-bridge read-index`: Reads `_index.md` as the map of company knowledge.
- `argo-vault-bridge handover <turnId> <fromAgent> <toAgent> <summary>`: Records turn-by-turn handover artifacts.

## Vault Layout
- `~/.argo/vault/notes/`: Curated agent knowledge notes.
- `~/.argo/vault/conversations/`: Turn handovers.
- `~/.argo/vault/_index.md`: Central knowledge graph entrypoint.
