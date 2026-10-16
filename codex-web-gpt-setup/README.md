# ChatGPT Web Skill

Reusable Windows CMD setup and diagnostic skill for **Codex Web GPT**, **GPT-6 High**, and common agent runners (**Codex, omo, GJC, Claude Code, Gemini CLI, OpenCode**).

The reusable skill is named `codex-web-gpt-setup` to keep compatibility with existing installations. `ChatGPT Web Skill` is the repository package name.

## What this installs

- A `codex-web-gpt` CMD command that can check health, install/configure the launcher, choose GPT-6 High, update it, and verify live responses.
- Reusable skill entry points for the installed agent runners.
- Separate **native** GPT-6 High routing for omo (`chatgpt-subscription`) and GJC (`openai-codex`). They **do not** use the Codex Web GPT local bridge.
- Agent model defaults for supported main agents, roles, categories, and subagents without overwriting their prompt bodies or tool permissions.

The skill is a setup tool; installing its files alone does not change every agent's model. Supported runners must be installed and authenticated individually. Never commit authentication files, OAuth tokens, runtime keys, or local report/backups.

## Install on Windows (CMD)

Requires Git, Node.js 22+, Python 3.11+, Codex CLI, and a compatible Windows x64 environment. Omo Native and GJC are optional and require their own login when selected.

Open **Command Prompt (`cmd.exe`)** and paste these commands one line at a time:

```bat
git clone --depth 1 --filter=blob:none --sparse https://github.com/lsi9923/gjc-skills.git "%TEMP%\gjc-skills-chatgpt-web"
cd /d "%TEMP%\gjc-skills-chatgpt-web"
git sparse-checkout set chatgpt-web-skill
call chatgpt-web-skill\install.cmd
"%USERPROFILE%\.local\bin\codex-web-gpt.cmd" status
"%USERPROFILE%\.local\bin\codex-web-gpt.cmd" setup --agents all
"%USERPROFILE%\.local\bin\codex-web-gpt.cmd" verify --omo --gjc
```

`setup` and `verify` need Codex Web GPT running and the appropriate logins. If GJC is not installed, omit `--gjc` from verification. First-time setup may open a login UI; do not paste passwords or API keys into commands or chats. **Do not force-close Codex Web GPT or change its settings while an AI request is running.**

To run it from an existing local copy instead, open CMD in the extracted `chatgpt-web-skill` directory and run `install.cmd`.

## Everyday commands

For an interrupted web response, run `codex-web-gpt repair-web`, then `codex-web-gpt verify-web`.
The repair backs up the affected settings, disables Bigger Context, and sets a 60,000-token compaction threshold.
Model selection and tool approvals are preserved. Restart Codex before using the new context settings.
The verification checks a fresh response, a read-only installed-app inventory command in the same chat, and a follow-up response.
It preserves permissions. The app inventory command must already be allowed by the user's native execution policy; otherwise the shell check reports failure.
Use `verify-web --high` to test High effort, or `--continue` to reuse successful probes after a diagnosed test interruption.
Reports retain failures as failures and are saved in `%LOCALAPPDATA%\CodexWebGPTSetup\reports`.
Server capacity failures and an already damaged active conversation are separate from these local settings.

Run the following in Command Prompt after installation:

```bat
"%USERPROFILE%\.local\bin\codex-web-gpt.cmd" models
"%USERPROFILE%\.local\bin\codex-web-gpt.cmd" status
"%USERPROFILE%\.local\bin\codex-web-gpt.cmd" agents all
"%USERPROFILE%\.local\bin\codex-web-gpt.cmd" verify-gjc
"%USERPROFILE%\.local\bin\codex-web-gpt.cmd" update
```

Within Codex, omo, or GJC, invoke the installed skill as `$codex-web-gpt-setup` or via the runner's skill-discovery command. Omo/GJC can also recognize `/skill:codex-web-gpt-setup` depending on runner support. `omo-gpt6` and `gjc-gpt6` are shell command wrappers provided by installation.

## Why does a web model display tokens?

Codex needs **input/output token estimates** to show context usage and decide when to compact a chat. The Codex Web GPT browser bridge explicitly marks these token counts as **estimated**. The token counter alone does **not** prove separate OpenAI API billing.

| Route | AI backend | Usage to check |
| --- | --- | --- |
| `chatgpt-web/gpt-6-sol` (Codex) | ChatGPT web browser bridge | ChatGPT web model/message limits; displayed Codex tokens are estimated |
| `chatgpt-subscription/gpt-6-sol` (omo Native) | Native subscription provider | ChatGPT subscription / applicable partner usage limits |
| `openai-codex/gpt-6-sol:high` (GJC) | Native Codex account provider | Applicable Codex / ChatGPT plan allowances or credits |
| OpenAI API key route | OpenAI API | Separate API billing (if explicitly configured) |

The bridge project's documentation says web-routed turns use **ChatGPT Web's separate usage limits** instead of Codex quota. This is a third-party bridge, not an official OpenAI billing guarantee. Check the route selected for the **actual turn** if your Codex quota or credits decrease. High reasoning can increase consumed usage on native providers.

Sources: [Codex Web GPT architecture](https://github.com/miuuyy/codex-chatgpt-web/blob/main/docs/architecture.md), [web token estimation code](https://github.com/miuuyy/codex-chatgpt-web/blob/main/src/adapters/chatgpt-web/usage.ts), [OpenAI Codex plan usage](https://help.openai.com/en/articles/11369540-using-codex-with-your-chatgpt-plan).

## Documentation and verification

- [SKILL.md](SKILL.md) — entry point / model routing and safety rules.
- [SETUP_KO.md](references/SETUP_KO.md) — Korean installation and troubleshooting instructions, all runner paths, model settings, and backup/restore.
- [VERIFICATION_KO.md](references/VERIFICATION_KO.md) — previously verified Windows installation and test results. These are historical results, not proof about another PC.
- [tests](tests/) — repeatable Node and Python regression checks.

Local configuration backups and reports are stored under `%LOCALAPPDATA%\CodexWebGPTSetup`. They are not part of this public repository.
