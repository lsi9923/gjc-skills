---
name: crew-orchestrator
description: GJC 멀티모델 크루(클로드·코덱스·제미나이) 및 아르고(Argo) 데스크톱 크루 통합 오케스트레이션 스킬. 크루 현황 조회, 모델별 업무 자동 분담(task 위임), 아르고 파일 및 OS GUI(마우스/키보드) 제어.
---

# 크루 오케스트레이터 (Crew Orchestrator)

GJC 내부의 모델별 전담 크루(`jarvis`, `coder`, `analyst`)와 바탕화면의 아르고(`argo.lnk`) 데스크톱 크루 시스템을 유기적으로 연결하고 총괄 지휘하는 스킬이다.

---

## 1. 현재 등록된 3대 핵심 크루 (GJC 전역)

| 크루 이름 (Slug) | 기반 모델 (Engine) | 담당 역할 및 전문 분야 |
| :--- | :--- | :--- |
| **자비스 (`jarvis`)** | **Claude Opus 4.8** (`anthropic/claude-opus-4-8:high`) | 수석 기획, 요구사항 스펙 정립, 아키텍처 설계 및 비평(Critic) |
| **코더 (`coder`)** | **OpenAI Codex GPT-5.6 Luna** (`openai-codex/gpt-5.6-luna:xhigh`) | 풀스택 코드 작성, 버그 수정, 빌드, 리팩토링 및 테스트 |
| **애널리스트 (`analyst`)** | **Gemini 3.8 Flash High** (`google-antigravity/gemini-3.8-flash-high:high`) | 1M 컨텍스트 기반 대용량 로그 분석, 웹 리서치, WAF/캡챠 우회 |

---

## 2. 크루 현황 조회 요청 시 (`"크루 누구누구 있어?"`, `"크루 상태 확인해"`)

1. **GJC 에이전트 목록**:
   - `~/.gjc/agent/agents/*.md` 파일을 확인하여 현재 등록된 크루 명단, 모델, 역할을 깔끔한 표로 요약 보고한다.
2. **아르고(Argo) 연동 크루 목록**:
   - `C:\Users\imda0\AppData\Local\com.beyondworks.argo\workspaces\co-jt3l\agents\*.md`를 조회하여 현재 아르고 사내에 등록된 크루(예: 자비스 - `runner: claude, model: claude-fable-5-1`) 목록을 함께 표시한다.

---

## 3. 업무 분담 및 병렬 실행 (`task` 도구 연동)

사용자가 개발/분석/기획 업무를 요청하면 작업 성격에 맞게 적절한 크루에게 `task` 도구로 위임한다:

- **복잡한 아키텍처/기획/설계 검토**:
  ```json
  task({
    "agent": "jarvis",
    "tasks": [{ "id": "ArchitectureReview", "description": "설계 검토", "assignment": "..." }]
  })
  ```
- **실제 파일 수정/코드 구현/빌드**:
  ```json
  task({
    "agent": "coder",
    "tasks": [{ "id": "FeatureImplement", "description": "기능 구현", "assignment": "..." }]
  })
  ```
- **대용량 파일 분석/크롤링/시장 조사**:
  ```json
  task({
    "agent": "analyst",
    "tasks": [{ "id": "MarketAnalysis", "description": "데이터 수집", "assignment": "..." }]
  })
  ```

---

## 4. 아르고(Argo) 직접 조정 및 제어 가이드

가재는 아르고(Argo) 시스템을 **2가지 방식**으로 자유자재로 다룬다:

### 방식 A. 백엔드 파일 직통 제어 (가장 빠르고 정확)
- **새 크루 추가**: `C:\Users\imda0\AppData\Local\com.beyondworks.argo\workspaces\co-jt3l\agents\<slug>.md` 파일을 직접 작성하여 아르고 대시보드에 새 직원을 즉시 출근시킨다.
- **루틴 및 스케줄 등록**: 아르고 데이터베이스/JSON에 루틴 작업을 등록하여 크루가 정해진 시간에 스스로 돌게 만든다.
- **사내 메모/지시 주입**: 크루 전용 컨텍스트 폴더에 작업 문서를 작성해 전달한다.

### 방식 B. OS GUI 조작 (`orca computer` 마우스/키보드 제어)
- 아르고 데스크톱 앱(`C:\Users\imda0\AppData\Local\argo\app.exe`)이 켜져 있을 때:
  1. `orca computer get-app-state --app app --json`으로 아르고 창의 버튼/채팅창 요소 탐색
  2. `orca computer click --app app --element-index <ID>`로 채팅방 클릭 또는 결재 승인 버튼 클릭
  3. `orca computer type-text --app app --text "지시사항"`으로 크루 채팅창에 직접 메시지 입력 및 엔터
