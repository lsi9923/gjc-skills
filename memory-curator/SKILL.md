---
name: memory-curator
description: "Canonical two-layer memory curator with G1-G5 governance clauses (trust gate, scope routing, redaction, typed supersede with retained pointers, knowledge homeostasis) and memory ticketing."
---

# Two-Layer Memory Curator

## Core Principle
Agents emit structured memory events. The Memory Curator owns durable memory writes.

## Governance Clauses (G1 - G5)
- **G3 Redaction**: Quarantine any memory containing secrets, keys, credentials, or PII before any other gate.
- **G2 Scope Routing**: Separate ephemeral session chatter from project/global memory.
- **G1 Trust Gate**: Low-trust claims go to quarantine, never active memory.
- **G4 Typed Supersede**: Retain full pointer chains (`supersedes: [id1, id2]`). Never silently overwrite.
- **G5 Knowledge Homeostasis**: Prune stale contradicted facts, preserve stable invariants.

## Memory Ticket Contract
- Queue memory events with: `projectId`, `sourceAgent`, `taskId`, `idempotencyKey`, `candidates` (max 20).
- Deterministic fast pass handles redaction & dedup; deep curation handles promotion & conflict resolution.
