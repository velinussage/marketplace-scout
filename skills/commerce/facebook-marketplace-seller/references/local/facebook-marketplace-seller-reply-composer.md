---
name: facebook-marketplace-seller-reply-composer
description: USE WHEN a buyer has messaged a listing the user is selling and you want the agent to draft a tailored reply that resolves the thread to its listing, applies the seller's policy (shipping, holds, price floor), matches real Marketplace-seller tone, and routes the chosen draft through facebook-marketplace-message-sender for per-message approval. DON'T USE WHEN the listing facts aren't yet loaded, when the user wants standing approval to auto-accept offers, or when the inbound message tripped the safety-guard.
version: 0.1.0
author: velinussage
prerequisites:
  commands: [browser-harness]
metadata:
  hermes:
    tags: [shopping, facebook, marketplace, seller, messaging, reply-composer, negotiation, approval-gate, agent-led]
    related_skills:
      - facebook-marketplace-seller
      - facebook-marketplace-buyer-inbox-triage
      - facebook-marketplace-inbox-heartbeat
      - facebook-marketplace-message-sender
      - facebook-marketplace-safety-guard
      - facebook-marketplace-listing-intake
      - facebook-marketplace-listing-drafter
    requires_toolsets: [terminal]
---

# Facebook Marketplace Seller Reply Composer

Use this skill when a buyer has messaged one of the user's active listings and the user wants a drafted reply that's grounded in the listing facts, the seller's policy, and the tone of real Marketplace sellers. The skill is the seller-side counterpart to the buyer's `facebook-marketplace-negotiator`.

Every reply this skill produces routes through `facebook-marketplace-message-sender` for the actual send. The composer itself never types into a composer and never clicks Send.

## When to Use

Use this skill when:
- An inbound buyer message exists (captured by `facebook-marketplace-buyer-inbox-triage` or `facebook-marketplace-inbox-heartbeat`).
- The listing the buyer is asking about is known (URL or listing id).
- The user has set seller policy fields: `price` (asking), `floor` (min acceptable), `shipping` (local-pickup / ships / both), `hold_policy` (`no` / `with-deposit-via-platform` / `cash-on-pickup-only`).
- The user wants a tailored reply rather than a generic ping.

## Don't Use When

Do not use this skill when:
- The listing facts haven't been loaded yet — use `facebook-marketplace-listing-intake` first, or run this skill's own listing-context loader.
- The inbound message was tagged `suspicious` by `facebook-marketplace-safety-guard` — escalate to the user, don't draft a reply.
- The user wants standing approval to auto-accept any offer at or above floor — every send still goes through per-message approval via `message-sender`.
- The buyer's message is below the `kind: clarification-question` complexity (e.g. a one-word "interested") — these are usually templated by the inbox-triage skill directly, no composer pass needed.

## Core Principles

1. **Resolve listing context first.** Every reply is grounded in the listing's title, asking price, condition, location, ships/local-pickup policy, and any custom seller notes. The composer loads or caches `reports/listings/<listing_id>.json` before drafting.
2. **Match real Marketplace seller voice.** Short, casual, no marketing-speak, no excess pleasantries. "Hey — yes still here. $260 firm. Pickup Saturday OK?" is the model, not "Thank you so much for your interest in this beautiful Steelcase chair!"
3. **Policy-driven, not improvised.** Counters are computed via the seller-side offer ladder against the user's `floor`. Holds are accepted only when policy says so. Shipping is offered only when listed `ships` or `both`.
4. **Safety-guard both sides.** The inbound message gets scanned for scam/off-platform asks first; the drafted outbound variants get scanned before surfacing to the user. A drafted variant that suggests off-platform contact (rare but possible) is dropped.
5. **Per-message approval, always.** The composer surfaces variants; the user picks one; `message-sender` requires its own `approval_token` for the actual send.
6. **Tone parity beats response-rate optimization.** Don't pad replies to seem "professional." Real Marketplace sellers reply in 3–15 words most of the time. Mirror that.

## Procedure

### 1. Load or refresh listing context

Before drafting, ensure `reports/listings/<listing_id>.json` exists and is fresh. The cache structure:

```json
{
  "listing_id": "2051040935507757",
  "listing_url": "https://www.facebook.com/marketplace/item/2051040935507757/",
  "title": "Steelcase Leap V2 office chair",
  "asking_price": 260,
  "floor": 220,
  "condition": "Used - Good",
  "condition_notes": "Some scuffs on base, fully working tilt and lumbar.",
  "location": "Greensboro, NC",
  "shipping": "local-pickup",
  "hold_policy": "cash-on-pickup-only",
  "delivery": "no",
  "custom_notes": "Saturday pickups preferred; can do weekday evenings after 6.",
  "cached_at": "2026-05-19T08:00:00-04:00"
}
```

If the file is missing or `cached_at` is more than 7 days old, refresh it by opening the listing page:

```bash
browser-harness <<'PY'
ensure_real_tab()
new_tab(LISTING_URL)
wait(3)
facts = js("""
  (() => {
    const text = document.body.innerText || '';
    const url = location.href;
    const is_item = /\\/marketplace\\/item\\//i.test(url);
    const title = document.querySelector('h1')?.innerText?.trim() || null;
    const price_match = text.match(/\\$([0-9][0-9,]*)/);
    const asking_price = price_match ? parseInt(price_match[1].replace(/,/g, ''), 10) : null;
    // Condition often appears as "Condition: Used - Good" or in the description block.
    const cond_match = text.match(/Condition:?\\s*([A-Za-z][A-Za-z\\s\\-]+?)(?:\\n|$)/i);
    const condition = cond_match ? cond_match[1].trim() : null;
    // Location appears under the listing title, format "City, ST" or "in City, ST".
    const loc_match = text.match(/\\b([A-Z][a-z]+(?:\\s+[A-Z][a-z]+)*),\\s*([A-Z]{2})\\b/);
    const location = loc_match ? loc_match[0] : null;
    // Shipping policy is in the listing if the seller offered shipping.
    const ships = /Shipping available|Ships to|This item ships/i.test(text);
    const local_only = /Local pickup only|Pickup only/i.test(text);
    return { is_item, title, asking_price, condition, location, ships, local_only };
  })()
""")
print(facts)
js("window.close()")
PY
```

Merge the extracted facts with the user's policy fields (`floor`, `hold_policy`, `delivery`, `custom_notes`) — those come from the user, not the page. Write the merged record back to `reports/listings/<listing_id>.json`.

The seller's `floor` and `hold_policy` are user-supplied; the composer must ask for them if the file is being created fresh and they aren't already known. Without `floor`, the offer-ladder math can't run.

### 2. Run safety-guard on the inbound

Pass the inbound message to `facebook-marketplace-safety-guard`:

```json
{
  "text": "<inbound_text>",
  "direction": "inbound",
  "listing_policy": { "shipping": "<from-cache>", "price": <asking_price> }
}
```

If the guard returns `blocked` AND `is_scam_pattern: true`, escalate to the user — do not draft a reply. Surface the `suggested_user_message` from the guard.

If the guard returns `blocked` for an off-policy ask (e.g. shipping ask on a local-pickup listing), draft a polite-but-firm decline using the inbound-pattern catalog below; the inbound isn't necessarily a scam, just a policy mismatch.

If the guard returns `warn`, surface the warning to the user as context but still proceed to draft.

### 3. Classify the inbound pattern

Match the inbound against the catalog:

| Inbound pattern | Approved reply scaffold |
|---|---|
| "Is this still available?" / "Still available?" / "Available?" | "Yes, still available. Pickup in [city], [days/times]." |
| "Will you take $X?" with `X < floor` | "Thanks for the offer — I'm holding at $[asking] for now." |
| "Will you take $X?" with `X >= floor` AND `X < asking` | "[Counter at midpoint] would work. Pickup [window]?" |
| "Will you take $X?" with `X >= asking` | "Yes that works. When can you pick up?" |
| "Can you ship?" / "Will you ship?" (listing is local-pickup) | "Local pickup only, sorry." |
| "Can you ship?" (listing is `ships` or `both`) | "Yes, ships via [carrier]. Shipping is $[X] on top." (If exact shipping cost isn't set, surface a draft-only placeholder the user fills in.) |
| "Can you deliver?" | Policy-driven: if `delivery: yes-within-X-miles`, "I can deliver within [X] miles for $[fee], otherwise local pickup." If `delivery: no`, "Local pickup only — happy to meet at [public location] if that helps." |
| "Will you trade?" / "Open to trades?" | "Cash only on this one, thanks." |
| "What's your lowest?" / "Last price?" / "Best price?" | "$[asking] is the price for now." (Don't pre-discount on an open-ended ask; the buyer hasn't offered.) |
| "Meet halfway?" / "Where can we meet?" | "Could meet at [public-location-suggestion, e.g. police station / Target parking lot near listing area]." |
| "Can you hold until [date]?" | Policy-driven: `hold_policy: no` → "Sorry, first-come first-served on pickup." `hold_policy: with-deposit-via-platform` → "Happy to hold with a small deposit via Marketplace [platform-payment]." `hold_policy: cash-on-pickup-only` → "I don't do holds, but it's still here right now." |
| "Cash on pickup OK?" | "Yes, cash on pickup." |
| "How does pickup work?" / "What's the address?" | "I'll send the pickup location once we set a time. What window works for you?" (Don't share address before time is locked.) |
| "Does it work?" / "Any issues?" | Restate the condition_notes from the listing cache. |
| "Can I see more pictures?" | "[If extra photos exist] Sure, what angles?" / "[If listing already has the photos] What's in the listing is what I've got." |

If the inbound doesn't match any pattern, classify as `clarification-question` and surface the inbound text to the user with a "draft from scratch?" prompt — the catalog covers maybe 80% of inbound shape; the rest deserve human attention.

### 4. Compute counter math (seller-side ladder)

When the inbound is `Will you take $X?` with `X >= floor` AND `X < asking`:

```
counter = ceil((asking + X) / 2)
counter = max(counter, floor + ((asking - floor) * 0.25))   # never counter at < 25% of the spread from floor
counter = min(counter, asking - 5)                          # always counter at least $5 below asking, to feel like movement
```

For example, `asking = 260`, `floor = 220`, buyer offers `$225`:
- midpoint = `(260 + 225) / 2 = 242.5` → `243`
- `floor + 25%-of-spread = 220 + 10 = 230` → counter is `max(243, 230) = 243`
- cap = `asking - 5 = 255` → final counter = `min(243, 255) = 243`

The reply is `"Could do $243 with same-day pickup. Want to set up a time?"` — anchored, short, conditional.

When the buyer offers exactly `floor`, accept rather than counter: `"$220 works. When can you pick up?"` — countering at floor signals the floor isn't real.

When the buyer offers `>= asking`, accept and pivot to pickup: `"Yes that works. When can you pick up?"`.

When the buyer offers below `floor`, hold firm at `asking` (not at a midpoint) to keep negotiation room: `"Thanks for the offer — I'm holding at $260 for now."`

### 5. Tone parity rules

Apply these to every drafted variant:

1. **3–15 words preferred; 25 hard ceiling.** Sellers don't write paragraphs. If the draft exceeds 25 words, cut.
2. **No "Thank you so much for your interest."** Replace with "Thanks for the offer" or omit entirely.
3. **No emoji** unless the user explicitly opted in. Marketplace sellers don't use them by default.
4. **No exclamation points** except on "Cash on pickup OK?" → "Yes, cash on pickup." style confirmations (still optional). Excited punctuation reads as sales-bot.
5. **Use "—" sparingly.** One per message max; helps separate clauses ("Hey — yes still here.").
6. **Address the buyer's actual ask first**, then the seller-side context. "Yes, still available. Local pickup only." not "Local pickup only. Yes, still available."
7. **End with a forward-motion question** when the thread is going somewhere ("When can you pick up?" / "Want to set up a time?"). Don't end with a question when declining (no need to invite re-engagement on a firm decline).

### 6. Draft 2–3 variants

For each inbound pattern, produce 2–3 drafted variants that all follow the tone rules but offer the user choice on register (slightly more vs. less terse, more vs. less directive).

Example — buyer asks "Still available?":

```
[1] Yes, still available. Pickup in Greensboro, weekends or weekday evenings.
[2] Yep — still here. When were you thinking for pickup?
[3] Yes. Want to set up a pickup time?
```

Example — buyer offers $225 on a $260 listing with $220 floor:

```
[1] Could do $243 with same-day pickup. Want to set up a time?
[2] Best I can do is $245. Could meet this weekend.
[3] $250 and we have a deal — pickup this week works.
```

### 7. Safety-guard each variant

Pass each variant through `facebook-marketplace-safety-guard` with `direction: outbound` and the listing policy. Drop any variant that returns `blocked` or `warn` — that's a sign the draft accidentally proposed off-platform contact, shared an address prematurely, or violated listing policy. (This is rare for the catalog scaffolds above, but the LLM-driven counter math can occasionally produce a draft like "I can Venmo you a refund if it doesn't work out" — the guard catches this.)

### 8. Surface variants for user approval

Present the variant block to the user along with the inbound context:

```
Listing: Steelcase Leap V2 — $260 asking, $220 floor, local-pickup
Buyer message: "Will you take $225?"
Pattern matched: counteroffer (X >= floor, X < asking)
Counter math: midpoint $243, floor-+25%-spread $230, capped at $255 → counter $243

Variants:
  [1] Could do $243 with same-day pickup. Want to set up a time?
  [2] Best I can do is $245. Could meet this weekend.
  [3] $250 and we have a deal — pickup this week works.

Pick [1/2/3] to surface for final approval, [e] to edit, or [s] to skip.
```

### 9. Route to message-sender

Once the user picks a variant (and produces the `approval_token` for the send), call `facebook-marketplace-message-sender`:

```json
{
  "thread_url": "<thread_url>",
  "exact_text": "<chosen_variant>",
  "approval_token": "<user-provided>",
  "listing_url": "<listing_url>",
  "role": "seller",
  "state_path": "reports/threads/<thread_id>.json",
  "kind": "counter" | "available" | "decline-shipping" | "decline-hold" | "accept" | "clarify"
}
```

The `kind` field is drawn from the pattern catalog match — it stamps the outbound record so future runs (e.g. the seller-side equivalent of buyer-thread-timeout) can reason about what was sent.

### 10. Update state

After `message-sender` confirms the bubble, the thread JSON gets the outbound entry. This composer doesn't write to thread JSON directly — that's `message-sender`'s job.

If the user picked `[e]` to edit, capture the edited text, re-run safety-guard on it, and proceed to surface as a single variant for final approval. If the user picked `[s]`, log the skip with the inbound text so the next pass knows it's unanswered.

## Output Contract

This skill returns:
- For each pending inbound: the matched pattern, the counter math (when relevant), 2–3 drafted variants, and a user choice.
- For each chosen variant: a `message-sender` invocation.
- For freshly loaded listings: an updated `reports/listings/<listing_id>.json`.
- For each run, a one-line summary: `inbound classified: N, drafted: X, sent: Y, escalated: Z`.

## Approval Policy

- **Per-message approval, never standing.** Even with the user's clear policy fields, every reply still surfaces for per-message approval before `message-sender` runs.
- **Floor is canon.** Counters never drop below `floor`; accepts never trigger below `floor`.
- **Shipping is policy-gated.** If the listing is `local-pickup`, no draft offers shipping — period.
- **Address is never shared before time is locked.** Even when the buyer asks "what's the address?", the default reply is "I'll send the pickup location once we set a time."
- **Holds follow `hold_policy` strictly.** "Hold for me until next week" doesn't get a yes unless policy says so.
- **No deposit accepted from buyer, ever, in this skill.** `hold_policy: with-deposit-via-platform` means a deposit *through* the Marketplace platform's official payment rail, not Venmo/Zelle/cash deposit. This is a hard rule — agents commonly soften this and it must not happen.

## Anti-patterns

- **Don't auto-accept on the first run-through.** Even a buyer offering exactly the asking price gets a "Yes that works. When can you pick up?" reply — not a "DEAL!" send.
- **Don't pre-discount on open-ended asks.** "What's your lowest?" doesn't deserve a number; it deserves "$[asking] is the price for now."
- **Don't volunteer information.** If the buyer didn't ask about delivery, don't mention it. Replies should be short and answer only the ask.
- **Don't soften the floor.** If the buyer is below floor, hold at asking — countering toward floor on a low offer signals there's room to push further down.
- **Don't propose meeting at the seller's home.** Default meetup is a public location (Target parking lot, police station, fire station) until the user explicitly opted into home pickup.
- **Don't add "let me know if you have questions" as a closer.** That's email tone, not Marketplace tone.

## Pitfalls

- **Listing facts can drift between cache writes.** A user may drop the price on their listing and forget to update the cache. Step 1's refresh check (cache > 7 days old) catches some of this; an explicit `?force-refresh` toggle handles the rest.
- **The buyer's `$X` parse can be ambiguous** ("would $200 with shipping work?" — is that $200 inclusive or before shipping?). When ambiguous, the variant surfaces the ambiguity ("Are you including shipping in that?") rather than guessing.
- **A multi-question inbound** ("Is this available? What's the condition? Any pictures of the base?") deserves a compact reply that addresses all three, not three separate sends. The composer batches by default.
- **Floor mid-thread changes.** If the user lowers the floor mid-negotiation, the cached floor is stale. Always read fresh from `reports/listings/<listing_id>.json` on each run.
- **"Cash on pickup OK?" is sometimes asked sarcastically** ("Cash on pickup OK, right? Or do you want me to Venmo you?") — the second part is the scam pivot. Always run safety-guard on inbound before classifying as a confirmation question.
- **Don't propose specific pickup times unless the user supplied availability.** The catalog scaffolds use placeholders like "weekends or weekday evenings" rather than committing to a specific day the user might not be free.

## Verification

Before reporting success, verify:
- Listing context was loaded from `reports/listings/<listing_id>.json` (fresh or cached < 7 days).
- The inbound message ran through `facebook-marketplace-safety-guard` (direction: inbound) before drafting.
- The inbound was classified against the pattern catalog; an unmatched inbound was escalated for user attention rather than guessed at.
- Counter math, when relevant, respected `floor` and didn't propose anything below it.
- Every drafted variant was 25 words or fewer.
- Every drafted variant ran through safety-guard (direction: outbound) and any blocked/warn variants were dropped.
- The user picked a variant explicitly; no default-pick.
- The send routed through `facebook-marketplace-message-sender` with a per-message `approval_token` and `role: "seller"`.
- No address, phone, or off-platform contact was suggested by the drafted text.
- The cached listing context wasn't written before the send confirmed (state correctness is `message-sender`'s job).
