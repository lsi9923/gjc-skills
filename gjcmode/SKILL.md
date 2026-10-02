---
name: gjcmode
description: >-
  gjcmode Orchestration Mode (Orca) — Supervised multi-agent orchestration where
  Codex is coordinator and workers are Codex/implement + Claude/design.
  Use when the user runs /gjcmod, /gjcmode, says gjcmode, orchestrate, 조율, or asks
  to run Orca gjc orchestration mode. Reads $HOME/.orca/gjc/PLAYBOOK.md.
metadata:
  short-description: "gjcmode Orca multi-agent orchestration"
  aliases: ["gjcmod", "gjcmode", "조율"]
---

# gjcmode Orchestration Mode (Orca) — Global

Codex = **coordinator**. Workers = **Codex/implement + Claude/design**.
When workers finish, the coordinator produces a **FINAL** synthesis.

Mode type: **supervised orchestration** (coordinator waits for `worker_done`). Not a fire-and-forget handoff.

- 엔진: `orchestration` 스킬 (`orca orchestration …`)
- 원본 규칙: `$HOME/.orca/gjc/PLAYBOOK.md` (`C:\Users\imda0\.orca\gjc\PLAYBOOK.md`)

## 시작 전 확인

```bash
orca status --json
orca orchestration task-list --json
```

## 역할

| 역할 | 에이전트 | 할 일 |
|------|----------|--------|
| **팀장** | Codex / GJC | 역할별 일 쪼개기, 배정, 대기, FINAL 정리 |
| **구현 · 코딩 (`implement`)** | `codex -m gpt-5.6-sol -c model_reasoning_effort="xhigh"` | 코드 작성·수정, 테스트 후 `worker_done` |
| **디자인 · UI/UX (`design`)** | `claude --model claude-sonnet-5` | 화면/플로우/컴포넌트·토큰 설계 |

## 팀장 루프
1. **일 쪼개기**: 2~6개 독립 태스크 (`[role=implement|design|backend-design|…]`)
2. **일 등록**: `orca orchestration task-create --spec "[role=...] ..." --json`
3. **실무 창 띄우기 & 배정**: `orca terminal create --worktree active ...` → `orca terminal wait` → `orca orchestration dispatch --task <id> --to <handle> --inject --json`
4. **기다리기**: `orca orchestration check --wait --types worker_done,escalation,decision_gate --timeout-ms 900000 --json`
5. **FINAL 정리**: Summary, Per-task results, Decisions, Files changed, Risks & next steps.
