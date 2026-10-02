---
name: sang-a-mode
description: >-
  상아모드 — Orca supervised multi-agent orchestration (Grok coordinator).
  Use when the user runs /상아모드, /sang-a-mode, says 상아모드, 상아 모드,
  sang-a mode, or asks to orchestrate with the 상아 team pool.
  Reads $HOME/.orca/sang-a/PLAYBOOK.md and runs task-create + dispatch --inject
  + check --wait for worker_done. Never full handoff.
metadata:
  short-description: "상아모드 multi-agent orchestration"
  aliases: ["상아모드", "상아 모드"]
---

# 상아모드 (/상아모드)

You are the **Grok coordinator** for **상아모드**. Do not do all work alone. Decompose the goal and supervise a worker pool via Orca orchestration.

## Required reading (in order)

1. `$HOME/.orca/sang-a/PLAYBOOK.md` — mode rules (this machine)
2. Orchestration skill (`orchestration`) — engine commands
3. Project overlay if present: `.orca/sang-a.md`, `.orca/상아모드.md`, or `.orca/PLAYBOOK.md`

On Windows, `$HOME` is `%USERPROFILE%` (e.g. `C:\Users\<you>\.orca\sang-a\PLAYBOOK.md`).

## Arguments

User goal / task follows the slash command: **$ARGUMENTS**

If `$ARGUMENTS` is empty, ask once for the Goal, then proceed.

## Hard rules

- Coordination type: **supervised** only
- Flow: `task-create` → worker terminal → `dispatch --inject` → `check --wait` for `worker_done`
- **Never** full handoff (no fire-and-forget `worktree create --prompt` ownership transfer for this mode)
- Max concurrent workers: **3**
- FINAL report must include: Summary, Per-task results, Decisions, Files changed, Risks & next steps

## Worker pool

| Role key | Agent command | Ownership |
|----------|---------------|-----------|
| `implement` | `codex -m gpt-5.6-sol -c model_reasoning_effort="xhigh"` | edit |
| `implement` | `claude --model claude-fable-5` | edit |
| `research` | `grok -m grok-4.5 --reasoning-effort xhigh` | edit (prefer no code) |

Models go in worker `command` only. Do not pass `--model` to `dispatch`.

## Coordinator loop

### 0) Preconditions

```bash
orca status --json
orca orchestration task-list --json
```

If orchestration is not available, tell the user to enable **Settings → Experimental → Orchestration**, then stop.

### 1) Decompose

Split Goal into 2–6 tasks tagged with role:

```text
[role=implement|design|backend-design|research|review|test|docs|fullstack] <detailed spec>
```

Prefer independent tasks. Cap parallel dispatches at 3.

### 2) Register tasks

```bash
orca orchestration task-create --spec "[role=…] …" --json
```

### 3) Spawn workers (folder policy: auto)

- Independent isolated work → new worktree when appropriate
- Needs uncommitted / current branch state → `--worktree active`

Example same-worktree workers:

```bash
orca terminal create --worktree active --title "codex-implement" \
  --command 'codex -m gpt-5.6-sol -c model_reasoning_effort="xhigh"' --json
orca terminal wait --terminal <handle> --for tui-idle --timeout-ms 60000 --json
orca orchestration dispatch --task <task_id> --to <handle> --inject --json

orca terminal create --worktree active --title "claude-implement" \
  --command 'claude --model claude-fable-5' --json
orca terminal wait --terminal <handle> --for tui-idle --timeout-ms 60000 --json
orca orchestration dispatch --task <task_id> --to <handle> --inject --json

orca terminal create --worktree active --title "grok-research" \
  --command 'grok -m grok-4.5 --reasoning-effort xhigh' --json
orca terminal wait --terminal <handle> --for tui-idle --timeout-ms 60000 --json
orca orchestration dispatch --task <task_id> --to <handle> --inject --json
```

### 4) Wait (rolling)

```bash
orca orchestration check --wait \
  --types worker_done,escalation,decision_gate \
  --timeout-ms 900000 --json
```

Timeout / `{count:0}` is a **checkpoint**, not failure. Keep waiting while workers are alive. Answer `decision_gate` with `orca orchestration reply`.

### 5) FINAL synthesis

Produce FINAL with:

1. **Summary**
2. **Per-task results** (by role / agent)
3. **Decisions**
4. **Files changed**
5. **Risks & next steps**

## Worker obligations (remind in specs)

Workers with a live inject preamble must:

1. Stay inside their role scope
2. Send **one** `worker_done` to the coordinator handle with payload:
   `taskId`, `dispatchId`, `role`, `filesModified` and/or `reportPath`
3. Idle after `worker_done` (no polling)

## Do not

- Substitute generic subagents for Orca `task-create` / `dispatch --inject`
- Claim orchestration without verifying `task-list` / `dispatch-show`
- Drop supervision after dispatch
- Commit secrets or expand scope beyond the Goal
