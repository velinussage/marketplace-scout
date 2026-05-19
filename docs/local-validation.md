# Local Validation

This file records what has actually been validated locally in the Hermes environment.

It is intentionally narrower than a full QA claim.
It separates:
- structural skill loading
- runtime assumptions
- browser readiness
- live Facebook execution paths that are still unproven

## Validation date

- 2026-04-23

## Environment

### Commands present
- `browser-harness`: present on `PATH`
- `python3`: present on `PATH`
- `hermes`: present on `PATH`

### `browser-harness --doctor`
Observed:
- Chrome running: OK
- daemon alive: OK
- optional cloud/profile sync features missing

Interpretation:
- local browser path is available for real-browser testing
- cloud-browser features are not required for local Marketplace work

## Hermes structural load tests

Method:
- each Marketplace skill was loaded via `hermes chat -q ... -s <skill>`
- prompt asked Hermes to summarize the skill’s core job and approval gates

Result:
- all 14 Marketplace skills loaded successfully for reasoning/summarization

Skills verified this way:
- facebook-marketplace-buyer-inbox-triage
- facebook-marketplace-buyer
- facebook-marketplace-deal-assessor
- facebook-marketplace-history-seed
- facebook-marketplace-inbox-heartbeat
- facebook-marketplace-listing-drafter
- facebook-marketplace-listing-intake
- facebook-marketplace-negotiator
- facebook-marketplace-pickup-manager
- facebook-marketplace-publish-manager
- facebook-marketplace-scout
- facebook-marketplace-seller-communication
- facebook-marketplace-seller
- facebook-marketplace-watch-notifier

## Browser/UI probe results

Attempted browser-harness smoke probes:
- `ensure_real_tab()`
- Marketplace home: `https://www.facebook.com/marketplace/`
- Marketplace inbox: `https://www.facebook.com/marketplace/inbox`
- direct item link open for a live listing
- message-composer visibility check for a live listing without sending

Observed result after fixing browser-harness auto-reconnect behavior:
- `ensure_real_tab()` succeeds
- Marketplace home opens successfully at `https://www.facebook.com/marketplace/`
- Marketplace inbox opens successfully at `https://www.facebook.com/marketplace/inbox`
- a direct item link opened successfully for a live Marketplace listing
- the listing exposed a live message composer surface tied to the user's logged-in Facebook session
- Facebook may prefill a default opener, confirming that seller outreach would post as the user account if approved and sent
- no message was sent during validation
- the prior `RuntimeError: no close frame received or sent` failure was traced to a stale CDP websocket inside the still-alive daemon process

Interpretation:
- local structural skill loading is verified
- live Marketplace UI smoke testing is no longer blocked by the browser-harness transport/session issue
- direct-listing / bookmarked-link entry into buyer-side seller-communication is viable in this environment
- buyer-side and seller-side live workflow validation can proceed from this environment

## What is proven

Proven:
- skills are structurally loadable in local Hermes
- Hermes can reason over the skills and restate their approval model
- the buyer-side and seller-side collections are legible as routed stage-specific capabilities

## What is not yet proven

Not yet proven:
- end-to-end live browser execution for every skill against Facebook Marketplace UI
- successful listing publish in live Marketplace
- successful inbox triage in a live Marketplace seller inbox
- successful heartbeat state tracking over multiple active chats in the live UI
- notification delivery in scheduled recurring watch runs
- durable state reload across sessions using a shared state artifact

## Next validation passes

### Pass A — buyer-side supervised live browser tests
- history-seed with real local browsing traces
- scout with real Marketplace logged-in browser
- deal-assessor on real shortlist output
- seller-communication draft on a real listing
- pickup-manager draft on a real negotiation state

### Pass B — seller-side supervised live browser tests
- listing intake from a real item
- listing drafter against real facts
- publish-manager form-fill dry run
- buyer-inbox-triage against live inbox threads
- inbox-heartbeat summary over active chats and in-progress sales

### Pass C — continuity tests
- fill `docs/deal-state-template.md`
- reload state in a new Hermes session
- verify queue order / active chats / next-action continuity

## Open blockers / missing pieces

- no dedicated local validation artifact existed before this file
- no repo-level durable state template existed before `docs/deal-state-template.md`
- active chats and in-progress sales need a more explicit documented continuity surface
- autonomous mode needs explicit policy plus open-gateway clarification behavior documented in the repo-level docs
