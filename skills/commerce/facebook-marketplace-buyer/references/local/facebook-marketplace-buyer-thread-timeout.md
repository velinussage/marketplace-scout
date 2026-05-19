---
name: facebook-marketplace-buyer-thread-timeout
description: USE WHEN buyer threads have gone stale (no seller reply within the configured window, default 36 hours) and the user wants to decide nudge / raise / abandon. Surfaces context + drafted message variants per thread and routes the chosen draft through facebook-marketplace-message-sender with per-thread approval. DON'T USE WHEN no buyer threads are stalled, when the user wants standing approval for follow-up bumps, or when no offer ladder has been established.
version: 0.1.0
author: velinussage
prerequisites:
  commands: [browser-harness]
metadata:
  hermes:
    tags: [shopping, facebook, marketplace, follow-up, stalled-thread, messaging, approval-gate, agent-led]
    related_skills:
      - facebook-marketplace-buyer
      - facebook-marketplace-buyer-inbox-watcher
      - facebook-marketplace-negotiator
      - facebook-marketplace-seller-communication
      - facebook-marketplace-message-sender
      - facebook-marketplace-safety-guard
    requires_toolsets: [terminal]
---

# Facebook Marketplace Buyer Thread Timeout (Stage 4c)

Use this skill after `facebook-marketplace-buyer-inbox-watcher` has flagged one or more buyer threads as stalled — the seller didn't reply within the configured window. The skill computes a per-thread recommendation (nudge / raise / abandon), drafts the message variants for whichever option fits, and surfaces a single approval prompt to the user for each thread.

This skill never sends. The chosen draft routes through `facebook-marketplace-message-sender` (which requires its own `approval_token`).

## When to Use

Use this skill when:
- One or more threads in `reports/threads/*.json` have `current_state: "stalled"`, OR `current_state: "awaiting_seller_reply"` AND `(now - last_outbound_timestamp) > timeout_window_hours` (default 36 h).
- The user wants to decide what to do with stalled threads as a batch.
- The user is running a recurring loop and wants stalled-thread surfacing on a cadence.

## Don't Use When

Do not use this skill when:
- No threads are stalled — the digest would be empty.
- The user wants standing approval to auto-nudge across many threads — every send still goes through per-message approval via `message-sender`.
- The user hasn't supplied an offer ladder (`opening`, `likely`, `hard_stop`) on the relevant threads — a "raise" option needs the ladder to compute the bump.
- The thread is `flagged` (safety-guard hit) — route to user escalation, not to a timeout follow-up.

## Core Principles

1. **Stalled is computed, not declared.** A thread is stalled when `(now - last_outbound_timestamp) > timeout_window_hours`. The default window is 36 h; the user can override per-run. Don't trust a stale `current_state: stalled` from a previous run without re-checking the age.
2. **Recommendation per thread, not per batch.** Each thread gets its own assessment based on its ladder position, listing age, prior nudge count, and how the negotiation has been going. Two threads can land on different recommendations in the same run.
3. **Drafts are short, low-pressure, and tone-matched to real Marketplace buyers.** No corporate email voice, no "circling back," no fake urgency.
4. **The "raise" option respects the offer ladder hard stop.** Never propose a bump that exceeds the thread's `hard_stop`. If the ladder is already at `hard_stop` and the seller hasn't budged, "raise" isn't an option; the choice is `nudge-once-more` or `abandon`.
5. **"Abandon" doesn't message the seller.** It updates the thread JSON to `current_state: abandoned` and stops surfacing the thread in future runs. The seller hears nothing — abandoning a stalled thread is silent on Marketplace.
6. **One approval per thread, never batch.** The user makes a decision for each stalled thread individually. No bulk-approve-all UI.

## Procedure

The whole flow runs inside `browser-harness <<'PY' ... PY` heredocs where browsing is needed (e.g. listing-status refresh). State logic runs in Bash + `jq`.

### 1. Configure the timeout window

Default `timeout_window_hours = 36`. The user can override per-run with an explicit value (e.g. `48` for a slow-traffic listing category, `24` for high-traffic).

Also configure:
- `nudge_cooldown_hours = 12` — never compose a nudge if the last outbound message was itself a nudge within the cooldown.
- `max_nudges_before_abandon = 2` — after the second nudge gets no reply, the only recommendation is `abandon`.

### 2. Load stalled threads

Read `reports/threads/*.json`. For each thread with `role: "buyer"`:

- Skip if `current_state` is terminal (`closed_won`, `closed_lost`, `abandoned`).
- Skip if `current_state == "flagged"` — that thread routes to user escalation, not to timeout follow-up.
- Compute `hours_since_last_outbound = (now - last_outbound.timestamp) / 3600`.
- Include the thread if `hours_since_last_outbound > timeout_window_hours`.
- Annotate `nudge_count = count(outbound[].kind == "nudge")` (the message-sender stamps each send with a `kind` field — `opener` / `counter` / `nudge` / `clarify` / `meetup` — drawn from the caller's bundle).

If no threads qualify, surface `no stalled threads` and exit.

### 3. Refresh listing status for each stalled thread

For each stalled thread, open the underlying listing and check whether it's still live. A sold/removed listing changes the recommendation calculus — there's no point nudging a sold listing.

```bash
browser-harness <<'PY'
ensure_real_tab()
new_tab(LISTING_URL)
wait(3)
status = js("""
  (() => {
    const text = document.body.innerText || '';
    const url = location.href;
    const is_item = /\\/marketplace\\/item\\//i.test(url);
    const unavailable = /listing is no longer available|this item is sold|marked as sold|no longer for sale/i.test(text);
    const pending = /pending|item is pending/i.test(text);
    const price_match = text.match(/\\$([0-9][0-9,]*)/);
    const current_price = price_match ? parseInt(price_match[1].replace(/,/g, ''), 10) : null;
    return { is_item, unavailable, pending, current_price };
  })()
""")
print({ "listing_url": LISTING_URL, **status })
js("window.close()")
PY
```

If `unavailable: true` → recommendation is automatically `abandon-listing-gone`. If `pending: true` → recommendation is `nudge-soft` (seller is talking to someone else; one polite ping is fine). If `current_price < listing_policy.price` → the listing dropped; this changes the offer math.

### 4. Compute per-thread recommendation

For each stalled (and still-live) thread, apply this decision logic:

| Condition | Recommendation |
|---|---|
| Listing is `unavailable` | `abandon-listing-gone` |
| `nudge_count >= max_nudges_before_abandon` | `abandon` |
| Last outbound was a `nudge` AND `hours_since_last_outbound < nudge_cooldown_hours` | `wait` (skip this thread this run — re-check next run) |
| `outbound[]` has only one message (the opener) AND listing age < 3 days | `nudge` (polite, low-pressure) |
| `outbound[]` has only one message AND listing age >= 3 days | `nudge-or-abandon` (let the user choose; seller may have gone quiet on purpose) |
| Latest offer < `likely` from offer ladder AND `nudge_count == 0` | `nudge` first; let the user raise next round if no reply |
| Latest offer >= `likely` AND latest offer < `hard_stop` AND seller hasn't countered | `raise` to halfway between current offer and `hard_stop` |
| Latest offer == `hard_stop` AND no reply | `nudge-once-more-or-abandon` (no more raises possible) |
| Listing price dropped since opener | `re-engage-with-current-price` (nudge that anchors on the new price) |

The decision is a recommendation — the user picks the final action.

### 5. Draft the message variants for each thread

For each thread + recommendation, draft 3 short variants in real Marketplace-buyer tone:

#### `nudge` variants (low-pressure, friendly)
- `"Hey, just checking in — still interested if it's available."`
- `"Hi, following up on this. Is it still available?"`
- `"Hey, no rush — just letting you know I'm still interested if you haven't sold it."`

#### `raise` variants (anchor the new offer)
For each, fill in `<new_offer>` = midpoint of current offer and `hard_stop`, rounded to nearest $5.
- `"Hey — would $<new_offer> work? I could pick up [day]."`
- `"Hi, would you take $<new_offer>? Happy to come grab it [day]."`
- `"Hey, $<new_offer> with same-day pickup if that helps."`

#### `re-engage-with-current-price` variants
- `"Hey, saw the price drop — still interested. Want to set up a pickup?"`
- `"Hi, noticed it's now $<current_price>. Could pick up [day] if that works."`

#### `nudge-once-more-or-abandon`
Surface both options. The nudge variant is one short line; the abandon path doesn't send anything.

#### `abandon` / `abandon-listing-gone`
No variants. The action updates the thread JSON to `current_state: abandoned` and the user sees a single-line confirmation: "Abandon this thread? It won't send anything to the seller."

#### `wait`
No variants. The thread is skipped this run; logged as "still in nudge cooldown."

Every drafted variant runs through `facebook-marketplace-safety-guard` (direction: outbound) before surfacing. A blocked variant is dropped from the option set.

### 6. Surface a single per-thread approval prompt to the user

For each stalled thread, present a compact block:

```
Thread: Steelcase Leap V2 — item 2051040935...
Listing: $260 asking, your last offer was $230 (4 days ago, 1 message sent)
Recommendation: nudge
Listing status: live, no price change

Variants:
  [1] Hey, just checking in — still interested if it's available.
  [2] Hi, following up on this. Is it still available?
  [3] Hey, no rush — just letting you know I'm still interested if you haven't sold it.

Pick [1/2/3] to send, [a] to abandon this thread, or [s] to skip.
```

The user picks one explicitly. The skill never proceeds without an explicit per-thread choice — no defaults, no timeouts, no "the model picks if you don't reply."

### 7. Route the chosen action

| User choice | Action |
|---|---|
| `[1]` / `[2]` / `[3]` | Compose the bundle for `facebook-marketplace-message-sender` and surface it for the *final* approval-token step (per-message). The user must produce the token before the send runs. |
| `[a]` (abandon) | Update `reports/threads/<thread_id>.json` → `current_state: "abandoned"`. No message sent. Append a note to the thread JSON: `{ abandoned_at, reason: "buyer-timeout-no-reply" }`. |
| `[s]` (skip) | Take no action this run. The thread remains stalled and surfaces again next run. |

For the send path, the bundle to `message-sender` looks like:

```json
{
  "thread_url": "<thread_url>",
  "exact_text": "Hey, just checking in — still interested if it's available.",
  "approval_token": "<user-provided>",
  "listing_url": "<listing_url>",
  "role": "buyer",
  "state_path": "reports/threads/<thread_id>.json",
  "kind": "nudge"
}
```

The `kind: "nudge"` stamps the outbound record so future runs can count nudges correctly. (For `raise`, `kind: "counter"`.)

### 8. Update thread state for any action taken

- For sends, `message-sender` does the state update.
- For abandons, this skill writes:

```json
{
  "current_state": "abandoned",
  "abandoned_at": "2026-05-19T11:42:13-04:00",
  "abandon_reason": "buyer-timeout-no-reply",
  "recommended_next_action": "none"
}
```

- For skips, no update.

After the run, emit a one-line summary: `stalled threads found: N, sent: X, abandoned: Y, skipped: Z, wait-cooldown: W`.

## Output Contract

This skill returns:
- For each stalled thread: a recommendation, listing status, draft variants, and a user choice.
- Updated `reports/threads/<thread_id>.json` for any abandoned thread (state → `abandoned`).
- For any chosen send, a `message-sender` invocation with the bundle above.
- A run summary line.

This skill does **not** itself send. The send always routes through `message-sender`, which requires its own `approval_token`.

## Approval Policy

- **Per-thread, explicit choice.** Each stalled thread surfaces its own approval prompt. No `--approve-all`, no batch confirmation, no "send the recommended variant for every thread."
- **Approval token still required at the send step.** Even after the user picks a variant, `message-sender` requires the per-message `approval_token`. Picking a variant in this skill is *not* the same as approving the send; it's choosing *which text* would be sent if approval is granted.
- **Abandon is silent.** Updating state to `abandoned` doesn't message the seller; the user is choosing to walk away.
- **Cooldown is hard.** Never compose a nudge inside the `nudge_cooldown_hours` window. Even if the user asks ("nudge again"), the skill refuses and surfaces the cooldown timer.
- **Raise never exceeds `hard_stop`.** The ladder is canon; no improvisation.

## Anti-patterns

- **Don't nudge a thread that already had two nudges.** Two pings without a reply means the seller isn't engaging on Marketplace — a third is spammy.
- **Don't ask the user "want me to nudge them all?"** Even with N stalled threads, surface them one by one with their context.
- **Don't compose drafts with fake urgency** ("Last chance!", "Picking up today only!") just to provoke a reply. Tone parity beats response-rate optimization.
- **Don't auto-abandon listings that went pending.** Pending sometimes resolves back to available; one polite nudge is fine.
- **Don't skip the safety-guard pass** on draft variants. A poorly-worded nudge can still trip the guard (e.g. an over-eager "I can Venmo you tonight" — yes, agents have suggested that).
- **Don't write a Python orchestrator** to loop this skill. Each run is one-shot, agent-driven. Cadence belongs to the harness.

## Pitfalls

- **Wall-clock drift between runs.** If the user's machine was asleep, "last outbound 36 h ago" may actually be 60 h. Use the timestamps in the JSON, not relative-time strings the user remembers.
- **"Stalled" vs "ignored."** Some sellers list and never check Marketplace. A nudge to a never-active seller is harmless but futile; track `nudge_count` so the second one converts the recommendation to `abandon` automatically.
- **Listing went live again after going pending.** The listing-status refresh in step 3 catches this; without it the thread would look terminally stalled.
- **A price drop can change the math entirely.** If the listing dropped from $260 to $220 and the buyer's last offer was $230, the buyer is now *over* the ask. Surface this as a special `re-engage-with-current-price` rather than `nudge` so the user sees the math shift.
- **`kind` field on outbound records is library convention.** Older thread JSONs may not have it. When counting nudges, fall back to a substring heuristic ("checking in", "following up") on `outbound[].text` for legacy threads — and stamp the field going forward.
- **Don't surface `wait` threads in the user-facing digest.** They're not actionable; just log them in the run summary.

## Verification

Before reporting success, verify:
- The timeout window was applied per the configured value (default 36 h).
- Every stalled thread had its listing status refreshed before recommending an action.
- Every drafted variant passed `facebook-marketplace-safety-guard` (direction: outbound).
- Every variant respects the offer ladder's `hard_stop`.
- Each thread surfaced its own approval prompt; no batched/implicit approvals.
- Abandons only updated state; no message was sent.
- Sends were routed through `facebook-marketplace-message-sender` with a per-message `approval_token`.
- The nudge cooldown was honored; no thread was nudged within the cooldown window.
- The run summary line was emitted.
