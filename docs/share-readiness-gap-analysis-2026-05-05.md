# Facebook Marketplace skill share-readiness gap analysis

Date: 2026-05-05

Reference inspected:
- `/tmp/browser-harness-1778014273/agent-workspace/domain-skills`
- Source: https://github.com/browser-use/browser-harness/tree/main/agent-workspace/domain-skills

Local repo inspected:
- this repo (`marketplace-scout`)

## Executive summary

The local Marketplace skill repo is strong as an operating policy / workflow philosophy layer, but it is not yet as usable as the browser-harness domain-skill examples because it lacks enough field-tested browser execution detail.

The reference domain skills are mostly concrete runbooks: URLs, selectors, DOM anchors, extraction snippets, failure signatures, rate-limit notes, self-inspection blocks, and copy-pasteable code. The Marketplace repo is mostly stage-routing, approval policy, judgment, and messaging tone. That is valuable, but a new user or agent cannot reliably execute it without rediscovering Facebook Marketplace UI details.

Main missing layer:

> A concrete `facebook-marketplace-ui.md` / `browser-harness-recipes.md` reference with verified Marketplace URL patterns, DOM anchors, extraction snippets, form-fill recipes, inbox extraction recipes, failure modes, and smoke tests.

## What high-quality browser-harness domain skills do

Patterns observed in reference skills such as Craigslist, eBay, Amazon, Facebook Groups/Pages, Zillow, and Shopify Admin:

1. State exactly what was field-tested and when.
2. Separate `what works` from `what does not work`.
3. Provide canonical URL patterns and query parameters.
4. Document DOM anchors / selectors / HTML structures.
5. Include complete extraction snippets in Python or JS.
6. Include known failure signatures: CAPTCHA, 403, bot block pages, lazy loading, stale tabs, controlled inputs, disabled save buttons.
7. Provide rate-limit / pacing discipline.
8. Include self-inspection blocks for when selectors break.
9. Prefer direct HTTP when possible and browser automation only when needed.
10. Show verification conditions: how to know an action actually succeeded.

## Current Marketplace repo strengths

The local repo already has:

- good top-level buyer/seller skill separation
- strong approval and safety model
- good stage routing
- clear “not an unattended bot” framing
- useful seller-side continuity concept
- publication sanitization checklist
- local validation doc
- deal-state template
- sharing/positioning reference
- good messaging tone guidance
- bounded autonomous mode concept

These are the strategic pieces most browser-harness examples do not have.

## Readiness gaps

### P0 — Missing field-tested Facebook Marketplace UI runbook

The repo does not yet contain a reference like the browser-harness `facebook/groups.md` or `shopify-admin/polaris-inputs.md` files for Marketplace itself.

Needed file:

- `skills/commerce/facebook-marketplace-buyer/references/local/facebook-marketplace-ui.md` or shared `docs/facebook-marketplace-ui-runbook.md`

It should include:

- Marketplace home/search URL patterns
- item detail URL patterns
- inbox URL patterns
- seller listing creation URL patterns
- search result card selectors
- item detail selectors
- message composer selectors
- listing publish form selectors
- inbox thread selectors
- stable text anchors
- screenshot-first debugging pattern
- self-inspection JS blocks
- exact failure signatures
- verification checks after read/write actions

### P0 — Skills reference `browser-harness`, but the shareable ecosystem points at browser-use/browser-harness without setup clarity

Current skill frontmatter requires `browser-harness`, but the public browser-use CLI skill in Hermes uses `browser-use`. Both are installed locally, but a recipient may not know which one to use.

Observed locally on 2026-05-05:

- `browser-use doctor`: 4/5 checks passed; cloudflared missing only for tunnel features.
- `browser-harness --doctor`: Chrome running OK, but daemon alive failed; setup required.

Needed:

- update README setup to distinguish `browser-use` CLI vs `browser-harness`
- add exact setup commands
- add `browser-harness --setup` as required before live Marketplace work
- add a smoke test command and expected output
- avoid claiming browser-harness is currently ready unless doctor passes

### P0 — No copy-pasteable execution snippets

Reference skills are useful because an agent can copy code directly. Marketplace skills mostly describe what to do, not how to do it.

Needed snippets:

- open Marketplace home/inbox/direct listing in real Chrome
- detect logged-in vs login wall
- search Marketplace and collect visible result cards
- scroll-and-collect without losing virtualized cards
- open item detail in a new tab
- extract title, price, location, seller name, description, image count, posted time, availability indicators
- detect and replace Facebook prefilled opener
- draft-only message composer flow
- publish form dry-run fill
- inbox thread extraction and queue summarization

### P0 — No durable state implementation path

There is a `docs/deal-state-template.md`, but no operational convention for where state files live, how they are named, how they are loaded, or when they are updated.

Needed:

- `state/README.md` or `docs/state-management.md`
- schema for buyer deal state and seller listing state
- file naming convention, e.g. `state/listings/<listing-id>.md` or `.json`
- create/update/load procedure
- examples filled with fake/sample data
- cross-session resume test

### P1 — No sample fixtures / example outputs

Shareable skills need examples that let users understand the artifact without touching a real Facebook account.

Needed:

- sample buyer brief
- sample scout output
- sample deal assessment
- sample seller listing intake
- sample generated listing
- sample inbox triage summary
- sample heartbeat update
- sample deal-state file

Use sanitized / synthetic data only.

### P1 — No automated or semi-automated validation harness

`docs/local-validation.md` records prior validation, but there is no runnable validation script.

Needed:

- `scripts/validate_structure.py`: frontmatter, linked files, docs references, no local secrets
- `scripts/browser_smoke.py`: non-mutating Marketplace open/search/inbox probes
- `scripts/sanitize_check.py`: scan for local paths, listing IDs, phone numbers, secrets
- README command: `python3 scripts/validate_structure.py`

### P1 — Missing Marketplace-specific failure catalog

Reference skills are good because they document exact platform traps. Marketplace docs mention approval traps, but not enough UI traps.

Needed failure catalog:

- login wall / checkpoint / 2FA
- Marketplace unavailable / location prompt
- stale CDP websocket / daemon reconnect
- virtualized feed losing cards
- result cards with missing price/location
- item sold/unavailable after click
- composer opens with prefilled opener
- Send button disabled until real typing/input event
- form field appears filled but not committed
- category/condition combobox not selected
- publish button disabled
- inbox thread order changes after message
- duplicate tabs / stale item page

### P1 — Need mode-specific quickstarts

README currently explains the repo well, but a new user needs task-focused starts.

Add:

- “Scout listings without messaging anyone”
- “Assess one listing URL”
- “Draft a seller message but do not send”
- “Create a listing draft but do not publish”
- “Summarize active inbox threads without replying”

Each should include inputs, command/prompt, expected output, approval gates.

### P1 — Need explicit compliance / ToS posture

Because Facebook automation is sensitive, public sharing should include a short compliance posture.

Recommended framing:

- real logged-in user session
- human-in-the-loop
- draft-first / approval-gated by default
- no scraping at scale
- no spam messaging
- no payments/deposits
- no credential handling
- user responsible for platform policy compliance

### P2 — Skill topology is confusing after consolidation

The README lists many absorbed/narrow skills, but the current file tree has only some as top-level `SKILL.md` and several as local references. Coding-agent users may not know whether to load umbrella skills or subskills.

Needed:

- a clear “installed skills vs internal references” table
- remove or soften references to sibling skills that no longer exist as installed top-level skills
- add exact use guidance: load `facebook-marketplace-buyer` or `facebook-marketplace-seller` first

### P2 — No browser-use/browser-harness bridge note

Since the public repo reference is browser-harness but Hermes also has browser-use, add a compatibility note:

- browser-use CLI is good for interactive state/click/type workflows
- browser-harness domain skills use Python helper patterns
- this repo currently targets browser-harness; browser-use CLI adapters are future work unless added

## Highest leverage next changes

1. Add `docs/facebook-marketplace-ui-runbook.md` with field-tested URL patterns, selectors, snippets, failures, verification.
2. Add `examples/` with synthetic inputs/outputs and filled state files.
3. Add `scripts/validate_structure.py` and `scripts/sanitize_check.py`.
4. Update README setup with exact browser-harness/browser-use distinction and smoke tests.
5. Update local validation after running `browser-harness --setup` and a non-mutating live smoke test.

## Share-readiness verdict

Current state: good internal alpha / strong concept artifact.

Not yet share-ready as a high-quality browser-use/browser-harness domain skill library.

Reason: a new agent can understand the desired Marketplace operating model, but cannot reliably execute it without rediscovering the Facebook Marketplace UI.

Shareable after P0 fixes.

Publicly compelling after P1 examples and validation scripts.
