# Architecture

## Goal

Provide any coding-agent host (Claude Code, Codex, Hermes, etc.) with a reusable Marketplace operations collection that can:

1. discover listings
2. benchmark value
3. reason about offers
4. manage buyer/seller conversations
5. coordinate publish and pickup stages safely
6. keep active chats and in-progress sales legible over time
7. default to operator confirmation when ambiguity appears
8. support bounded autonomous mode only when the user has defined clear rules

## Repo graph

### Buyer-side graph

```text
facebook-marketplace-buyer
├── facebook-marketplace-history-seed
├── facebook-marketplace-scout
├── facebook-marketplace-watch-notifier
├── facebook-marketplace-deal-assessor
├── facebook-marketplace-seller-communication
├── facebook-marketplace-negotiator
└── facebook-marketplace-pickup-manager

borrowed source for history seeding:
chromehistory-to-facebookmarketplace / wishlist
```

### Seller-side graph

```text
facebook-marketplace-seller
├── facebook-marketplace-listing-intake
├── facebook-marketplace-listing-drafter
├── facebook-marketplace-publish-manager
├── facebook-marketplace-buyer-inbox-triage
└── facebook-marketplace-inbox-heartbeat
```

### Shared continuity surface

```text
docs/deal-state-template.md
├── active chats
├── primary / backup queue order
├── pricing mode and hold policy
├── approved windows / availability policy
├── next operator action
└── open-gateway clarification points
```

## Why multiple narrow skills

This repo uses multiple focused skills instead of one monolith because:
- search and ranking require different logic than negotiation
- notification routing has different concerns than browsing
- deal assessment needs deeper pricing logic than first-pass scouting
- seller communication needs a different tone and approval model than pure analysis
- pickup scheduling has different safety constraints than scouting
- seller-side inbox management is a different runtime problem than buy-side outreach
- active chats and in-progress sales need continuity, not just one-shot prompts
- small skills route better and are easier to test
- the agent can preload only the stage it needs

## Approval model

### Default mode: operator-first

Allowed autonomously:
- open Marketplace
- run searches
- collect listing metadata
- deduplicate listings
- score and rank listings
- compare price bands
- draft negotiation messages
- draft pickup plans
- draft publish actions
- classify inbox threads
- update local notes or summaries
- track active chats and in-progress sales locally

Allowed only after explicit user approval:
- send the first seller message
- send a counteroffer
- publish a listing
- share phone number
- share precise pickup details
- confirm a pickup time or location
- tell a seller or buyer the deal is definitely closed
- commit to a hold outside pre-approved rules

Never allowed:
- send deposits
- send payments
- leave Facebook Marketplace for payment handling without explicit, separate user instruction
- disclose sensitive identity details automatically

## Autonomous mode

Autonomous mode should exist only when the user opts into it and defines a clear policy.

Required policy fields:
- fixed-price vs negotiable mode
- minimum acceptable price / offer range
- hold policy
- approved pickup windows or explicit availability check rule
- queue rule (for example: first real pickup wins)
- blocked actions
- escalation triggers
- open-gateway path to the user for clarification

Design rule:
- when policy is incomplete, ask the user through open gateways instead of improvising
- autonomous mode is bounded execution, not general discretion

## Active chats and in-progress sales capability

This repo should explicitly support a runtime capability for:
- checking active chats
- summarizing which threads are live
- ranking the current queue
- showing which sales are in progress
- showing what is waiting on the user vs what is waiting on the counterparty

The seller-side mechanism for this is:
- `facebook-marketplace-inbox-heartbeat`
- plus a durable local deal-state surface from `docs/deal-state-template.md`

This is critical because Marketplace work is not just retrieval and messaging. It is continuity under changing state.

## Optional history-informed scouting

The Marketplace stack can optionally borrow the local `wishlist` skill from the `chromehistory-to-facebookmarketplace` library.

The local bridge skill for that is:
- `facebook-marketplace-history-seed`

That skill is useful for:
- extracting prior Facebook Marketplace searches from Chrome history
- extracting prior Marketplace listing visits
- recovering repeated brand/model vocabulary from shopping research
- seeding tighter Marketplace queries before live scouting begins

Design rule:
- history is a search-seeding signal, not a source of truth
- the explicit current brief wins over stale history
- old Marketplace searches should be surfaced back to the user when intent is ambiguous

## Runtime assumptions

- `browser-harness` is installed and on `PATH`
- Chrome is running
- the user is already logged into Facebook in a real browser profile
- browser-harness has been attached to that browser successfully at least once
- the coding-agent host (Hermes, Claude Code, Codex, etc.) is configured to scan this repo's `skills/` directory for `SKILL.md` files

## Publication hygiene

Before sharing this repo publicly or through Sage:
- remove author-local absolute paths and one-off listing artifacts
- keep runtime assumptions generic and fork-friendly
- separate reusable workflow truth from one operator's browser/session state
- use `docs/publication-sanitization-checklist.md` before publication

## Durable state requirement

The collection should be able to preserve and reload the minimum state needed to continue work safely.

That includes:
- listing identifier
- current stage
- active chats
- primary / backup ordering
- offers and price mode
- approval state
- availability windows
- what still needs clarification from the user

Proposed template:
- `docs/deal-state-template.md`

## Test strategy

### Stage 1 — structural
- the agent can discover the skills from this repo's `skills/` directory
- the agent can preload each skill by name
- the agent can summarize the workflow and approval gates correctly

### Stage 2 — browser-ready
- browser-harness health checks report Chrome running
- browser-harness can attach to the logged-in browser successfully
- the agent can reason about how it would execute each skill without sending messages

### Stage 3 — supervised live trials
Buyer side:
- history-seed only
- scouting only
- post-scout notification summary only
- deal-assessment only
- seller-communication drafting only
- draft-only negotiation
- pickup-plan drafting only

Seller side:
- listing intake only
- listing draft only
- publish preparation only
- inbox triage summary only
- heartbeat summary over active chats only
- operator-approved first reply only
- operator-approved publish only

### Stage 4 — bounded autonomous trials
Only after policy is explicit:
- autonomous inbox classification
- autonomous queue updates
- autonomous draft replies inside policy
- automatic clarification requests routed to the user through open gateways whenever policy/state becomes incomplete
