---
name: chrome-ui-safe
description: Safely operate an already-open, user-authenticated Chrome window on Windows without replacing or closing the user's profile. Use when the user explicitly asks to use their computer, Chrome, Coupang Wing, or webmail.
---

# Safe operation of the user's existing Chrome

## Trigger

Use this skill only after an explicit request to operate the user's computer/Chrome or a named site such as Coupang Wing. Do not launch a replacement authenticated profile merely because a normal browser session is unavailable.

## Non-negotiable safety

- Preserve every existing Chrome window and tab. Never kill Chrome, replace its profile, or use the same `User Data` directory with a new browser process.
- Treat login state, mail, seller data, and attachments as private. Read only what is needed for the requested task and do not copy credentials, cookies, or unrelated messages into files or responses.
- Never press Send, Submit, Delete, Apply, or another consequential control unless the user explicitly requested that exact action and the target/account/item has been verified. “준비해”, “보낼 수 있게”, and “메일 작성” mean save a draft, not send.
- Do not close a user window. A duplicate compose window may be closed only when it was created by this workflow, is verified blank, and closing it cannot discard user content.
- Before any destructive or external action, verify the active account, exact identifier, visible target, and resulting status. Stop on ambiguity rather than guessing.

## Attach to the existing window

1. Prefer Windows UI Automation over browser profile launch or CDP. Enumerate `Chrome_WidgetWin_1` top-level windows from `AutomationElement.RootElement` and choose by exact title/content/handle.
2. Scope every UIA query to the selected window. Re-read after every navigation because element references become stale.
3. Read the address bar through the `ValuePattern` on `주소창 및 검색창` to confirm the current page before acting.
4. Navigate by setting the existing address bar value and pressing Enter. Open a new tab instead of replacing a user tab when navigation is not explicitly requested.
5. Prefer `InvokePattern`, `SelectionItemPattern`, `TogglePattern`, and `ValuePattern`. Use a clickable point only when the element exposes one and the selected window is visible.
6. If another application is foreground, do not steal focus casually. Focus Chrome only when the user authorized computer operation; restore/avoid unrelated windows and verify the foreground title before keyboard input.

## Forms, files, and mail

- For a web form, identify controls by accessible name and verify the resulting value after each edit.
- For native file pickers, select exact filenames from the picker UI, verify the file count and names in the compose window, and keep total size within the site's limit. Do not attach unrelated files.
- For a reply draft, verify recipient and subject, insert the prepared body, attach only verified evidence, click the site's draft-save control, and confirm the draft remains present. Leave the final Send control untouched unless explicitly told to send.
- Evidence must state observed facts only. Distinguish “deleted/status shows deleted” from “not found in search”; never infer a deletion or Rocket Growth status without visible evidence.

## Coupang Wing workflow

- Confirm the seller account/vendor ID in the visible Wing header before reading or changing products.
- For a violation notice, extract the exact violation dates, categories, and IDs from the notice, then search each ID in the relevant Wing surface.
- Check normal products through `상품관리 > 상품 조회/수정`; include deleted products when verifying remediation. Check Rocket Growth through `로켓그로스 > 재고현황` using the `옵션 ID` field when the notice permits a Rocket Growth exception.
- Capture evidence only after the search result and status are stable. Label evidence with the exact queried ID and observed result. Keep screenshots in a temporary, non-repository location unless the user requests permanent storage.
- Do not delete a product merely because a search result is similar. If the exact violating ID is already `상품삭제`, document that fact; if it is absent, document both the normal-product and Rocket Growth searches before drafting the appeal.

## Completion report

Report the exact account, identifiers checked, observed statuses, files attached, recipient/subject, and whether the draft was saved or actually sent. Mention any blocked step and why; never claim a click, upload, send, or deletion without verifying its result.
