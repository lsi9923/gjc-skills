---
name: orca-coordinator
description: "Bridge GJC with Orca ADE native multi-agent orchestration for task dispatching, peer message exchange, thinking threads, decision gates, and worktree terminals."
---

# Orca ADE Multi-Agent Orchestrator

## Overview
Orca is a multi-agent ADE environment where agents run in dedicated terminals and worktrees.
GJC agents use `orca-bridge` or `orca orchestration` CLI to coordinate across agents.

## Core Commands
- `orca-bridge list-runs`: Lists active orchestration runs.
- `orca-bridge create-run "<objective>"`: Starts an autonomous multi-agent swarm run.
- `orca-bridge create-task "<spec>"`: Decomposes tasks into the Orca task DAG.
- `orca-bridge send <toHandle> <subject> <body>`: Sends peer-to-peer messages/thoughts.
- `orca-bridge check [--wait]`: Listens for replies, questions, and worker status.
- `orca-bridge resolve-gate <gateId> <decision>`: Resolves approval/decision gates.

## Autonomous Workflow
1. Leader initializes or binds an Orca Run.
2. Leader breaks down features into tasks and creates them in the DAG.
3. Workers receive injected dispatch preambles and send lifecycle events (`status`, `worker_done`, `escalation`).
4. Agents think and communicate via `send` and `reply` threads.
