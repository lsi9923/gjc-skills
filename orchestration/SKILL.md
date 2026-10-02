---
name: orchestration
description: "사용자가 '오케스트레이션으로 작업해', '오케스트레이션 모드로 해줘', '5개 모델로 분담해서 작업해', '오케스트레이션 구현', '/skill:orchestration'을 지시했을 때 반드시 이 스킬을 활성화하여 실행. 5대 핵심 모델(Claude Opus 4.8 Default, GPT-5.6 Sol Planner, GPT-5.6 Terra Executor, Gemini 3.8 Flash Tiered Architect, Gemini 3.8 Flash Tiered Critic) 협업 파이프라인을 자동 가동하여 기획-설계-구현-독립비평-최종검증을 완수한다."
---

# 5-Role Multi-Vendor Orchestration Protocol

사용자가 **"오케스트레이션으로 작업해"** 또는 동등한 협업 지시를 내렸을 때, GJC의 5대 역할 전문 모델들을 `task` 서브에이전트 시스템으로 유기적으로 연결하여 완전한 구현 및 검증을 달성하는 전담 스킬이다.

---

## 1. 5대 모델 역할 및 책임 명세 (Daily Multi-Vendor Matrix)

| 역할 | 담당 모델 (Selector) | Thinking | 핵심 책임 |
| :--- | :--- | :--- | :--- |
| **Default (메인 지휘관)** | `anthropic/claude-opus-4-8:high` | `high` | 세션 총괄, 요구사항 접수, 컨텍스트 전달, 최종 통합 빌드/검증 및 사용자 보고 |
| **Planner (기획/로드맵)** | `openai-codex/gpt-5.6-sol:high` | `high` | 작업 분해, 의존성 트리 수립, 단계별 목표 및 Acceptance Criteria 정의 |
| **Architect (구조 분석/보안)** | `google-antigravity/gemini-3.8-flash-tiered:high` | `high` | 1M 대용량 컨텍스트 기반 코드베이스 영향도 분석, 아키텍처 정합성·보안 검토 |
| **Executor (코드 구현)** | `openai-codex/gpt-5.6-terra:high` | `high` | 파일 단위의 정밀한 소스 코드 작성, 리팩토링, 버그 수정 및 기능 구현 |
| **Critic (독립 비평/게이트)** | `google-antigravity/gemini-3.8-flash-tiered:high` | `high` | 구현 결과물 독립 대조 검증, 엣지케이스·사이드이펙트 적발 및 품질 승인 |

> **동작 전제**: `~/.gjc/agent/models.yml`의 `daily` 프로필과 `~/.gjc/agent/config.yml`의 `modelProfile.default: daily` 설정에 의해 각 에이전트 호출 시 위 모델들이 자동 바인딩된다.

---

## 2. 오케스트레이션 실행 파이프라인 (Step-by-Step)

사용자가 작업을 지시하면 메인 지휘관(Default Claude)은 단일 모델로 대충 처리하지 않고, 아래 5개 역할을 순차/병렬 연계하여 실행한다.

```
[Default 접수] ──> [1. Planner 분해] ──> [2. Architect 검토] ──> [3. Executor 구현] ──> [4. Critic 비평] ──> [Default 최종 검증]
```

### Step 1. [Default] 요구사항 접수 및 컨텍스트 바운딩 (Claude Opus 4.8 High)
- 사용자의 과업 목표(Goal)와 필수 제약조건(Constraints)을 명확히 정리한다.
- 현재 작업 디렉토리의 핵심 파일 구조를 신속히 파악한다.

### Step 2. [Planner] 작업 기획 및 태스크 분해 (GPT-5.6 Sol High)
- `task` 도구를 통해 `planner` 에이전트를 호출한다:
  ```json
  task({
    "agent": "planner",
    "tasks": [{
      "id": "PhasePlan",
      "description": "작업 분해 및 로드맵 수립",
      "assignment": "# Goal\n...\n# Constraints\n...\n# Target\n..."
    }]
  })
  ```
- 구체적인 파일 목록, 구현 단계, 완료 판정 기준(Acceptance Criteria)을 도출한다.

### Step 3. [Architect] 1M 컨텍스트 아키텍처 & 영향도 분석 (Gemini 3.8 Flash Tiered High)
- `task` 도구를 통해 `architect` 에이전트를 호출한다:
  ```json
  task({
    "agent": "architect",
    "tasks": [{
      "id": "ArchReview",
      "description": "아키텍처 및 안전성 분석",
      "assignment": "# Review Target\n...\n# System Context\n..."
    }]
  })
  ```
- 대용량 컨텍스트를 활용하여 기존 시스템과의 충돌, 패턴 일관성, 보안 취약점 여부를 점검하고 권고안을 확정한다.

### Step 4. [Executor] 정밀 코드 구현 (GPT-5.6 Terra High)
- Planner의 계획과 Architect의 구조 권고안을 취합하여 `executor` 에이전트에게 구현을 위임한다:
  ```json
  task({
    "agent": "executor",
    "tasks": [{
      "id": "CodeImplementation",
      "description": "코드 파일 생성 및 수정",
      "assignment": "# Implementation Target\n...\n# Plan & Architecture Guidelines\n..."
    }]
  })
  ```
- 대상 파일들을 직접 수정/작성하고 완료 내역을 수집한다. (서브에이전트는 전체 빌드를 돌리지 않고 코드 수정만 전담)

### Step 5. [Critic] 독립 결함 검증 및 게이트 심사 (Gemini 3.8 Flash Tiered High)
- 구현이 끝나면 `critic` 에이전트를 호출하여 결과물을 독립 비평한다:
  ```json
  task({
    "agent": "critic",
    "tasks": [{
      "id": "QualityCritic",
      "description": "독립 결함 및 엣지케이스 검증",
      "assignment": "# Review Target\n변경된 파일 및 코드\n# Acceptance Criteria\n..."
    }]
  })
  ```
- **판정**:
  - `OKAY`: 통과.
  - `ITERATE` (결함 발견): 발견된 블로커/누락점을 정리하여 Executor에게 즉시 재수정 지시.

### Step 6. [Default] 최종 통합 검증 및 결과 납품 (Claude Opus 4.8 High)
- Critic 통과 후, Default 오케스트레이터가 프로젝트 전체의 빌드, 테스트, 린트(`npm test`, `cargo test`, `bun test` 등)를 1회 최종 검증한다.
- 5개 모델의 기여 결과와 최종 검증 통과 증거를 사용자에게 간결하고 명확하게 보고한다.

---

## 3. 트리거 발화 예시
- `"오케스트레이션으로 작업해"`
- `"오케스트레이션 모드로 해줘"`
- `"5개 모델로 분담해서 작업해"`
- `"오케스트레이션 모드로 구현해"`
- `/skill:orchestration <작업 내용>`
