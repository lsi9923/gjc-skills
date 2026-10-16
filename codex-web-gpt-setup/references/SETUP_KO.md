# Codex Web GPT / GPT-6 High / 여러 에이전트 설정

이 패키지는 Windows CMD에서 같은 설정을 다시 적용하는 도구다. Node.js 22 이상, Codex CLI, Python 3.11 이상이 필요하다. omo 설정에는 `omo.exe` Native 실행기와 ChatGPT 로그인이 필요하다. GJC 설정에는 GJC 실행기와 `openai-codex` 로그인이 필요하다. 필요한 프로그램이 없으면 종료 코드 2로 원인을 알려준다. 패키지는 새 npm/Python 의존성을 설치하지 않는다.

## 현재 적용하는 설정

| 항목 | 값 | 저장/적용 위치 |
|---|---|---|
| 검증한 앱 | Codex Web GPT 6.1.7, 기존 6.1.3에서 업데이트 | `%LOCALAPPDATA%\Programs\Codex Web GPT` |
| Codex 기본/역할 모델 | `chatgpt-web/gpt-6-sol` | `%USERPROFILE%\.codex\config.toml`, `agents\*.toml` |
| Codex 추론 | `high` | `model_reasoning_effort` |
| Codex Responses 연결 | `http://127.0.0.1:17841/v1` | `openai_base_url` |
| 연결 모드 | Full, 자동 브라우저 조작 | `.codex-chatgpt-web\config.json` |
| 도구 커넥터 | 이 PC는 `Codex Native2` | 기존 터널/키 재사용 |
| 서브 에이전트 전송 | `compatibility-v1`, 깊이 2 | 앱이 관리하는 Codex 통합 설정 |
| omo 기본/역할/카테고리 모델 | `chatgpt-subscription/gpt-6-sol` | `.omo\agent\settings.json`, `.omo\omo.jsonc` 또는 `.json` |
| omo 메인 프로필 | `model_profile: chatgpt-subscription/gpt-6-sol:high` | 시작 시 플러그인의 추천 프로필이 모델을 바꾸지 않도록 고정 |
| omo 추론 | `high`, 역할/카테고리도 `reasoning: high` | 추천 모델 자동 변경을 끄고 GPT-6 Sol 유지 |
| GJC 기본/역할 모델 | `openai-codex/gpt-6-sol:high` | `.gjc\agent\config.yml`의 `modelRoles`, `task.agentModelOverrides` |
| GJC 추론 | `defaultThinkingLevel: high` 및 모델 선택의 `:high` | 자동 모델 프로필 해제, `task.autorouting.enabled: false` |
| GJC 공급자 우선순위 | `openai-codex` | GJC 자체 ChatGPT 구독 연결 사용 |
| 언어 | 한국어 | 앱 상태 |
| Windows 자동 시작 | 켬 | 앱의 정식 자동 시작 API |
| 창 닫아도 계속 실행 | 켬 | 앱 상태 |
| 응답 중 브라우저 표시 | 켬 | 앱 상태 |
| 도구 자동 승인 | 끔 | 기존 값을 확인, 켜져 있으면 프리셋 적용 중단 |
| Bigger Context | 켬 | 계정/모델이 지원하는 범위에서만 동작 |
| 스킬 파일 첨부 | 끔, 인라인 스킬 사용 | 앱 상태 |
| 요청마다 새 대화 | 끔 | 기존 대화 재사용 |
| ChatGPT 대화 저장 | 끔 | Temporary Chat |
| Zero Risk Pro | 끔 | 현재 계정은 Pro/Extra High 미지원 |

설정 당시 런타임의 `contextWindow` 값은 256000이었다. 실제 지원 컨텍스트는 모델·계정에 따라 달라지며 이 숫자를 임의로 덮어쓰지 않는다. GPT-6 Sol은 Medium/High, Instant는 Low를 광고했다. 실제 사용 가능한 모델은 매번 인증된 모델 목록으로 확인한다.

앱 버전과 업데이트 이력은 [공식 프로젝트 릴리스](https://github.com/miuuyy/codex-chatgpt-web/releases/tag/v6.1.7)를 참고한다. `update`는 실행 시 최신 정식 Windows x64 릴리스를 조회하고 GitHub의 SHA256 digest와 설치 파일을 비교한다. 앱을 정상 종료한 후 설치한다. 강제 종료하지 않는다.

## 처음 등록하기: CMD에 입력

압축을 푼 `chatgpt-web-skill` 폴더의 `install.cmd`를 실행하면 공용 도구 및 스킬을 설치한다. 명령 프롬프트(CMD)에서 해당 폴더로 이동한 다음 실행한다.

```bat
install.cmd
```

실제 실행 파일은 `%LOCALAPPDATA%\CodexWebGPTSetup\skill`에 복사한다. `%USERPROFILE%\.local\bin\codex-web-gpt.cmd`, `omo-gpt6.cmd`, `gjc-gpt6.cmd`를 만든다. `.local\bin`이 PATH에 없으면 아래처럼 전체 경로로 실행하면 된다. 전역 PATH를 강제로 변경하지 않는다.

```bat
"%USERPROFILE%\.local\bin\codex-web-gpt.cmd" setup --agents all
"%USERPROFILE%\.local\bin\codex-web-gpt.cmd" verify --omo --gjc
```

정상 결과는 `SETUP_OK`, 검증 JSON의 `nativeCodexHigh: true`, `omoNativeHigh: true`, `gjcNative: true`다. 실제 응답은 `CODEX_GPT6_HIGH_OK`, `OMO_GPT6_HIGH_OK`, `GJC_GPT6_HIGH_OK`다. 종료 코드 0이면 성공이다. GJC JSON 응답은 추론 단계 필드를 노출하지 않으므로 GJC High는 설정 감사로 확인하며, 실제 응답에서는 공급자와 GPT-6 모델을 확인한다.

## 명령

CMD에서 다음 명령을 실행한다. PATH에 없으면 `codex-web-gpt`를 위의 전체 경로로 바꾼다.

```bat
codex-web-gpt status
codex-web-gpt models
codex-web-gpt setup --agents all
codex-web-gpt agents codex
codex-web-gpt agents omo
codex-web-gpt agents gjc
codex-web-gpt agents all
codex-web-gpt verify --omo --gjc
codex-web-gpt verify-gjc
codex-web-gpt update
codex-web-gpt login
codex-web-gpt run
omo-gpt6
gjc-gpt6
```

`setup --agents all`은 기존 인증과 터널을 재사용하고 앱 설정·Codex 역할·omo 역할·설치된 GJC 역할을 적용한다. GJC가 없으면 해당 부분만 건너뛰며 `agents gjc`와 `verify --gjc`는 GJC 설치를 요구한다. `agents`는 역할/모델 설정만 적용한다. `run`은 Web GPT 모델로 Codex CLI를 시작한다. `omo-gpt6`, `gjc-gpt6`는 각각 GPT-6 High로 시작한다. 기존 세션은 저장된 모델이나 프로젝트 설정이 우선할 수 있으므로 새 세션으로 시작한다.

`--project`는 현재 작업 폴더의 `.omo/omo.jsonc` 또는 `.json`에도 역할/카테고리를 적용한다. 기존 다른 프로젝트의 설정은 자동 수정하지 않는다. Codex 쪽은 기본 사용자 홈을 사용하며, 다른 `CODEX_HOME`으로 연결한 경우 `setup`이 중단된다.

이 PC에서 수행한 검사와 검증하지 않은 환경은 [VERIFICATION_KO.md](VERIFICATION_KO.md)에 정리했다.

## 새 PC 또는 인증이 없을 때

앱이 없으면 `setup`이 정식 Windows x64 앱을 다운로드하고 검증 후 설치한다. 로그인은 사용자가 앱의 로그인 화면에서 완료해야 한다. CMD에서 비밀번호를 받거나 브라우저 인증을 우회하지 않는다.

```bat
codex-web-gpt login
codex login
```

로그인 후 Full 연결용 터널 ID와 Tunnels Read+Use 키 파일이 필요하다. 아직 만든 적이 없다면 앱의 MCP 안내에서 발급/연결한다. 이미 있는 키 파일로 연결할 때는 다음 명령을 쓴다. `실제_터널_ID`를 자신의 ID로 바꾼다. 키 값은 명령에 넣지 않는다.

```bat
codex-web-gpt setup --tunnel-id 실제_터널_ID --runtime-key-file "%USERPROFILE%\runtime-key.local.txt" --agents all
```

omo 로그인은 `omo.exe`를 실행한 뒤 `/login chatgpt-subscription`을 사용한다. 이 패키지는 omo 설치 프로그램 자체를 설치하거나 다른 계정의 인증을 복사하지 않는다.

## 여러 실행기와 서브 에이전트

| 실행기 | 설치한 설정 스킬 | 모델 연결 |
|---|---|---|
| Codex | `.codex/skills/codex-web-gpt-setup` | Web GPT 모델·High, 사용자 역할 TOML 모두 설정 |
| omo Native | `.omo/agent/settings.json`의 `skills`에 절대 경로 등록 | 자체 ChatGPT 구독 모델·High, 런타임에서 발견한 모든 역할/카테고리 설정 |
| GJC | `.gjc/agent/skills/codex-web-gpt-setup` | 자체 `openai-codex` 모델·High, 기본 6개 역할과 내장/사용자 서브 에이전트 선택 설정 |
| Claude Code | `.claude/skills/codex-web-gpt-setup` | 공용 CMD 도구 호출 |
| Gemini CLI | `.gemini/skills/codex-web-gpt-setup` | 공용 CMD 도구 호출 |
| OpenCode | `.config/opencode/skills/codex-web-gpt-setup` | 공용 CMD 도구 호출 |
| 공용 Agent Skills | `.agents/skills/codex-web-gpt-setup` | 같은 설정 도구 제공 |

omo와 GJC에서는 `/skill:codex-web-gpt-setup`으로 부른다. omo는 프롬프트 첫머리의 `$codex-web-gpt-setup` 또는 명시적인 스킬 파일로 실행할 수도 있다. 셸 명령을 omo/GJC 대화창에 붙이는 대신 스킬을 호출해 설정을 요청한다.

```bat
omo.exe --skill "%LOCALAPPDATA%\CodexWebGPTSetup\skill\SKILL.md"
```

Codex 역할들의 프롬프트와 도구 제한은 유지하며 top-level `model`과 `model_reasoning_effort`만 수정한다. Windows에서 상대 경로 문자열로 저장된 `yd_*.toml` 링크는 `.agents/skills` 또는 `.codex/skills`의 실제 원본으로 복구한다. 원본이 없거나 TOML이 잘못되면 전체 역할 변경을 시작하지 않는다. 모든 역할을 같은 High로 맞추므로 저비용 탐색 역할도 High를 사용한다.

omo 기본 역할과 카테고리 이름은 설치된 Native 런타임에서 발견한다. 사용자 정의 역할도 포함한다. 기존 모델 체인을 단일 GPT-6 High 선택으로 맞추며 프롬프트/도구/비활성화 플래그는 유지한다. 명시적인 실행 시 모델 지정, 프로젝트 설정, 이미 실행 중인 세션은 전역 기본값보다 우선할 수 있다.

GJC는 공식 `gjc config get/set/reset` 명령으로 YAML 설정을 보존하며 저장한다. `default`, `executor`, `architect`, `planner`, `critic`, `image`와 기존 역할 키를 GPT-6 High로 맞춘다. 내장 서브 에이전트 4개와 사용자 `agents/*.md`의 이름을 `task.agentModelOverrides`에 등록하며 에이전트 프롬프트와 도구 목록을 수정하지 않는다. 별도의 `thinking` 또는 `thinkingLevel`이 High 외 값으로 고정돼 있으면 오류로 알린다. `--project`를 주면 현재 프로젝트의 GJC 에이전트 이름도 포함한다. 실행 중인 GJC 및 기존 세션에는 즉시 반영하지 않으며 새 세션에서 사용한다.

GJC 스킬 설치 확인은 CMD의 `gjc skills discover --query codex-web-gpt-setup --json`으로 가능하다. 이 PC의 GJC 0.18.7 모델 목록에서 `openai-codex/gpt-6-sol`과 High 지원을 확인했다. 로그인은 GJC 자체 로그인 메뉴에서 완료하며 인증 파일을 배포 패키지에 복사하지 않는다.

GJC만 검사할 때는 `codex-web-gpt verify-gjc`를 쓴다. Web GPT 앱이 꺼져 있어도 GJC 설정과 실제 응답만 따로 검사한다. 정상 결과는 `gjcNative: true`이며 응답 증거는 개인 `reports/gjc-response.json`에 저장한다.

다른 실행기의 자체 모델을 GPT-6로 바꾸는 것은 이 공용 스킬 설치와 별개다. 특히 Codex Web GPT의 로컬 서버는 native turn metadata와 권한 정보를 요구하므로 일반 OpenAI-compatible 공급자 URL만 바꿔서 omo/Claude/Gemini에 연결하면 안 된다. 기존 omo `codex-web-gpt` 공급자의 오래된 모델 행은 선택하지 않으며 자체 `chatgpt-subscription`을 사용한다.

스킬 위치 참고: [Claude Code](https://code.claude.com/docs/en/skills), [Gemini CLI](https://github.com/google-gemini/gemini-cli/blob/main/docs/cli/using-agent-skills.md), [OpenCode](https://opencode.ai/v2/docs/skills). omo의 실제 `--skill` 지원과 설정 키는 이 PC의 `omo --help` 및 설치된 Native 런타임 문서를 확인했다.

## 파일·백업·오류

인증 토큰은 `.codex/auth.json`에서 모델 조회용으로 내부에서만 읽는다. Web GPT 제어 토큰과 터널 키는 앱이 관리한다. 런타임 경로·키·로그인 프로필 전체를 배포 패키지에 넣지 않는다.

백업은 `%LOCALAPPDATA%\CodexWebGPTSetup\backups`, 증거는 같은 폴더의 `reports`에 저장한다. 백업은 민감한 설정을 포함할 수 있으므로 개인 폴더에 보관한다. 도구가 출력한 해당 백업 경로로 복원한다.

```bat
codex-web-gpt restore "도구가_출력한_백업_폴더"
```

복원은 기록된 기존 설정 파일만 복사한다. 새로 등록한 스킬이나 앱은 삭제하지 않는다. 앱 상태 백업을 복원할 때는 앱을 정상 종료한 상태에서 실행한다.

| 종료 코드 | 의미 | 다음 조치 |
|---|---|---|
| 0 | 작업 성공 | 실제 검증 보고서 확인 |
| 1 | 검사/설치/연결 실패 | 앱 Activity에서 실패 원인 확인 |
| 2 | 로그인·실행기·키·계정 지원 등 전제 조건 부족 | 메시지가 지정한 전제 조건 해결 후 재실행 |
| 3 | 활성 요청 존재 | 요청 완료 후 재실행 |

`/healthz`가 정상이고 모델 목록이 HTTP 200이어도 응답 생성 성공은 별도 검사한다. 기존 터널이 로컬에서 정상이라는 것만으로 ChatGPT 커넥터 연결을 완료 처리하지 않고 앱의 실제 `verifyMcp` 결과를 확인한다. 버전 변경 후 오류가 생기면 `status`, `models`, `verify --omo --gjc` 순서로 실패 지점을 좁힌다.
