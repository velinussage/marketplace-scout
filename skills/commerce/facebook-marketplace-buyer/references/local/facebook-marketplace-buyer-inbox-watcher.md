---
name: facebook-marketplace-buyer-inbox-watcher
description: USE WHEN at least one buyer-side message has been sent and you want the agent to poll the user's outbound Marketplace threads, detect new seller replies, parse each reply's intent, and surface a digest with recommended next-action classes. DON'T USE WHEN no outbound buyer message exists yet (there's nothing to watch) or when you want autonomous reply-sending (this skill is read-only).
version: 0.1.0
author: velinussage
prerequisites:
  commands: [browser-harness]
  browser:
    - browser-harness daemon attached to the user's logged-in Chrome (run `browser-harness --doctor` to verify)
metadata:
  hermes:
    tags: [shopping, facebook, marketplace, browser-automation, inbox, messaging, reply-detection, agent-led]
    related_skills:
      - facebook-marketplace-buyer
      - facebook-marketplace-seller-communication
      - facebook-marketplace-negotiator
      - facebook-marketplace-pickup-manager
      - facebook-marketplace-message-sender
      - facebook-marketplace-safety-guard
      - facebook-marketplace-buyer-thread-timeout
    requires_toolsets: [terminal]
---

# Facebook Marketplace Buyer Inbox Watcher (Stage 4b)

Use this skill after the buyer has sent at least one outbound Marketplace message and wants to know whether sellers have replied. The skill polls the tracked threads, diffs the current conversation state against the cached per-thread JSON, classifies any new inbound messages, and surfaces a compact digest with recommended next-action classes.

It is **read-only**. It never sends a reply. Drafts triggered by recommendations route through `facebook-marketplace-negotiator` → `facebook-marketplace-message-sender` with their own per-message approval.

## When to Use

Use this skill when:
- The user has at least one outbound thread tracked in `reports/threads/*.json` with `role: buyer`.
- The user wants a "what's new from sellers?" digest.
- The user is running a recurring loop (cron, manual cadence, or harness watch) and wants this skill invoked on a schedule.
- A buyer thread is `awaiting_seller_reply` and the user wants to check its status.

## Don't Use When

Do not use this skill when:
- No outbound buyer messages have been sent yet — there's nothing to watch. Route to `facebook-marketplace-seller-communication` (Stage 4) instead.
- The user wants the agent to autonomously reply to detected messages — this skill never sends.
- `browser-harness --doctor` reports daemon dead or Chrome unattached.
- The Marketplace session is logged out or hitting a checkpoint.

## Core Principles

1. **Tracked-thread set comes from `reports/threads/`, not from the Marketplace inbox UI.** The inbox lists every thread the user has ever had; this skill only re-examines the ones the buyer-side workflow created. If a thread JSON has `role: buyer`, it's in scope.
2. **Diff, don't re-read.** Each thread JSON holds the last-known snapshot. The skill captures the current snapshot and surfaces only the *new* inbound messages — not the full thread.
3. **Intent classification is per-message, not per-thread.** A single seller can send a counteroffer and a clarifying question in two consecutive bubbles. Each gets its own intent tag.
4. **Suspicion is delegated to safety-guard.** The watcher doesn't carry the off-platform / scam pattern catalog; it passes each new inbound message through `facebook-marketplace-safety-guard` with `direction: inbound` and uses the guard's result to drive the `suspicious` intent class.
5. **Recommendations are classes, not drafts.** This skill emits `counteroffer-via-negotiator`, `answer-clarification`, `confirm-meetup-via-pickup-manager`, `walk-away` — short next-action class names. Drafting the actual reply text belongs to the receiving skill, not the watcher.
6. **Virtualized message lists need scroll-load.** Long threads truncate at the top; the skill scroll-loads to find new inbound messages if the last cached message isn't visible in the initial snapshot.

## Procedure

The whole flow runs inside `browser-harness <<'PY' ... PY` heredocs. No persisted Python orchestrators.

### 1. Preflight

```bash
browser-harness --doctor
```

Require `chrome running` and `daemon alive`. Bail if either fails.

### 2. Load the tracked-thread set

Read all `reports/threads/*.json` files. Filter to entries where `role: "buyer"`. For each, capture:

- `thread_id`, `thread_url`, `listing_url`
- `outbound[]` (count, last timestamp)
- `inbound[]` (count, last timestamp, last text — for the diff)
- `current_state` (`awaiting_seller_reply`, `negotiating`, `meetup_proposed`, `stalled`, `abandoned`, `closed_won`, etc.)
- `listing_policy` (shipping mode, listed price — passed through to safety-guard later)

Skip threads with `current_state` in `{closed_won, closed_lost, abandoned}` — they're terminal.

Record the working set count for the digest header.

### 3. Open the Marketplace inbox surface (sanity check)

```bash
browser-harness <<'PY'
ensure_real_tab()
new_tab("https://www.facebook.com/marketplace/inbox/")
wait(3)
state = js("""
  (() => {
    const text = document.body.innerText || '';
    const url = location.href;
    return {
      url,
      logged_out: /\\/login|Log in|Email address or phone number/i.test(url + ' ' + text),
      checkpoint: /checkpoint|two-factor|security check/i.test(url + ' ' + text),
      thread_rows: document.querySelectorAll('a[href*="/marketplace/t/"]').length,
      excerpt: text.slice(0, 400)
    };
  })()
""")
print(state)
PY
```

If `logged_out` or `checkpoint` is true, stop and ask the user to fix the session manually — do not type credentials. If `thread_rows == 0`, the inbox didn't render; report `low_yield_run` and stop without false-clearing existing state.

### 4. For each tracked thread, capture the current snapshot

```bash
browser-harness <<'PY'
ensure_real_tab()
new_tab(THREAD_URL)
wait(3)

# Long threads virtualize the top; scroll the message list up a few times to load older bubbles
# if the cached last_inbound_text isn't yet visible.
js("""
  (() => {
    const scroller = document.querySelector('[role="main"]') || document.scrollingElement;
    if (scroller) scroller.scrollTop = 0;
  })()
""")
wait(1)

messages = js("""
  (() => {
    // Outbound and inbound bubbles render as separate rows; the simplest stable
    // signal is the row's text content + an alignment heuristic via aria-label
    // or row class. We capture everything and let the post-processor classify.
    const rows = Array.from(document.querySelectorAll('[role="row"], div[data-testid*="message"]'));
    return rows.map(r => {
      const text = (r.innerText || '').trim();
      // Outbound bubbles often carry "You sent" / "You: " prefixes or right-side
      // alignment classes; inbound bubbles carry the seller's name or no prefix.
      const aria = (r.getAttribute('aria-label') || '').toLowerCase();
      const is_outbound = /^you\\s/i.test(text) || /sent by you/i.test(aria);
      // Strip the "You: " / "Sent at HH:MM" decorations to get the body.
      const body = text
        .replace(/^You:\\s*/i, '')
        .replace(/\\bSent (at|today|yesterday) .+$/i, '')
        .trim();
      return body ? { body, is_outbound } : null;
    }).filter(Boolean);
  })()
""")
print({ "thread_url": THREAD_URL, "message_count": len(messages), "messages": messages })
js("window.close()")
PY
```

If the message list comes back empty for a thread that previously had bubbles, treat it as a virtualization failure — do not mark the thread as cleared, just log `snapshot_failed` for that thread and skip it this run.

### 5. Diff against the cached snapshot

For each thread, identify new inbound messages: messages where `is_outbound == false` AND the body text doesn't appear in the cached `inbound[].text` list (substring match on the cached list's most recent ~10 entries is sufficient — Facebook's bubble truncation can change spacing).

If no new inbound, mark the thread as `unchanged` and continue.

If new inbound found, append each new message to the thread JSON:

```json
{
  "inbound": [
    { "timestamp": "2026-05-19T11:08:00-04:00", "text": "Would you take $230?", "intent": "counteroffer" }
  ]
}
```

The `timestamp` is the harness wall-clock at capture time — Facebook's bubble timestamps are imprecise ("Sent at 10:42") and not always parseable. Sort `inbound[]` by capture order.

### 6. Classify intent on each new inbound message

For each new inbound message, classify it into one of:

| Intent | Rubric |
|---|---|
| `counteroffer` | Contains a dollar amount that differs from the listed price; phrases like "I can do $X", "would you take $X", "$X firm". |
| `accept` | Seller agrees to the buyer's last offer: "OK that works", "Deal", "Sure $X works". |
| `hold-firm` | No price movement, seller restates ask: "Price is firm", "$X is the price", "Not budging". |
| `clarification-question` | Seller is asking for buyer info: "What time can you pick up?", "Do you have a truck?", "Where are you coming from?". |
| `meetup-proposal` | Seller is proposing a specific time or location: "Can you come Saturday at 2?", "I'm at [address]". |
| `decline` | Seller is declining to sell: "Sorry, I have other interest", "Going to someone else first". |
| `off-topic` | Doesn't relate to the listing: spam, wrong-thread reply, ambient chatter. |
| `suspicious` | `facebook-marketplace-safety-guard` returned `blocked` for the inbound text — likely off-platform payment ask, premature identity exchange, scam tell, or shipping ask outside listing policy. |

Run `facebook-marketplace-safety-guard` with `{ text: inbound_text, direction: "inbound", listing_policy }` first. If `status: blocked`, intent is `suspicious` regardless of other content (a single Venmo mention overrides any "still available?" framing).

Otherwise, classify via straightforward LLM-style judgment with the listing context + conversation history in mind. Document the rubric in the per-thread JSON (`intent_reasoning` field, one short sentence) so the user can see why the agent labeled it.

When a single inbound message expresses two intents (e.g. "Yes still available, can you do $220?"), pick the dominant one: counteroffer > meetup-proposal > clarification-question > accept > hold-firm > decline > off-topic. The `intent_reasoning` field surfaces the secondary signal.

### 7. Update the thread state

For each thread that changed:

- Append new inbound messages to `inbound[]` with their `intent` and `intent_reasoning`.
- Update `last_inbound_timestamp` to the most-recent capture timestamp.
- Recompute `current_state`:
  - any `suspicious` → `flagged`
  - any `counteroffer` → `negotiating`
  - any `meetup-proposal` → `meetup_proposed`
  - any `accept` → `accept_pending`
  - any `decline` → `closed_lost`
  - clarification-question only → `awaiting_buyer_clarification`
  - hold-firm only → `negotiating_firm`

For each `current_state`, set `recommended_next_action`:

| State | Recommended next-action class |
|---|---|
| `flagged` | `escalate-to-user` (surface safety-guard's `suggested_user_message`) |
| `negotiating` | `counteroffer-via-negotiator` |
| `meetup_proposed` | `confirm-meetup-via-pickup-manager` |
| `accept_pending` | `confirm-via-seller-communication` |
| `closed_lost` | `walk-away` (no further action) |
| `awaiting_buyer_clarification` | `answer-clarification` (route back to `seller-communication`) |
| `negotiating_firm` | `walk-away-or-raise-via-negotiator` |

Write back to `reports/threads/<thread_id>.json`.

### 8. Surface the digest

Emit a single console digest, one line per changed thread plus a summary header:

```
Inbox watcher run @ 2026-05-19T11:42-04:00
  Tracked threads: 7   Changed: 3   Suspicious: 1   Unchanged: 4

  [negotiating]   Steelcase Leap V2 (item 2051040935...) — seller offered $230 (was asking $260).
                  → counteroffer-via-negotiator
  [meetup_proposed] Varier kneeling chair (item 9043...) — "Saturday at 2 works, my address is..."
                  → confirm-meetup-via-pickup-manager
  [flagged]       IKEA HOVET mirror (item 1781...) — seller asked to "send Venmo as deposit."
                  → escalate-to-user
```

The digest is the primary output. The thread JSON updates are the durable artifact the downstream skills consume.

## Output Contract

This skill returns:
- Updated `reports/threads/<thread_id>.json` files for every thread that changed (new `inbound[]` entries with intents, refreshed `current_state`, refreshed `last_inbound_timestamp`, recommended `next_action_class`).
- A console digest summarizing what changed, with one line per changed thread.
- A run summary: `{ tracked, changed, suspicious, unchanged, snapshot_failed }`.

The skill does **not** produce drafts. Routing those is the caller's job — typically the buyer umbrella routes the digest entries to `negotiator` or `pickup-manager`, each of which produces drafts that flow through `message-sender` for the actual send.

## Approval Policy

This skill is read-only. No approval is required to poll the inbox and update thread state.

Any reply the user later approves goes through `facebook-marketplace-message-sender` with its own per-message approval token — never through this skill. This skill never types into a composer, never clicks Send, never opens the listing-message surface.

## Anti-patterns

- **Don't infer intent from the thread's `current_state` alone.** A `negotiating` thread can still receive a `decline` as its next message — re-classify each new inbound on its own.
- **Don't silently overwrite the cached `inbound[]`.** Append only; the diff depends on the cache being a true running record.
- **Don't mark a thread `closed_lost` on a single `decline`.** Sometimes sellers come back. The state is fine; the recommended action of `walk-away` already reflects it.
- **Don't try to parse Facebook's bubble timestamps.** They're imprecise and locale-dependent; capture-time wall-clock is sufficient for ordering.
- **Don't open a thread tab and leave it open.** Close it after the snapshot with `js("window.close()")`.
- **Don't run safety-guard on outbound messages here.** This skill only handles inbound. Outbound checks live in `message-sender`.

## Pitfalls

- **Facebook's inbox URL redirects to the most-recently-active thread.** Navigating to `/marketplace/inbox/` and assuming you'll see all threads is fragile — go directly to `/marketplace/t/<thread_id>/` for each tracked thread.
- **The message-list virtualizes both ends.** Long threads (50+ bubbles) hide older messages; the diff can return false-positives if the cache holds an older message the current snapshot doesn't include. Scroll-to-top once before reading, and rely on the cache's most-recent ~10 entries for the diff.
- **A seller can send a reply that *looks* like spam (one word, no punctuation) but is actually substantive ("$220").** Don't classify length-based; classify on substance.
- **`is_outbound` heuristic isn't perfect.** Facebook localizes "You: " in some accounts and uses pure alignment elsewhere. When in doubt, treat a message as inbound and let safety-guard catch the false-positives.
- **Stale thread JSON from a previous library version** may not have `role`. Treat missing `role` as `buyer` when the thread came from `seller-communication` (buyer side); otherwise skip the file with a warning rather than guessing.
- **Don't trigger more than one thread navigation in a tight loop without a wait.** Facebook will throttle the rapid CDP navigations; pace at ~2 s between threads.

## Verification

Before reporting success, verify:
- `browser-harness --doctor` reported healthy state.
- The tracked-thread set was loaded from `reports/threads/*.json`, not invented.
- Each tracked thread either has an updated JSON or was logged as `snapshot_failed` / `unchanged`.
- New inbound messages were appended (not overwriting prior cache).
- Each new inbound message carries `intent` and `intent_reasoning`.
- Suspicious messages were flagged by safety-guard, not by ad-hoc string matching.
- The digest lists every changed thread with a recommended next-action class.
- No outbound message was sent (this skill is read-only).
- No thread tabs were left open.
