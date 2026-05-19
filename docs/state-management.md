# Marketplace State Management

Marketplace work often spans multiple sessions. State files keep active buyer deals, seller listings, inbox queues, and pending approvals legible without relying on chat memory.

## Storage location

For reusable examples, use `examples/state/`:
- `examples/state/deal-state-filled-example.md` — synthetic buyer deal continuity example
- `examples/state/seller-listing-state-example.md` — synthetic seller listing / inbox policy state example

For real local operator runs, use a gitignored runtime directory outside published examples, such as `.local-state/marketplace/`.

Do not commit real buyer/seller names, phone numbers, addresses, private messages, or listing artifacts.

## File naming

Use stable, non-sensitive identifiers:

```text
buyer-{product-family}-{YYYYMMDD}.md
seller-{item-family}-{YYYYMMDD}.md
inbox-{listing-short-id}-{YYYYMMDD}.md
```

If using a real Marketplace listing ID locally, keep it in `.local-state/`, not in public examples.

## Buyer deal schema

```markdown
# Buyer Deal State

## Meta
- state_id:
- created_at:
- updated_at:
- mode: read-only | draft-only | approval-gated | bounded-auto
- source_skill:

## Buying brief
- product_family:
- must_have:
- nice_to_have:
- budget_target:
- hard_stop:
- radius:
- pickup_constraints:

## Candidate listings
| status | title | price | location | url | notes |
|---|---|---:|---|---|---|

## Current lead
- listing_url:
- seller_status:
- condition_questions:
- target_offer:
- max_offer:
- approved_message_text:
- approval_status:

## Next action
- waiting_on_user:
- waiting_on_seller:
- recommended_next_step:
```

## Seller listing schema

```markdown
# Seller Listing State

## Meta
- state_id:
- created_at:
- updated_at:
- mode: read-only | draft-only | approval-gated | bounded-auto
- source_skill:

## Listing facts
- item_title:
- condition:
- known_flaws:
- included_parts:
- test_status:
- photos_status:

## Pricing policy
- list_price:
- fixed_or_negotiable:
- floor_price:
- price_drop_policy:
- hold_policy:

## Publish state
- status: intake | drafted | form-prepared | published | paused | sold
- title:
- description:
- category:
- location_scope:
- review_gate:

## Inbox queue
| queue_status | buyer_alias | offer | pickup_window | last_message_summary | next_action |
|---|---|---:|---|---|---|

## Approvals
- publish_approved:
- auto_reply_policy:
- blocked_actions:
- escalation_triggers:
```

## Update rules

Update state when a shortlist is created, a lead becomes worth messaging, a draft is approved/sent, a reply changes deal state, a listing draft is created, publish state changes, inbox queue order changes, or pickup windows are proposed/confirmed.

## Reload procedure

At the start of a new session:
1. identify buyer-side or seller-side task
2. ask for or locate the relevant state file
3. summarize current stage and approvals
4. list what is waiting on the user vs counterparty
5. continue only inside the recorded mode and policy

## Cross-session resume test

Create a synthetic or local state file, start a new coding-agent session (Hermes, Claude Code, Codex, etc.), load the relevant top-level skill, ask the agent to resume from the state file, and verify it identifies current stage, blocked actions, next action, and approval state without inventing missing details.
