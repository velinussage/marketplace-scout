---
name: facebook-marketplace-safety-guard
description: "USE WHEN any outbound Marketplace message is about to send, or any inbound seller/buyer message has just been captured, and you want a structured pass/blocked verdict for off-platform payment asks, deposit/holdback requests, premature identity exchange, shipping commitments outside listing policy, and common scam patterns. DON'T USE WHEN you want the skill to generate off-platform contact details (it never does) or to override a block without explicit user override."
version: 0.1.0
author: velinussage
prerequisites:
  commands: []
metadata:
  hermes:
    tags: [shopping, facebook, marketplace, safety, scam-detection, off-platform-guard, approval-gate, agent-led]
    related_skills:
      - facebook-marketplace-buyer
      - facebook-marketplace-seller
      - facebook-marketplace-message-sender
      - facebook-marketplace-seller-communication
      - facebook-marketplace-negotiator
      - facebook-marketplace-buyer-inbox-watcher
      - facebook-marketplace-buyer-thread-timeout
      - facebook-marketplace-seller-reply-composer
    requires_toolsets: [terminal]
---

# Facebook Marketplace Safety Guard

Use this skill as a structured pre-send guard for every outbound Marketplace message and as a post-parse classifier for every inbound message captured by an inbox watcher or reply composer. The skill carries the pattern catalog for off-platform payment asks, deposit / holdback requests, premature identity exchange, shipping commitments outside the listing policy, and common scam tells.

It is **detection-only**. It never generates off-platform contact details, never proposes a payment rail outside the platform, and never suggests sharing identity information prematurely. It only flags those patterns in *other* text.

## When to Use

Use this skill when:
- `facebook-marketplace-message-sender` is about to click Send on an outbound message — it must call this skill first.
- `facebook-marketplace-buyer-inbox-watcher` is classifying a newly-captured inbound message as part of its intent-parse step.
- `facebook-marketplace-seller-reply-composer` is preparing a reply and wants to verify the inbound the user is responding to wasn't a scam.
- The user pastes a seller / buyer message and asks "is this sketchy?"

## Don't Use When

Do not use this skill when:
- The text being checked is empty or contains no natural-language content (e.g. raw HTML, image-only message). Return `{ status: "pass" }` trivially.
- The user has *already* explicitly overridden a prior block on this same conversation and is sending the same text the guard just blocked. The override is the caller's responsibility to track; the skill itself doesn't remember session state.
- You want the skill to *propose* off-platform contact details — it never does. It only flags them.

## Core Principles

1. **Catalog-driven, not vibes-driven.** The detection logic is a published pattern catalog (below). Every block surfaces the exact pattern matched so the user can audit the verdict.
2. **Case-insensitive, word-boundary-respecting matches.** "Venmo" inside "Venmo me $50" matches; "venmo" in a hypothetical product name like "Venmotion 3000" would not (different word boundary). Most patterns are exact tokens or regex; the catalog table specifies which.
3. **Listing policy gates several patterns.** A "ship it" ask on a `local-pickup` listing is `warn` or `block`; on a `ships` listing it's `pass`. The caller must supply `listing_policy.shipping` for the gate to apply correctly.
4. **Severity has two levels: `warn` and `block`.** `warn` surfaces the pattern to the user but doesn't refuse the send; `block` refuses. The caller (`message-sender`) treats `block` as an abort. A single `block` hit dominates the verdict.
5. **Multiple high-severity hits in one inbound message → `suspicious` intent class.** That's a hand-off to `buyer-inbox-watcher`'s intent classifier, which uses this skill's result to label the message.
6. **The skill never auto-overrides.** A user-issued override (e.g. "I know it's risky, send it anyway") is a separate explicit step the caller manages. The skill itself always returns the same verdict for the same input.

## Input Contract

```json
{
  "text": "Can you send the deposit via Zelle? I'll ship it tomorrow.",
  "direction": "outbound" | "inbound",
  "listing_policy": {
    "shipping": "local-pickup" | "ships" | "both",
    "price": 260
  }
}
```

Field rules:

| Field | Required | Notes |
|---|---|---|
| `text` | yes | The natural-language content to scan. Empty / whitespace-only → trivial `pass`. |
| `direction` | yes | `outbound` scans for asks the *user* would be making (catches the agent suggesting Venmo). `inbound` scans for asks the *seller/buyer* is making of the user. |
| `listing_policy.shipping` | yes | `local-pickup` (most common), `ships` (seller offers shipping), `both`. Determines whether ship/mail patterns are `warn`/`block` or `pass`. |
| `listing_policy.price` | yes | The listed price. Used for the "deposit" pattern severity — a deposit ask on a $50 item is sketchier than on a $5,000 item. |

## Pattern Catalog

The catalog is the source of truth. Severities are `warn` or `block`. Patterns marked `block` cause `status: blocked` on a single hit; `warn` patterns only escalate to `block` if multiple fire together (≥ 2 warn hits in one inbound = `block`).

### Off-platform payment rails

| Pattern | Severity | Notes |
|---|---|---|
| `\bvenmo\b` | block | Most common scam tell. |
| `\bzelle\b` | block | Same. |
| `\bcash\s*app\b` or `\bcashapp\b` | block | Two spellings. |
| `\bapple\s*pay\b` | block | |
| `\bbitcoin\b` or `\bbtc\b` | block | Crypto asks. |
| `\bcrypto\b` | block | Catches "send crypto", "crypto wallet". |
| `\bwire\s*transfer\b` or `\bwire\s*\$?\d` | block | "Wire $500 to..." |
| `\bgift\s*card\b` | block | Classic scam pattern. |
| `\bpaypal\s*(friends|family|f&f)\b` | block | PayPal F&F is the off-platform variant. (Plain "PayPal goods & services" is a real Marketplace shipping flow — don't block.) |
| `\bmoneygram\b` or `\bwestern\s*union\b` | block | |

### Deposit / holdback

| Pattern | Severity | Notes |
|---|---|---|
| `\bdeposit\b` | warn | Common scam ask. Severity escalates on listings under $500 (most deposit scams target low-ticket items). |
| `\bhold\s*(it\s*)?for\s*me\b` | warn | Only escalates to `block` when paired with a payment-rail mention. |
| `\bpartial\s*(payment|deposit)\b` | warn | |
| `\bsend\s*\$?\d+\s*(to|via)\b` followed by a payment-rail pattern | block | "Send $100 to my Zelle" — the combo is decisive. |

### Premature identity exchange

| Pattern | Severity | Notes |
|---|---|---|
| US phone-number regex: `\b\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b` | warn | Catches `(555) 123-4567`, `555.123.4567`, `5551234567`. On outbound, scoped to messages where no meetup has yet been agreed (the caller's job to tell us via the `current_state` they pass — defer for now, treat any phone exchange before meetup as `warn`). |
| Email regex: `[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z\|a-z]{2,}` | warn | Same gating intent. |
| Street-address keywords: `\b\d{1,5}\s+[A-Z][a-z]+(?:\s+(St|Street|Ave|Avenue|Rd|Road|Blvd|Dr|Drive|Ln|Lane|Way|Ct|Court))\b` | warn | Catches "123 Main St", "5 Oak Avenue". Sellers sometimes share addresses for pickup — that's fine *after* a meetup proposal, but premature is warn-worthy. |
| `\btext\s*me\b` or `\btext\s*at\b` followed by a phone number on the same line | warn | The "let's move to text" ask. |

### Shipping outside listing policy

For listings with `listing_policy.shipping == "local-pickup"`:

| Pattern | Severity | Notes |
|---|---|---|
| `\bship\s*(it|to\s*me)?\b` | block | "Can you ship it to Florida?" |
| `\bmail\s*(it|to\s*me)?\b` | block | |
| `\btracking\s*number\b` | block | Seller is being asked to provide tracking — wrong flow. |
| `\b(usps|ups|fedex|dhl)\b` | warn | Carrier mention — context-sensitive. |
| `\bout\s*of\s*state\b` or `\bI'?m\s*not\s*local\b` | warn | Common scam preamble for a shipping ask. |

For listings with `listing_policy.shipping == "ships"`, all of the above are `pass`. For `both`, all are `pass`.

### Scam tells

These fire regardless of listing policy. Each is `block` on its own — they don't appear in legitimate buyer/seller conversation.

| Pattern | Severity | Notes |
|---|---|---|
| `\bI'?ll\s*send\s*(a|the)\s*check\b` | block | "I'll send a check for the full amount plus shipping" — classic overpayment scam. |
| `\bagent\s*will\s*pick\s*(it|this)\s*up\b` | block | Or "my assistant will pick up." |
| `\bsend\s*tracking\s*(number\s*)?first\b` | block | "Send tracking before I pay" — reversed flow. |
| `\boverpay(ment)?\b` | block | Overpayment scam keyword. |
| `\bwestern\s*union\b` | block | Already in payment-rail catalog; also a standalone scam tell. |
| `\b(my\s*(secretary|assistant)\s*will)\b` | block | The "absentee buyer" framing. |

### Off-platform contact rails (other than phone/email)

| Pattern | Severity | Notes |
|---|---|---|
| `\bwhatsapp\b` | warn | Sometimes legitimate for international sellers; usually a scam pivot on Marketplace. |
| `\btelegram\b` | block | Almost always a scam pivot. |
| `\bsignal\b` followed by a phone number | block | Same. |
| `\bcontact\s*me\s*on\b` | warn | Context-dependent. Combined with any of the above → block. |

## Procedure

The whole flow is in-process text matching. No browser, no I/O.

### 1. Validate input

- If `text` is empty or whitespace-only → return `{ status: "pass", reason: "empty_text" }`.
- If `direction` is missing or not in `{outbound, inbound}` → refuse with `{ status: "error", reason: "bad_direction" }`.
- If `listing_policy.shipping` is missing → default to `local-pickup` (the stricter mode) and add a note: `defaulted_shipping_policy: true`.

### 2. Tokenize

Lowercase the text. Build two views:
- `raw_lower` — the full text, lowercased, with all whitespace runs collapsed to single spaces.
- `lines` — the text split on `\n`, each line trimmed.

Most patterns match against `raw_lower` with explicit word boundaries (`\b`). Phone-number and email regexes match against `raw_lower` case-insensitive. Street-address regex matches against `lines` line-by-line.

### 3. Apply the catalog

For each pattern in the catalog:

- Run the regex / token match.
- If hit, record `{ pattern_name, severity, matched_substring }`.

### 4. Apply listing-policy gating

For shipping patterns:
- If `listing_policy.shipping == "local-pickup"`, all ship/mail/tracking hits keep their catalog severity.
- If `listing_policy.shipping == "ships"` or `"both"`, ship/mail/tracking hits are demoted to `pass` (removed from the hit list).

For deposit pattern:
- If `listing_policy.price < 500`, deposit hits escalate from `warn` to `block`.
- If `listing_policy.price >= 500`, deposit stays `warn`.

### 5. Compute the verdict

- If any pattern hit is `block` → `status: blocked`, `severity: block`.
- Else if `direction == "inbound"` AND `warn` count `>= 2` → `status: blocked`, `severity: block` (multiple warn hits in one inbound = compounding suspicion).
- Else if any `warn` hits → `status: warn`, `severity: warn`. Caller decides whether to surface to user.
- Else → `status: pass`.

For `inbound` direction, an additional flag `is_scam_pattern: true` is set when `block` severity comes from the **scam tells** sub-catalog (the overpayment / agent-pickup / send-tracking-first patterns specifically — those are decisively scam, not just policy violations).

### 6. Build the suggested user message

When `status: blocked`, generate `suggested_user_message`:

- For off-platform payment hits: `"This message asks to move payment off Marketplace ({pattern}), which is the most common scam pattern. I won't send / process this. Recommend you flag the thread or block the user."`
- For deposit hits on low-price listings: `"This message asks for a deposit on a ${price} listing, which is almost always a scam pattern. I won't proceed."`
- For shipping-outside-policy on local-pickup: `"This listing is local-pickup only. The shipping ask suggests the other party isn't local or isn't reading the listing — most legit local buyers/sellers don't push shipping. Recommend you confirm pickup terms or pass."`
- For scam-tell hits: `"This message matches a known scam pattern ({pattern}). I won't send / process this. Strongly recommend you don't reply."`
- For premature-identity (warn-only escalated by quantity): `"This message exchanges identity info ({patterns}) before a meetup is agreed. I'll flag for you to review; phone / address exchange usually waits until both sides are committed."`

### 7. Return the result

```json
{
  "status": "pass" | "warn" | "blocked" | "error",
  "severity": null | "warn" | "block",
  "patterns_hit": [
    { "pattern_name": "venmo", "matched_substring": "venmo", "severity": "block" }
  ],
  "is_scam_pattern": false,
  "suggested_user_message": null | "<string>",
  "defaulted_shipping_policy": false
}
```

## Wiring

This skill is called from three places in the library:

### Pre-send (outbound)

`facebook-marketplace-message-sender` calls this skill in step 2 of its procedure, before any composer interaction. A `blocked` result aborts the send, the bundle is returned to the caller, and the caller surfaces `suggested_user_message` to the user.

### Post-parse (inbound)

`facebook-marketplace-buyer-inbox-watcher` calls this skill for every new inbound message captured in its step 6 (intent classification). A `blocked` result tags the message with `intent: "suspicious"` and `intent_reasoning` includes the matched patterns; the thread's `current_state` flips to `flagged`.

### Reply composition (inbound + outbound)

`facebook-marketplace-seller-reply-composer` calls this skill once on the inbound message it's responding to (to detect scam) and once on every drafted outbound variant (to make sure the reply doesn't accidentally suggest off-platform contact).

## Approval Policy

- **Never auto-bypasses.** The skill always returns the same verdict for the same input. There is no `force: true` flag.
- **Override is the caller's responsibility.** If the user wants to send a message that the guard blocked (very rare and usually wrong), the caller must capture the explicit override string from the user (e.g. `"override-guard-2026-05-19T10:42"`) and proceed with the send while logging the override + the original guard verdict in the per-thread JSON. The guard itself never sees the override.
- **No off-platform escalation generated.** The skill never produces text like "you can use Venmo as a backup." Only detects.
- **Catalog updates require explicit edits to this file.** The catalog is not loaded from an external config to keep it auditable. Adding a pattern is a documented change.

## Anti-patterns

- **Don't suppress a block to "be helpful."** The guard exists because off-platform asks are the most common Marketplace scam pattern; a missed block is the failure mode that matters.
- **Don't broaden patterns to catch all variants** (`/zelle|venmo|cashapp|.../` as one giant regex). Per-pattern entries with named matches make the result auditable.
- **Don't classify by sentiment.** "I'm so excited to buy this!" is not a pattern. Stay catalog-driven.
- **Don't trust user-supplied policy blindly.** If the listing claims `shipping: ships` but the caller is operating on a `local-pickup` listing, the gate fails open. The caller is responsible for accurate policy.
- **Don't store conversation state.** The guard is a pure function — same input, same output, no memory. Override tracking belongs to the caller.

## Pitfalls

- **Listing-title false positives.** A listing literally titled "Bitcoin Mining Rig" or "Venmo Sticker Pack" can cause the guard to fire on legitimate listing-context discussion. The skill only scans message text — but be aware the caller might pass in a quoted listing title; surface this as a `defaulted_shipping_policy` -like flag if needed.
- **International phone formats** (e.g. `+44 20 7946 0958`) don't match the US-centric regex. For US-market Marketplace this is acceptable; if expanding to international, the catalog needs an i18n pass.
- **The "deposit" pattern is intentionally aggressive on low-priced listings.** A $200 chair with a "small deposit to hold" is almost certainly a scam. A $5,000 boat with a refundable deposit might be a real negotiation. The `< 500` threshold reflects the empirical scam pattern.
- **Severity escalation via warn count is direction-dependent.** Outbound messages don't escalate the same way — an outbound message with two warn hits is usually the agent being too eager (e.g. proposing to call + share an address in the same message); surface it as `warn` and let the user decide.
- **"PayPal goods & services" is the safe rail; PayPal F&F is not.** The catalog distinguishes them. Don't broaden the PayPal pattern.
- **`I'll send a check` is a high-confidence scam tell on Marketplace** — local-pickup transactions almost never use mailed checks. Don't soften this pattern.

## Verification

Before returning a verdict, verify:
- `text` was non-empty and `direction` was valid.
- `listing_policy.shipping` was supplied (or the default-fallback flag was set).
- Every reported `patterns_hit` entry has the matched substring captured.
- The verdict matches the rules: any `block` → `blocked`; ≥ 2 `warn` on inbound → `blocked`; any `warn` (otherwise) → `warn`; nothing → `pass`.
- `suggested_user_message` is present whenever `status: blocked`.
- `is_scam_pattern` is set only when the block came from the scam-tells sub-catalog.
- No off-platform contact details were generated as part of the response.
