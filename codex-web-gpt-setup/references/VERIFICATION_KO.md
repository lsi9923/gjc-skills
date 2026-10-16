# 이 PC에서 확인한 결과 (2026-10-09)

- 원본 앱 6.1.3 → 6.1.7 업데이트, 브라우저 인증·모델 목록·도구 커넥터 검사 통과.
- CMD `install.cmd`: 도구와 공용 스킬 설치 성공, 반복 설치 성공.
- CMD `codex-web-gpt setup --agents all`: 성공. Codex 역할 190개를 실제 TOML로 검증하고 GPT-6 High로 설정했다. 잘못된 링크 문자열 16개를 `.agents/skills`의 원본으로 복구했다.
- 같은 설정을 재실행했을 때 Codex 역할 변경 파일 수 0: 재실행으로 설정을 중복 추가하지 않는다.
- omo Native: 역할 7개, 카테고리 10개를 GPT-6 High로 맞췄다. 시작 시 기본값을 덮어쓰는 모델 프로필을 확인해 `model_profile`에도 GPT-6 High를 지정했다.
- Codex 실제 응답: `CODEX_GPT6_HIGH_OK`.
- omo 실제 응답: `OMO_GPT6_HIGH_OK`. 모델을 실행 인수로 지정하지 않은 검사에서 실제 `provider=chatgpt-subscription`, `model=gpt-6-sol`, `thinkingLevel=high`를 확인했다.
- omo `explore` 서브 에이전트 디스패치: 런타임의 `resolved_model`이 `chatgpt-subscription/gpt-6-sol`, reasoning `high`임을 확인했다. 이 디스패치 검사는 모델 선택을 검증하며, 모든 역할의 개별 응답 생성까지 반복 실행한 것은 아니다.
- GJC 0.18.7: 기본 역할 6개 및 서브 에이전트 7개(executor, architect, planner, critic, analyst, coder, jarvis)의 모델 선택을 `openai-codex/gpt-6-sol:high`로 설정했다. YAML 설정은 GJC 자체 config 명령으로 저장한다. 에이전트 프롬프트와 도구 목록은 유지한다.
- GJC 기본값 응답 검사: 모델/추론 실행 인수 없이 `GJC_GPT6_HIGH_OK` 응답과 `provider=openai-codex`, `model=gpt-6-sol`을 확인했다. GJC JSON은 `thinkingLevel` 필드를 노출하지 않아 High는 설정 감사로 확인했다. 서브 에이전트 7개의 개별 응답까지 실행한 검사는 아니다.
- Node 회귀 검사 5개, Python 회귀 검사 4개, 스킬 형식 검사 통과. 프롬프트 안의 TOML 예제·중첩 프로필·도구 제한 보존, 잘못된 역할의 변경 중단, JSONC 문자열/URL 보존, Unicode 경로에서 반복 설치, GJC 기존/사용자 역할 모델 체인 교체와 재실행을 검사했다.

원본 설치 기록과 새 검사 보고서는 개인 로컬 데이터 폴더에 보관했다. 재사용 패키지에는 로그인 토큰·터널 키·개인 설정 백업·대화 로그를 넣지 않았다.

새 PC에서 로그인부터 시작하는 설치와 미래 릴리스의 실제 업그레이드는 이 PC의 기존 인증 환경과 별개다. 최초 로그인·터널 발급에는 사용자 계정 인증이 필요하다. 이 패키지의 최신 설치 파일 조회·SHA256 검사·정상 종료 경로는 제공하지만, 이를 위해 기존 앱을 삭제하고 새 PC 상태를 만들지는 않았다.

Windows omo Native는 시작 시 Bun child-reaper 안내를 출력한다. 본 검증의 모델/응답 실패는 아니며, 이 패키지는 omo 런타임 내부를 수정하지 않았다.
