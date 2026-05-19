# Commerce / Facebook Marketplace Collection

This folder contains the buyer-side and seller-side Facebook Marketplace skills for any coding-agent host (Claude Code, Codex, Hermes, etc.).

The collection is designed around one practical idea:
- the operator should not have to load the whole workflow at once
- the agent should retrieve the narrow capability that matches the current stage
- the workflow still needs continuity across stages through a shared deal-state surface

## Collections

### Buyer-side flow

```text
facebook-marketplace-buyer
├── Stage 0 — algorithmic feed scroll (Browse All, no query, skips interest gate)
├── facebook-marketplace-history-seed   (also feeds Stage 0 as recency-weighted bias)
├── facebook-marketplace-scout
├── facebook-marketplace-watch-notifier
├── facebook-marketplace-deal-assessor  (IMV/SCOPE pricing stack per card)
├── facebook-marketplace-seller-communication  (per-message approval gate)
├── facebook-marketplace-buyer-inbox-watcher   (Stage 4b — reply detection + intent classification)
├── facebook-marketplace-buyer-thread-timeout  (Stage 4c — stalled-thread nudge / raise / abandon)
├── facebook-marketplace-negotiator
└── facebook-marketplace-pickup-manager
```

Use when:
- the user is shopping on Marketplace
- the user wants ambient discovery via the Browse-All algorithmic feed, or a shortlist / pricing / negotiation / pickup help
- the user has not yet committed to buy

User-editable filters live alongside the buyer skill:
- `reports/.scout_block_list.txt` — hard-exclude category patterns (gowns, costumes, MLM, vape, crypto/NFT, weight-loss, etc.) applied before scoring

### Seller-side flow

```text
facebook-marketplace-seller
├── facebook-marketplace-listing-intake
├── facebook-marketplace-listing-drafter
├── facebook-marketplace-publish-manager
├── facebook-marketplace-buyer-inbox-triage
├── facebook-marketplace-seller-reply-composer  (Stage 5b — per-inbound reply with listing context)
└── facebook-marketplace-inbox-heartbeat
```

Use when:
- the user is selling on Marketplace
- the listing needs to go from intake to publish to inbox management
- active chats and in-progress sales need to stay ordered and legible

## Shared runtime rules

### 1. Default to operator-first
By default, the runtime should ask the user before:
- publishing a listing
- sending the first message
- sending a counteroffer
- confirming pickup
- changing committed terms
- resolving unclear queue / sale-state ambiguity

### 2. Active chats must be visible
The collection should support a durable view of:
- active chats
- queue order
- who is primary vs backup
- where each in-progress sale stands
- what the next operator action is

The minimum state surface is documented in:
- `../../docs/deal-state-template.md`
- `../../docs/state-management.md`

The concrete browser UI surface is documented in:
- `../../docs/facebook-marketplace-ui-runbook.md`

### 3. Autonomous mode is bounded, not implied
Autonomous mode is allowed only when the user has explicitly provided:
- price policy
- hold policy
- approved windows / availability policy
- blocked actions
- escalation triggers
- open-gateway path back to the user for clarification

If those are missing, the system should ask the user for more clarity instead of improvising.

### 4. Buyer and seller collections should share the same philosophy
The repo is not trying to automate everything.
It is trying to make noisy Marketplace workflows:
- more legible
- more policy-bound
- more retrievable at the right stage
- safer to hand off in bounded slices

## Skill index

### Top-level coordinators
- `facebook-marketplace-buyer`
- `facebook-marketplace-seller`

### Shared (cross-side) skills
- `facebook-marketplace-message-sender` — outbound-send executor; required per-message `approval_token`
- `facebook-marketplace-safety-guard` — pre-send + inbound classifier (off-platform / deposit / identity / scam)

### Buyer-side specialist skills
- `facebook-marketplace-history-seed`
- `facebook-marketplace-scout`
- `facebook-marketplace-watch-notifier`
- `facebook-marketplace-deal-assessor`
- `facebook-marketplace-seller-communication`
- `facebook-marketplace-negotiator`
- `facebook-marketplace-pickup-manager`
- `facebook-marketplace-buyer-inbox-watcher` (Stage 4b)
- `facebook-marketplace-buyer-thread-timeout` (Stage 4c)

### Seller-side specialist skills
- `facebook-marketplace-listing-intake`
- `facebook-marketplace-listing-drafter`
- `facebook-marketplace-publish-manager`
- `facebook-marketplace-buyer-inbox-triage`
- `facebook-marketplace-inbox-heartbeat`
- `facebook-marketplace-seller-reply-composer` (Stage 5b)

## Good default validation

```bash
hermes chat -q "Use the facebook-marketplace-buyer skill and summarize the buy-side workflow in 5 bullets." -s facebook-marketplace-buyer
hermes chat -q "Use the facebook-marketplace-seller skill and summarize the seller-side workflow in 5 bullets." -s facebook-marketplace-seller
hermes chat -q "Use the facebook-marketplace-inbox-heartbeat skill and explain how active chats should be tracked." -s facebook-marketplace-inbox-heartbeat
```

## Related docs

- `../../README.md`
- `../../docs/architecture.md`
- `../../docs/local-validation.md`
- `../../docs/facebook-marketplace-ui-runbook.md`
- `../../docs/state-management.md`
- `../../docs/deal-state-template.md`
- `../../docs/facebook-marketplace-inbox-policy.md`
- `../../examples/`
