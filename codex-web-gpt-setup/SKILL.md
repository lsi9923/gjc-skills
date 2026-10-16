---
name: codex-web-gpt-setup
description: Windows CMD에서 Codex Web GPT 설치·업데이트·GPT-6 High 연결을 재현하고 Codex, omo Native, GJC의 메인·서브 에이전트 설정을 적용하거나 진단한다. Claude Code, Gemini CLI, OpenCode에서는 이 공용 설정 도구를 호출한다.
---

# Codex Web GPT / 여러 에이전트 설정

웹 응답 끊김·긴 대기·메시지 충돌을 고치는 요청은 `status` → `repair-web` → `verify-web` 순서로 실행한다. `repair-web`은 설정을 백업하고 Bigger Context를 끄며 60,000 토큰에서 대화를 압축하도록 설정한다. 모델과 권한은 유지한다. `verify-web`은 새 응답, 같은 채팅에서 설치된 Codex 앱 목록 조회, 후속 응답을 실제 검증한다. 조회 명령에 기존 허용 규칙이 없는 PC에서는 셸 검사가 차단될 수 있으므로 실패를 그대로 보고하며 권한을 넓히지 않는다. High 검사에는 `verify-web --high`, 중단된 검사의 성공 결과 재사용에는 `--continue`를 쓴다. 결과는 `reports/web-verification-medium.json` 또는 `web-verification-high.json`에 저장한다. 활성 요청이 있으면 변경하지 않는다. 모델 역할 감사 실패는 웹 연결 실패와 구분한다. 일반 `setup`은 Bigger Context를 끈 상태가 기본이며, 확장하려고 명시한 경우에만 `--bigger-context`를 쓴다.

먼저 `scripts/codex-web-gpt.cmd status`를 실행한다. 설정 복원은 `setup --agents all`, 검증은 `verify --omo --gjc`, 최신 앱 업데이트는 `update`를 사용한다. CMD 진입점과 상대 경로는 이 스킬 디렉터리를 기준으로 계산한다. GJC가 설치되지 않았으면 `all`은 GJC를 건너뛰며, 검증에서도 `--gjc`를 생략한다.

설정 변경 요청에는 다음 순서로 실행한다.

1. `scripts/codex-web-gpt.cmd setup --agents all`로 연결과 각 에이전트 설정을 적용한다.
2. `scripts/codex-web-gpt.cmd verify --omo --gjc`로 모델 목록, 연결, 실제 Codex·omo·GJC 응답을 검증한다.
3. 종료 코드와 실제 응답을 읽고 통과한 범위만 보고한다. 증거는 사용자 로컬 데이터의 `CodexWebGPTSetup/reports`에 남는다.

`agents all`은 Codex 역할 TOML, omo 기본 모델·역할·카테고리 및 설치된 GJC의 기본 모델·역할 선택을 설정한다. GJC만 적용하려면 `agents gjc`를 쓴다. 역할별 프롬프트와 도구 권한을 유지한다. omo는 `chatgpt-subscription/gpt-6-sol`, Codex는 `chatgpt-web/gpt-6-sol`, GJC는 `openai-codex/gpt-6-sol:high`를 쓴다. 실행기별 요청 형식이 다르므로 일반 Responses 공급자를 Codex 전용 로컬 서버로 바꾸지 않는다.

스킬과 명령 도구는 공용이고 모델 설정은 각 실행기의 설정 파일에 따로 저장한다. omo 또는 GJC 대화창에서는 `/skill:codex-web-gpt-setup`으로 호출한다. `codex-web-gpt ...`, `omo-gpt6`, `gjc-gpt6` 명령은 Windows CMD에서 실행한다. 현재 대화가 계속 실행 중이면 설정 후 새 세션에서 반영한다.

기존 검증 범위와 한계는 [references/VERIFICATION_KO.md](references/VERIFICATION_KO.md)를 참고한다. 재실행한 경우 현재 도구 출력이 이전 기록보다 우선한다.

Claude/Gemini/OpenCode에서 이 스킬을 읽는 것은 공용 CMD 도구를 사용하는 것이다. 해당 실행기의 자체 모델을 GPT-6로 교체한 것으로 보고하지 않는다. 지원 경로와 모든 설정은 [references/SETUP_KO.md](references/SETUP_KO.md)를 읽는다.

로그인 세션이 없으면 `login`을 실행하고 로그인 완료 후 같은 설정 명령을 다시 실행한다. 새 Full 연결에는 `setup --tunnel-id ID --runtime-key-file PATH --agents all`을 사용한다. 키는 파일에서만 읽으며 채팅, 명령 인수, 보고서에 키 값을 적지 않는다. 이미 저장된 키는 재사용한다.

활성 요청이 있으면 설정·업데이트를 중단하고 완료 후 재시도한다. 프로세스를 강제 종료하거나 인증/권한 검사를 우회하지 않는다. 오류가 나면 오류 코드와 어느 검증에서 실패했는지 보고한다. `restore BACKUP_DIRECTORY`는 사용자가 요청한 경우에만 실행한다.
