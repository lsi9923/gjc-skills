---
name: ontology-engine
description: "Local-first GraphRAG ontology runtime with offline Model2Vec multilingual embeddings, Korean document parser (HWP/HWPX), entity resolution, and governed experience memory."
---

# Local Ontology & GraphRAG Engine

## Overview
Hephaestus Ontology Runtime provides fast, local-first GraphRAG search, offline multilingual vector embeddings (Model2Vec INT8), entity relation extraction, and Korean document model support (HWP5 and HWPX) without calling external APIs.

## Commands
- `ontology query "<question>" [--db <path>]`: Performs hybrid RRF lexical + semantic vector GraphRAG query.
- `ontology ingest <file_or_dir> [--scope <internal|public|private>]`: Parses and ingests documents, extracting entities and chunks.
- `ontology experience ingest "<summary>" --agent "<agent_id>"`: Ingests agent experience projections with salience and provenance.
- `ontology experience query "<query>" --agent "<agent_id>"`: Queries agent-scoped working and episodic memory.
- `ontology verify`: Verifies database integrity and ontology invariants.
- `ontology gui`: Launches a local interactive ontology visualizer.

## Offline Embeddings
Uses local quantized INT8 Model2Vec embeddings (`potion-multilingual-128M-int8`) for fast 256-dimensional semantic similarity.
Zero network overhead and zero token cost.
