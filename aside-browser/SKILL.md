---
name: aside-browser
version: 3
description: Read when you need a browser, or have to work across user's logged-in websites (e.g. Gmail, Slack, cloud consoles, etc.), or have to refer personal contexts like memory and browsing history.
---

# Aside

This file is only an entry point. You MUST run `aside guide` to read this skill’s actual instructions before using Aside, then follow them.

- If `aside` is not installed, ask the user for permission to install Aside CLI. After the user approves, run the macOS/Linux installer `curl -fsSL https://releases.aside.com/install.sh | bash`, then run `aside guide`.
- If `aside guide` is reported as an unknown command, your CLI is outdated. Run `aside --update`, then run `aside guide` again.
- If a newer CLI version is available, the guide may be outdated. Always run `aside --update`, then run `aside guide` again before continuing.

If installation or an update fails, report the error instead of guessing the CLI usage.

## Troubleshooting & Window Recovery (재부팅 후 창 없음 대응)
- **증상**: 재부팅 후 OmO 또는 브라우저 조작 에이전트가 `Aside u0 프로필에 브라우저 창이 없음` 오류로 조작 불가한 경우.
- **원인**: Aside 프로세스는 백그라운드에 떠 있으나 메인 GUI 창(`MainWindowTitle`)이 없음.
- **해결**: PowerShell에서 아래 명령어로 메인 창을 직접 실행하여 띄운 뒤 REPL에 재접속한다:
  ```powershell
  Start-Process 'C:\Program Files\Aside\Application\Aside.exe'
  ```
- **확인**: 메인 창(`MainWindowTitle`)이 정상 생성되었는지 검증한다:
  ```powershell
  Get-Process Aside | Where-Object { $_.MainWindowTitle }
  ```

## User Login Tab Execution (사용자 로그인용 탭 실행 규칙)
- **증상**: `aside repl openTab()`으로 로그인 탭을 열었다고 보고했으나 사용자 화면에는 보이지 않음.
- **원인**: `aside repl` 탭은 보이지 않는 자동화 세션에 열리고 세션이 끝나면 사라짐 (`listBrowserTabs` 빈 배열 반환).
- **해결**: 사용자 로그인용 탭은 `aside repl openTab()`을 쓰지 않고, 보이는 창에 직접 열리도록 실행한다:
  ```powershell
  Start-Process 'C:\Program Files\Aside\Application\Aside.exe' -ArgumentList <URL들>
  ```
- **확인**: 메인 창(`MainWindowTitle`)에 해당 사이트 제목이 표시되는지 검증하고 사용자 확인을 거친다:
  ```powershell
  Get-Process Aside | Where-Object { $_.MainWindowTitle }
  ```
