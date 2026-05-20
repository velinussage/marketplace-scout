---
name: facebook-marketplace-runtime-setup
description: "USE WHEN a coding-agent session is about to invoke any marketplace-scout skill but `browser-harness` is missing, broken, or not yet attached to Chrome. Installs browser-harness via uv, attaches it to the user's real Chrome with remote debugging, signs the user into Facebook, and verifies the full runtime is healthy before any other marketplace skill runs. DON'T USE WHEN `browser-harness --doctor` already reports `chrome running` and `daemon alive` — the runtime is ready and no install action is needed."
version: 0.1.0
author: velinussage
prerequisites:
  commands: [git, uv]
  browser:
    - User has Chrome (or Chromium-based browser) installed
metadata:
  hermes:
    tags: [shopping, facebook, marketplace, browser-automation, install, setup, runtime, prerequisite]
    related_skills:
      - facebook-marketplace-buyer
      - facebook-marketplace-seller
      - facebook-marketplace-history-seed
      - facebook-marketplace-message-sender
      - facebook-marketplace-safety-guard
      - facebook-marketplace-seller-communication
      - facebook-marketplace-watch-notifier
    requires_toolsets: [terminal]
---

# Facebook Marketplace Runtime Setup

Every other skill in this library assumes `browser-harness` is installed, attached to the user's signed-in Chrome, and reachable on the host. This skill is the one-stop install + attach + verify flow. Run it whenever a marketplace-scout skill complains that the browser-harness daemon isn't alive, Chrome isn't reachable, or Facebook session is missing.

This skill does NOT touch Marketplace data or send any messages. It only sets up the runtime.

## When to Use

Use this skill when:
- `browser-harness --doctor` reports `chrome FAIL` or `daemon FAIL`.
- `browser-harness` is not installed at all (`command -v browser-harness` returns nothing).
- A marketplace-scout skill bailed early with a message like "browser-harness is not attached" or "Chrome is not reachable."
- The user signed out of Facebook in their Chrome and the session needs to be restored before running buyer/seller workflows.

## Don't Use When

- `browser-harness --doctor` already reports `chrome running` AND `daemon alive`. Runtime is healthy; skip.
- The user is on a non-Chrome / non-Chromium browser. The library does not currently support Firefox or Safari.
- The user wants to run a marketplace skill against a headless cloud browser. That requires the Browser Use Cloud configuration (`BROWSER_USE_API_KEY`); refer them to the upstream browser-harness docs instead of running this skill.

## Core Principles

1. **One source of truth.** This is the canonical install/attach/verify reference for the whole marketplace-scout library. Other skills' "Pitfalls" sections may mention browser-harness issues but should defer to this skill for the actual fix.
2. **Idempotent.** Running this skill when everything is already set up should be a no-op that reports "already healthy" and exits.
3. **Try yourself before asking the user.** Each step has an automation path and a fallback that asks the user. Always try the automated path first; only escalate to the user when the step genuinely needs them (ticking a Chrome checkbox, clicking Allow on a popup, entering Facebook credentials).
4. **No payment, no Marketplace action.** This skill is read-only with respect to Marketplace itself. It only operates on the runtime layer.

## Procedure

### 1. Check current state

```bash
command -v browser-harness && browser-harness --doctor
```

Decision tree:

- **`browser-harness` not found** → install (step 2)
- **`chrome FAIL`** → user's Chrome isn't running; ask them to open it (step 3)
- **`chrome ok` + `daemon FAIL`** → remote debugging not enabled yet (step 4)
- **`chrome running` + `daemon alive`** → check Facebook session (step 5)

If all checks pass, report "runtime healthy" and exit.

### 2. Install `browser-harness`

The upstream-recommended path is an editable `uv tool` install from a stable clone. Pre-flight:

```bash
command -v uv || curl -LsSf https://astral.sh/uv/install.sh | sh
command -v git
mkdir -p ~/Developer
```

Install:

```bash
cd ~/Developer
git clone https://github.com/browser-use/browser-harness
cd browser-harness
uv tool install -e .
command -v browser-harness   # confirms ~/.local/bin/browser-harness exists
```

Why editable: when the agent edits `agent-workspace/agent_helpers.py` later, the next `browser-harness` run picks up the change immediately. Don't install into `/tmp` — use `~/Developer/browser-harness` or another durable path.

Optional but recommended — make the harness's own `SKILL.md` globally discoverable by your coding-agent host:

```bash
# Claude Code: append an import to ~/.claude/CLAUDE.md
echo '@~/Developer/browser-harness/SKILL.md' >> ~/.claude/CLAUDE.md

# Codex: symlink into the global skills dir
mkdir -p "${CODEX_HOME:-$HOME/.codex}/skills/browser-harness"
ln -sf "$PWD/SKILL.md" "${CODEX_HOME:-$HOME/.codex}/skills/browser-harness/SKILL.md"
```

### 3. Ensure Chrome is running with the user's real profile

The marketplace-scout library is designed for **Way 1** (real-profile attach), not the isolated `--remote-debugging-port` path. The user's real Chrome must be running, because the Facebook session and the user's identity for Marketplace messaging come from that profile.

If `--doctor` shows `chrome FAIL`:

- **Try yourself:** `open -a "Google Chrome"` (macOS) — opens the user's default Chrome with their default profile.
- **Fallback:** ask the user to open Chrome themselves, then re-run the check.

Do NOT launch Chrome with `--remote-debugging-port=9222 --user-data-dir=<custom>`. That gives an isolated profile and loses the user's Facebook login.

### 4. Enable remote debugging (one-time per Chrome profile)

If `chrome ok` but `daemon FAIL`, Chrome is running but isn't allowing remote-debugging attach yet. This is a one-time per-profile setup.

**Try yourself (macOS):** open the inspect page in the user's running Chrome:

```bash
osascript -e 'tell application "Google Chrome" to activate' \
          -e 'tell application "Google Chrome" to open location "chrome://inspect/#remote-debugging"'
```

Then tell the user, in plain language:

> "I opened `chrome://inspect/#remote-debugging` in your Chrome. Tick the **'Allow remote debugging for this browser instance'** checkbox — it's a one-time setting. Then come back here."

After they tick it, retry `browser-harness --doctor`. If Chrome is 144+, an "Allow remote debugging?" popup will appear on the first attach — instruct the user to click **Allow**. This popup may reappear on later attaches under conditions not fully characterized upstream; click Allow each time.

### 5. Verify Facebook session

Once the harness is healthy, confirm the user's Chrome has an active Facebook session — marketplace-scout uses the user's logged-in cookies; it never types credentials.

```bash
browser-harness <<'PY'
ensure_real_tab()
new_tab("https://www.facebook.com/marketplace/")
wait(3)
state = js("""
  (() => {
    const text = document.body.innerText || '';
    const url = location.href;
    return {
      url,
      logged_out: /\/login|Log in|Email address or phone number/i.test(url + ' ' + text),
      checkpoint: /checkpoint|two-factor|security check/i.test(url + ' ' + text),
      card_count: document.querySelectorAll('a[href*="/marketplace/item/"]').length
    };
  })()
""")
print(state)
PY
```

Decision tree on the result:

- **`logged_out: true`** → ask the user to sign into Facebook in that Chrome window. Never type credentials on their behalf.
- **`checkpoint: true`** → ask the user to clear the security check (2FA / phone confirmation) in Chrome themselves.
- **`card_count == 0`** but logged in → Marketplace surface didn't render; can happen if the user is region-blocked or location prompt is showing. Ask the user to set their location in Chrome.
- **`card_count > 0`** → session is good. Runtime is ready.

### 6. Final health check

```bash
browser-harness --doctor
```

Confirm `chrome running` AND `daemon alive`. Surface the version line — the library was developed against `browser-harness` ≥ 0.1.0; very old versions may lack helpers the marketplace skills depend on (`fill_input`, `press_key`, native CDP `Input.insertText`).

If the doctor says an update is available, run:

```bash
browser-harness --update -y
```

(`--update` refuses to run on an editable clone with uncommitted changes. If that happens, surface it to the user; don't `git stash` on their behalf.)

## Output Contract

This skill returns:
- `{ status: "ready" }` — runtime is healthy, all checks pass, Facebook session is active.
- `{ status: "needs_install", missing: ["browser-harness"|"uv"|"git"], action: "..." }` — components are missing; the user needs to run the install steps.
- `{ status: "needs_user_action", reason: "chrome_not_running"|"remote_debugging_disabled"|"chrome_144_allow_popup"|"facebook_logged_out"|"checkpoint"|"location_prompt", instruction: "..." }` — automated path is blocked on a user-controlled step.
- `{ status: "stale_version", current: "X.Y.Z", latest: "A.B.C", action: "browser-harness --update -y" }` — runtime works but should update.

## Approval Policy

Read-only with respect to Marketplace itself — no listings opened, no messages sent, no listings created. No payment of any kind.

Local system actions taken automatically:
- `uv tool install -e .` from a fresh clone of `browser-harness` (writes to `~/.local/share/uv/tools/`)
- `git clone https://github.com/browser-use/browser-harness` into `~/Developer/`
- Opens `chrome://inspect/#remote-debugging` in the user's existing Chrome via `osascript` (macOS)
- Runs `browser-harness --doctor` and a single Marketplace homepage navigation for session verification
- Optional `browser-harness --update -y` if a newer release is published

User-approval-required actions:
- Modifying `~/.claude/CLAUDE.md` to add the browser-harness skill import (offer it; don't append without confirmation)
- Symlinking into `$CODEX_HOME/skills/` (same — offer it)
- Restarting Chrome (the user does this themselves)

## Anti-patterns

- **Don't launch Chrome with `--remote-debugging-port=9222 --user-data-dir=<custom>`** for marketplace-scout use. That's the isolated-profile path (Way 2); it strips the user's Facebook cookies and breaks every messaging skill.
- **Don't ever type the user's Facebook password.** If they're logged out, surface it and let them sign in themselves.
- **Don't `pip install browser-harness`** as the first attempt unless `uv` is genuinely unavailable. The editable `uv tool install -e .` from a stable clone is the canonical install path; PyPI may not have the version this library targets.
- **Don't install into `/tmp`** or any ephemeral path. `~/Developer/browser-harness` (or another durable location the user has named) is correct.
- **Don't run multiple instances of `browser-harness`** against the same Chrome simultaneously — the daemon namespaces via `BU_NAME`, and parallel daemons against one profile can race.

## Pitfalls

- **Chrome 144+ "Allow remote debugging?" popup** can re-appear on later attaches. The conditions aren't fully characterized upstream. Tell the user to click Allow when it appears; don't try to dismiss it.
- **The Privy / Sage wallet flow uses a different daemon.** This skill manages the `browser-harness` daemon for Chrome attach. Sage's `sage daemon` is a separate process and won't help here.
- **Multiple Chrome profiles** can confuse the harness's discovery. If the user has Chrome Beta, Canary, or Chromium installed alongside regular Chrome, the doctor may attach to a profile that doesn't have the Facebook session. If `card_count == 0` after a logged-in check, ask which Chrome profile the user expects marketplace-scout to use.
- **macOS Sequoia and later** may show a system permission prompt the first time `osascript` automates Chrome. The user must click "Allow" in System Settings → Privacy → Automation. If `osascript` silently no-ops, that's the cause.
- **`uv` install path:** the `uv tool` binaries land in `~/.local/share/uv/tools/<name>/bin/` with a symlink to `~/.local/bin/<name>`. Make sure `~/.local/bin` is on `PATH`; some shells (e.g., zsh fresh install) don't include it by default.

## Verification

Before reporting `{ status: "ready" }`, verify:
- `command -v browser-harness` resolves to a real binary (not a stale shim).
- `browser-harness --doctor` reports `chrome running` and `daemon alive`.
- A test navigation to `https://www.facebook.com/marketplace/` finds ≥ 1 marketplace listing link (`a[href*="/marketplace/item/"]`).
- The user's Facebook session is active (no `/login` redirect, no `checkpoint`).
- The `browser-harness` version is recent enough — if the doctor reports an update is available and the user agrees, run `--update -y`.

If any of those fail, return the structured `{ status, ... }` bundle so the calling skill knows whether to wait for the user or abort.
