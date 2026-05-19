---
name: facebook-marketplace-message-sender
description: "USE WHEN any other Marketplace skill needs to actually click Send on an approved outbound message: routes to the thread, replaces any Facebook prefilled opener, types the approved text via native keystrokes, verifies the composer value byte-for-byte, clicks Send, confirms the bubble appears in the conversation, and updates the per-thread state file. DON'T USE WHEN no approved exact-text + approval token is in hand — this skill refuses to send without both."
version: 0.1.0
author: velinussage
prerequisites:
  commands: [browser-harness]
  browser:
    - browser-harness daemon attached to the user's logged-in Chrome (run `browser-harness --doctor` to verify)
metadata:
  hermes:
    tags: [shopping, facebook, marketplace, browser-automation, messaging, approval-gate, send-executor, agent-led]
    related_skills:
      - facebook-marketplace-buyer
      - facebook-marketplace-seller
      - facebook-marketplace-seller-communication
      - facebook-marketplace-negotiator
      - facebook-marketplace-safety-guard
      - facebook-marketplace-buyer-inbox-watcher
      - facebook-marketplace-buyer-thread-timeout
      - facebook-marketplace-seller-reply-composer
    requires_toolsets: [terminal]
---

# Facebook Marketplace Message Sender

Single source of truth for "send an approved Marketplace message." Every other messaging skill — buyer outreach, negotiator counters, seller replies, stalled-thread nudges — delegates the actual click-Send mechanic to this skill so the same prefilled-opener replacement, native-keystroke entry, value verification, post-send confirmation, and state-template update happens every time.

This skill never decides *what* to say. It only decides *whether the bundle it received is safe to send* and then executes the send precisely.

## When to Use

Use this skill when:
- A caller (buyer-comm, negotiator, seller reply composer, thread-timeout, inbox-watcher follow-up) has produced an approved exact-text message and an approval token from the user.
- The caller has a `thread_url` (Marketplace inbox thread or listing-message surface) and a `listing_url` for context.
- The user has explicitly approved this specific text — not a category, not a plan, not standing approval.

## Don't Use When

Do not use this skill when:
- There is no `approval_token` set by the user. The agent must never produce or paraphrase this token; absence means refuse.
- The text differs by even one character from what the user approved. Any drift requires a fresh approval round.
- The composer doesn't exist on the page yet (the listing isn't open, or the inbox surface isn't loaded).
- `browser-harness --doctor` reports daemon dead or Chrome unattached.
- `facebook-marketplace-safety-guard` returns `blocked` for the outbound text.

## Core Principles

1. **Approval token is non-negotiable.** The bundle must include a non-empty `approval_token` string produced by the user. If absent, return `{ status: "refused", reason: "no_approval_token" }` and stop. The agent must never synthesize this value.
2. **Exact-text discipline.** The skill types the `exact_text` field, no transformation, no paraphrase, no trailing whitespace normalization. After typing, the composer's read-back value must equal `exact_text` byte-for-byte; mismatch aborts.
3. **Native keystrokes only.** Synthetic `value =` assignment on a Facebook/Comet `[contenteditable]` does not enable the Send button. Use CDP `Input.dispatchKeyEvent` (or the harness's `type_text` / `press_key` helpers) so React's `input`/`beforeinput` listeners actually fire.
4. **Replace, don't append.** Any Facebook prefilled opener ("Hi, is this still available?") must be cleared via `Cmd/Ctrl+A` select-all → Backspace before typing the approved text. Appending leaves the prefilled draft in the outbound message.
5. **Safety-guard before Send.** Call `facebook-marketplace-safety-guard` with the outbound text + listing policy *before* the click-Send step. A `blocked` result aborts the send and surfaces the guard's recommended user-facing escalation.
6. **Post-send confirmation is a real check.** "Clicked Send" is not "sent." Wait until the just-typed text appears as a message bubble in the thread DOM before declaring success. If it doesn't appear within 8 seconds, report `{ status: "send_unverified" }` so the caller can investigate rather than silently moving on.
7. **State update happens once, after confirmation.** Update `reports/threads/<thread_id>.json` only after the bubble is confirmed visible. Failing earlier writes leave the state in a "sent" state when nothing went out.

## Input Contract

Callers pass a single bundle:

```json
{
  "thread_url": "https://www.facebook.com/marketplace/t/1234567890/",
  "exact_text": "Hey, is this still available? If so, would you take $250?",
  "approval_token": "user-approved-2026-05-19T10:42-msg-1",
  "listing_url": "https://www.facebook.com/marketplace/item/2051040935507757/",
  "role": "buyer",
  "state_path": "reports/threads/1234567890.json"
}
```

Field rules:

| Field | Required | Notes |
|---|---|---|
| `thread_url` | yes | Marketplace inbox thread URL (`/marketplace/t/<thread_id>/`). If the caller only has a listing URL, it must resolve the thread URL first by opening the listing's Message button surface; this skill won't search-and-find. |
| `exact_text` | yes | The literal characters to send. No formatting tokens, no placeholders. |
| `approval_token` | yes | Any non-empty string the user explicitly produced for this message. The skill checks presence, never value. |
| `listing_url` | yes | Passed through to safety-guard so listing policy (local-pickup vs ships, price band) can gate the check. |
| `role` | yes | `"buyer"` or `"seller"`. Stamped on the state-file `last_outbound` record so threads coming back from `buyer-inbox-watcher` know which side authored each message. |
| `state_path` | yes | Repo-relative path to the per-thread state JSON. Skill creates it if missing. |

## Procedure

The whole flow runs inside `browser-harness <<'PY' ... PY` heredocs invoked from Bash. No persisted Python orchestrators.

### 1. Preflight

```bash
browser-harness --doctor
```

Require `chrome running` and `daemon alive`. If either fails, return `{ status: "refused", reason: "browser_not_ready" }` — do not try to relaunch the browser.

Validate the input bundle:
- `approval_token` is a non-empty string → otherwise `{ status: "refused", reason: "no_approval_token" }`.
- `exact_text` is non-empty and not just whitespace → otherwise `{ status: "refused", reason: "empty_text" }`.
- `thread_url` matches `/marketplace/t/\d+/` or `/marketplace/item/\d+/` (listing-surface composer) — otherwise `{ status: "refused", reason: "bad_thread_url" }`.

### 2. Safety-guard pre-send

Invoke `facebook-marketplace-safety-guard` with:

```json
{
  "text": "<exact_text>",
  "direction": "outbound",
  "listing_policy": { "shipping": "<local-pickup|ships|both>", "price": <int> }
}
```

If the guard returns `{ status: "blocked", ... }`, abort with that bundle and surface the guard's `suggested_user_message` so the caller can present it to the user. Do not retry. Do not silently rewrite the text.

### 3. Open the thread and verify the composer

```bash
browser-harness <<'PY'
ensure_real_tab()
new_tab(THREAD_URL)
wait(3)
state = js("""
  (() => {
    const text = document.body.innerText || '';
    const url = location.href;
    const boxes = Array.from(document.querySelectorAll('[contenteditable="true"], textarea, input[type="text"]'))
      .filter(el => el.offsetWidth || el.offsetHeight || el.getClientRects().length);
    return {
      url,
      logged_out: /\\/login|Log in|Email address or phone number/i.test(url + ' ' + text),
      checkpoint: /checkpoint|two-factor|security check/i.test(url + ' ' + text),
      composer_count: boxes.length,
      composer_first_value: boxes[0] ? (boxes[0].innerText || boxes[0].value || '') : null,
      send_buttons: Array.from(document.querySelectorAll('[role="button"], button'))
        .map(b => (b.innerText || b.getAttribute('aria-label') || '').trim())
        .filter(t => /^Send$|Send message/i.test(t)).slice(0, 5)
    };
  })()
""")
print(state)
PY
```

If `logged_out` or `checkpoint` is true → `{ status: "refused", reason: "session_invalid" }`. If `composer_count == 0` → `{ status: "refused", reason: "no_composer" }` (the thread may have been archived or the URL is wrong).

### 4. Detect and replace any Facebook prefilled opener

The `composer_first_value` from step 3 is the prefilled draft Facebook injected. Common shapes:
- `"Hi, is this still available?"`
- `"Hi [Seller Name], is this still available?"`
- empty string (no prefill — most common on returning threads)

Regardless of content, clear the field before typing — even an empty composer can hold zero-width whitespace that breaks the byte-for-byte check.

```bash
browser-harness <<'PY'
ensure_real_tab()
# Focus the composer (first visible editable surface)
js("""
  (() => {
    const box = Array.from(document.querySelectorAll('[contenteditable="true"], textarea, input[type="text"]'))
      .find(el => el.offsetWidth || el.offsetHeight || el.getClientRects().length);
    if (box) { box.focus(); }
  })()
""")
# Native select-all + delete (Cmd on macOS, Ctrl elsewhere).
# The harness's press_key helper drives Input.dispatchKeyEvent under the hood.
press_key("a", modifiers=["meta"])      # macOS Cmd+A
press_key("Backspace")
PY
```

Re-read the composer value and assert it is empty (or only the zero-width prefill artifact Facebook sometimes leaves; treat anything ≤ 2 chars of whitespace as empty). If still populated after one clear pass, retry once. If still populated after two passes, return `{ status: "send_unverified", reason: "clear_failed" }`.

### 5. Type the approved text via native keystrokes

```bash
browser-harness <<'PY'
ensure_real_tab()
type_text(EXACT_TEXT)  # harness wraps Input.insertText / dispatchKeyEvent
wait(0.6)
PY
```

`type_text` must drive native key events, not synthetic `value =` assignment. Verify by reading the composer back:

```bash
browser-harness <<'PY'
ensure_real_tab()
value = js("""
  (() => {
    const box = Array.from(document.querySelectorAll('[contenteditable="true"], textarea, input[type="text"]'))
      .find(el => el.offsetWidth || el.offsetHeight || el.getClientRects().length);
    return box ? (box.innerText || box.value || '') : null;
  })()
""")
print({ "composer_value": value })
PY
```

Compare to `exact_text` byte-for-byte (no trim, no normalize). If they differ, return `{ status: "send_unverified", reason: "value_mismatch", expected: EXACT_TEXT, actual: value }` — never click Send when the field doesn't hold what was approved.

### 6. Click Send

Only after the value verification passes. Locate the Send button by visible text (Facebook rotates aria-labels; visible text is more stable):

```bash
browser-harness <<'PY'
ensure_real_tab()
clicked = js("""
  (() => {
    const buttons = Array.from(document.querySelectorAll('[role="button"], button'));
    const send = buttons.find(b => {
      const t = (b.innerText || b.getAttribute('aria-label') || '').trim();
      return /^Send$|^Send message$/i.test(t);
    });
    if (!send) return { found: false };
    const disabled = send.getAttribute('aria-disabled') === 'true' || send.disabled;
    if (disabled) return { found: true, disabled: true };
    send.click();
    return { found: true, disabled: false, clicked: true };
  })()
""")
print(clicked)
PY
```

If `disabled: true`, the typing didn't generate real input events. Return `{ status: "send_unverified", reason: "send_disabled" }` and recommend the caller verify the harness's `type_text` is actually dispatching native key events (not assigning `value`).

### 7. Post-send DOM confirmation

Wait up to 8 seconds for the typed text to appear as an outbound bubble in the thread:

```bash
browser-harness <<'PY'
ensure_real_tab()
import time
deadline = time.time() + 8
confirmed = False
snapshot = None
while time.time() < deadline:
    snapshot = js("""
      (() => {
        // Outbound bubbles on Marketplace render as right-aligned message rows.
        // Look for the just-sent text appearing in the conversation list.
        const rows = Array.from(document.querySelectorAll('[role="row"], div[aria-label]'));
        const allText = rows.map(r => (r.innerText || '').trim()).filter(Boolean);
        return { rows_count: rows.length, last_5: allText.slice(-5) };
      })()
    """)
    if any(EXACT_TEXT in line for line in (snapshot.get("last_5") or [])):
        confirmed = True
        break
    time.sleep(0.5)
print({ "confirmed": confirmed, "final_snapshot": snapshot })
PY
```

If `confirmed: false` after 8 s → `{ status: "send_unverified", reason: "no_bubble_after_send" }`. Do NOT mark the state file as sent; the caller can re-try with fresh approval.

### 8. Update the per-thread state file

Only on `confirmed: true`. Read the current `reports/threads/<thread_id>.json` (create if missing), append to `outbound[]`, update `last_outbound`:

```json
{
  "thread_id": "1234567890",
  "thread_url": "https://www.facebook.com/marketplace/t/1234567890/",
  "listing_url": "https://www.facebook.com/marketplace/item/2051040935507757/",
  "role": "buyer",
  "outbound": [
    { "timestamp": "2026-05-19T10:42:13-04:00", "text": "Hey, is this still available? ...", "role": "buyer" }
  ],
  "inbound": [],
  "last_outbound": {
    "timestamp": "2026-05-19T10:42:13-04:00",
    "text": "Hey, is this still available? ...",
    "role": "buyer"
  },
  "current_state": "awaiting_seller_reply"
}
```

The `thread_id` is the trailing path segment of `thread_url`. If the caller passed a listing-surface URL (the composer that opens from a listing's Message button), use the listing item id as the thread_id placeholder until the first inbound resolves the real thread URL — note this in `current_state: "thread_url_provisional"`.

### 9. Return the result

Return one of:

```json
{ "status": "sent", "thread_id": "1234567890", "bubble_confirmed": true, "state_path": "reports/threads/1234567890.json" }
{ "status": "blocked", "patterns_hit": ["venmo"], "guard_severity": "block", "suggested_user_message": "..." }
{ "status": "refused", "reason": "no_approval_token" | "empty_text" | "bad_thread_url" | "browser_not_ready" | "session_invalid" | "no_composer" }
{ "status": "send_unverified", "reason": "clear_failed" | "value_mismatch" | "send_disabled" | "no_bubble_after_send", ...debug fields... }
```

## Approval Policy

This skill is the bottleneck for every outbound Marketplace message in this library. The rule set:

- **Refuses without `approval_token`.** Always. No exceptions. The agent must never call this skill with a fabricated token; the user must produce it explicitly.
- **One token, one message.** A token authorizes exactly this one `exact_text` send. If the caller wants to follow up with a second message, it needs a second approval round and a fresh token.
- **No silent rewriting.** If safety-guard blocks the text or the field-value check mismatches, the skill never edits the text to make it acceptable. It returns the failure to the caller.
- **No standing approval.** This skill never accepts a flag like `pre_approved_for_session: true` or `auto_approve_within_band: true`. Approval is per-message.
- **No auto-recovery on send failure.** If post-send confirmation fails, the skill does not retry. The caller decides whether to re-approve and re-send.

## Anti-patterns

- **Don't synthesize `approval_token` from a previous message's token.** Each message gets its own.
- **Don't strip / normalize / smart-quote the text.** What the user approved is what gets typed.
- **Don't assume the composer is empty because the page just loaded.** Always run the clear step.
- **Don't click Send while the button is `aria-disabled`.** Report the failure so the underlying input-event problem is diagnosed instead of papered over.
- **Don't write to the state file before the bubble is confirmed.** That state lie compounds across runs.
- **Don't keep the thread tab open** if you opened it in step 3. Close it with `js("window.close()")` only after the state write succeeds.

## Pitfalls

- **Facebook's composer occasionally pre-injects an opener on first-touch of a listing's Message button.** It's silent — the field looks empty at first paint, then a half-second later the opener appears. Always wait at least 600 ms after `new_tab` before reading `composer_first_value`.
- **Cmd+A on a contenteditable inside an iframe-ish Comet surface sometimes only selects the focused element's text, not all of it.** If the clear pass leaves a residue, the second pass (`press_key("End")` → `Shift+Home` → `Backspace`) handles the edge case.
- **The Send button can stay disabled for 1–2 s after `type_text` even when keystrokes were real.** Wait briefly between typing and the click probe to avoid a false `send_disabled` result.
- **Thread URLs vs listing-surface composers behave differently.** A listing's Message composer creates a new thread on first send; the URL doesn't change to `/marketplace/t/...` until the reply lands. Provisional `thread_id` from the listing item id is fine for the immediate state write, but the next run should re-resolve to the real thread URL via the inbox.
- **The post-send DOM check is text-substring, not exact-match.** Facebook sometimes adds a leading "You: " prefix or trailing timestamp to outbound bubbles. Substring match on `exact_text` is the right heuristic.
- **Don't trust `aria-label` alone for the Send button.** Comet rotates labels (`Send`, `Send message`, `Press Enter to send`) seasonally; visible-text + regex is more stable.

## Verification

Before returning `{ status: "sent" }`, verify:
- `approval_token` was present and non-empty in the input bundle.
- safety-guard returned `pass`.
- The composer was located and verified visible.
- Any prefilled opener was cleared and the composer was empty before typing.
- `type_text` ran through native keystrokes (not synthetic value assignment) and the composer read-back equals `exact_text` byte-for-byte.
- The Send button was located, was not `aria-disabled` at click time, and was clicked.
- The typed text appeared as an outbound bubble in the thread DOM within 8 s.
- `reports/threads/<thread_id>.json` was updated with the new `outbound[]` entry and the `last_outbound` mirror.
- The thread tab opened for the send was closed (unless it was the user's pre-existing tab).
- No payment, deposit, off-platform-contact, or identity action was taken.
