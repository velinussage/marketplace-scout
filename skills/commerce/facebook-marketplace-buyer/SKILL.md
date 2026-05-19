---
name: facebook-marketplace-buyer
description: "USE WHEN you want the agent to run a Facebook Marketplace buying workflow: ambient Browse-All feed-scroll discovery (history-biased, IMV/SCOPE-priced HTML report) or topic-driven scout, ranking, and negotiation drafts with per-message approval. DON'T USE WHEN you want unattended autopilot."
version: 1.1.0
author: velinussage
prerequisites:
  commands: [browser-harness]
metadata:
  hermes:
    tags: [shopping, facebook, marketplace, buyer, negotiation, pickup, browser-automation, chrome-history, alerts, pricing]
    related_skills: [facebook-marketplace-scout, facebook-marketplace-deal-assessor, facebook-marketplace-watch-notifier, facebook-marketplace-seller-communication, facebook-marketplace-negotiator, facebook-marketplace-pickup-manager, facebook-marketplace-history-seed, facebook-marketplace-buyer-inbox-watcher, facebook-marketplace-buyer-thread-timeout, facebook-marketplace-message-sender, facebook-marketplace-safety-guard, wishlist]
    requires_toolsets: [terminal]
---

# Facebook Marketplace Buyer

This is the top-level coordination skill for Marketplace buying workflows.

It does not replace the narrower skills. It routes the session through the right stage:

0. scroll the algorithmic Browse All feed for ambient discovery (no query)
1. scout listings from an explicit buying brief
2. notify / watch on worthwhile hits
3. assess how good the deal really is
4. draft or supervise negotiation (per-message approval)
5. plan pickup safely

## When to Use

Use this skill when:
- the user wants an end-to-end Marketplace buying helper
- the user wants one skill to coordinate shortlist, negotiation, and pickup stages
- the user wants recurring Marketplace help from a logged-in browser workflow

## Core Principle: Validate Current Intent First (Stage 1+ only)

Before any **topic-driven** scouting or live Marketplace action, always check recent browser history signals first. Summarize the strongest recent interests to the user and require explicit confirmation of the current target. Never silently reuse stale interests from months ago.

**Exception — Stage 0 (feed scroll):** Algorithmic feed discovery deliberately skips this gate. The whole point of Stage 0 is to delegate discovery to Facebook's own ranking. If the user explicitly asked for a Browse-All feed scroll, do not interrupt them with an interest-validation question.

## Don't Use When

Do not use this skill when:
- the user only needs one narrow stage and can use a stage-specific skill directly
- the user expects unsupervised messaging or autonomous payment
- browser-harness is not installed or not attached to the real browser

## Workflow routing

### Stage 0 — algorithmic feed scroll (passive discovery)

If the user wants ambient Marketplace discovery without supplying a search brief, use `facebook-marketplace-feed-scroll` behavior:
- open Marketplace at the default Browse All landing surface — no category filters, no query
- scroll the feed for N viewports (default 8, cap 20) and let Facebook's ranking surface the candidates
- capture each surfaced listing card as a structured record plus an element-scoped screenshot
- write the results to `reports/feed_<run_id>.json` and `reports/screenshots/feed_<run_id>_*.jpg`
- hand off to Stage 3 (deal assessment) for scoring, then to the report generator for the digest HTML
- this stage **skips** the interest-validation gate by design

### Stage 1 — scouting (topic-driven)

If the user *does* have a specific product brief, brand, or budget, use `facebook-marketplace-scout` behavior:
- ask for a real buying brief first when product, brand/model preference, budget, or clone tolerance is unclear
- optionally borrow Chrome-history / old Marketplace-search signal via `facebook-marketplace-history-seed` when the user wants prior browsing to inform search phrases
- define the buying brief explicitly before browsing
- search Marketplace with strict tab discipline
- capture listings
- benchmark shortlisted used listings against both local used comps and current new-price anchors
- rank shortlist
- propose which ones to message later

### Stage 2 — post-scout notify / watch

If the user wants asynchronous updates, use `facebook-marketplace-watch-notifier` behavior:
- notify only on worthwhile shortlist hits or strong deals
- prefer the harness's notification surface (e.g. Hermes gateway / background / cron, or whatever your coding-agent host exposes) back to the same chat or approved target
- keep the summary short and actionable
- never message sellers

### Stage 3 — deal assessment + reviewable report

If a listing looks promising and the user wants structured judgment plus a reviewable artifact, combine deal assessment with report generation:

- Use `facebook-marketplace-deal-assessor` for pricing logic and offer ladder
- Generate a bookmarkable HTML report that includes:
  - Real screenshots captured via browser-harness (focused on the listing)
  - Agent reasoning (deal label, confidence, price comparison, red flags)
  - Offer strategy
  - Clear recommendation
- The report serves as the primary output for human review instead of raw terminal text.

### Stage 4 — seller communication

If the user wants to actually pursue a listing, use `facebook-marketplace-seller-communication` behavior:
- accept a direct Marketplace item URL, bookmarked listing, or manually highlighted active listing as the stage entrypoint
- open the listing in the user's logged-in browser and verify the message surface is present before drafting anything
- close any temporary listing tab the agent opened for that check once the drafting/send step is complete
- ask for missing information in a natural seller-facing style
- negotiate inside approved price bounds
- validate the user's real availability before proposing meetup times
- trigger meetup coordination only after condition / price / timing are good enough
- keep all seller-facing messages inside explicit approved boundaries and post only as the user's own Facebook account after exact-text approval

### Stage 4b — inbox-watcher

Once one or more buyer messages have been sent, route to `facebook-marketplace-buyer-inbox-watcher` to poll outbound threads for seller replies and classify their intent. Surfaces a digest of new inbound activity with recommended next-action classes (counteroffer / answer / confirm meetup / walk away). Read-only; never sends a reply. Suspicious inbound messages (off-platform asks, scam tells) get tagged via `facebook-marketplace-safety-guard` and escalated to the user.

### Stage 4c — stalled-thread timeout

When `buyer-inbox-watcher` flags threads as stalled (no seller reply within the configured window — default 36 h), route to `facebook-marketplace-buyer-thread-timeout` to surface nudge / raise / abandon options. Each option is a drafted message gated by per-message approval and routed through `facebook-marketplace-message-sender` for the actual send.

### Stage 5 — negotiation (narrow / advanced)

If the user wants deeper price strategy or reply-by-reply interpretation, use `facebook-marketplace-negotiator` behavior:
- build the negotiation dossier
- suggest opener and offer ladder
- interpret seller posture
- require explicit approval before every seller-facing message

### Stage 6 — pickup planning

If a deal is forming, use `facebook-marketplace-pickup-manager` behavior:
- evaluate whether pickup is worth it
- draft timing options
- surface safety constraints
- require explicit approval before confirming any pickup details

## Library sharing / public positioning

When preparing a README, demo, X post, Sage library share, or launch note for this skill library, use the positioning reference at `./references/facebook-marketplace-skill-library-sharing.md`.

Core framing: this is not an unattended Marketplace bot. It is an approval-bounded Marketplace ops skill library that turns messy buyer-side judgment into reusable, inspectable workflow capability.

## Approval policy

The rule set is simple:

### Automatic reasoning allowed
- search and ranking
- pricing logic
- shortlist generation
- drafting messages
- planning routes and pickup windows
- updating deal-state summaries

### Explicit user approval required
- first seller message
- counteroffer message
- sharing phone number
- confirming a pickup time
- confirming a pickup location
- saying the user is definitely buying
- sending any Marketplace prefilled default opener unless the user explicitly approved that exact text

### Never allowed automatically
- deposits
- payments
- moving to off-platform payment rails
- disclosing sensitive identity details

## Quick Reference

```bash
browser-harness --doctor
browser-harness --setup
hermes chat -q "Use the facebook-marketplace-buyer skill and tell me which stage we are in." -s facebook-marketplace-buyer
```

## Pitfalls

- A fully automatic buyer agent is a bad default; approval-gated supervision is safer and more realistic.
- Marketplace quality is noisy; scouting quality matters more than message volume.
- Chrome-history signal can improve scouting, especially when old Marketplace searches reveal real product vocabulary, but it should inform the scout rather than silently dictate it.
- Post-scout notification should be low-noise and should prefer the harness's notification surface (e.g. Hermes gateway / background / cron, or whatever your coding-agent host exposes) when available.
- Deal assessment should compare against both new-price anchors and broader used-market distributions, not just nearby vibes.
- Pickup planning should not begin until price and item reality are sufficiently clear.
- If browser attachment fails, stop instead of pretending to browse.
- Opening the Marketplace message composer can expose Facebook's prefilled default opener; do not send it unless the user approved that exact text.

## Verification

Before finishing, verify:
- the correct stage was selected
- the browser path was healthy if browsing was required
- approval gates were preserved for all seller-facing actions
- no payment or deposit action was taken

## Absorbed Buyer Subskills

This umbrella is the main buyer-side discovery surface. Stage-specific playbooks should live here as labeled subsections or support files, not as sibling top-level skills.

### Stage references
- Shared browser UI runbook: `../../../docs/facebook-marketplace-ui-runbook.md` from the repo root, or `docs/facebook-marketplace-ui-runbook.md` when reading from the repo root
- State management and resume rules: `../../../docs/state-management.md` from the repo root, or `docs/state-management.md` when reading from the repo root
- Scouting and search-seeding details: `./references/local/facebook-marketplace-scout.md`
- Deal-comparison / comp-building details: `./references/local/facebook-marketplace-deal-assessor.md`
- Negotiation message and offer-ladder details: `./references/local/facebook-marketplace-negotiator.md`
- Pickup timing / safety / last-mile logistics details: `./references/local/facebook-marketplace-pickup-manager.md`
- Inbox polling / reply-intent classification (Stage 4b): `./references/local/facebook-marketplace-buyer-inbox-watcher.md`
- Stalled-thread nudge / raise / abandon flow (Stage 4c): `./references/local/facebook-marketplace-buyer-thread-timeout.md`
- Shared outbound send executor: `../../facebook-marketplace-message-sender/SKILL.md`
- Shared pre-send + inbound safety guard: `../../facebook-marketplace-safety-guard/SKILL.md`

## Consolidation Rule

If the maintainer would describe the task as “help me buy on Marketplace,” use this umbrella and route by stage. Do not force skill search to choose among multiple narrowly named buyer-side siblings first.

## New Support Files (2026-05-19)

- `references/local/facebook-marketplace-feed-scroll.md` — Stage 0 algorithmic-feed discovery (v0.7.0). Agent-led `browser-harness` scroll loop on Browse All, no query, no interest gate. Includes: 180-day Chrome-history bias with 21-day exponential decay across the `visits` table, `seen_listings` / `seen_searches` / `recurring_domains` / `title_vocab` build, block-list filter at `reports/.scout_block_list.txt`, quality filter (drops `No comps + Low confidence`, `$0`, empty titles), six-field IMV/SCOPE pricing stack (`comp_median_90d`, `imv_delta_pct`, `sell_through_rate`, `condition_multiplier` + `adjusted_floor`, `depreciation_anchor` + `dep_years`, `trust_signal_score`), and a 100-card capture re-ranked to top-50.
- `references/local/facebook-marketplace-report-generator.md` — Agent-authored single-file HTML report at `reports/current_scout_report.html`. Facebook visual language, top-50 compact cards with colored IMV verdict blocks, strikethrough MSRP + saving %, 3-cell offer ladder, button-style "Open on Marketplace" CTA, 140px thumbnails, and a "Previously viewed" tail showing all cataloged history listings. No Python templating; CSS custom properties only.
- `references/local/facebook-marketplace-ui.md` — Field-tested browser selectors, URL patterns, extraction logic, and failure modes for Facebook Marketplace automation.
- `references/local/current-interest-validation.md` — Mandatory validation pattern for **topic-driven** runs (Stage 1+). Stage 0 explicitly skips it.
- `references/local/real-marketplace-image-extraction.md` — Working selector pattern (`a[href*='/marketplace/item/'] img`) and flow for pulling real product images and direct listing URLs from Marketplace. FB CDN URLs (`scontent.fbcdn.net`) are downloaded with `curl` into `reports/images/feed_<run_id>/` so they never expire in the report.

## Architecture Decisions (2026-05-19)

- **Agent-led, end-to-end via `browser-harness` only.** All browser automation runs through `browser-harness <<'PY' ... PY` heredocs invoked from Bash, driven directly by the Claude agent. **Chrome-devtools MCP is explicitly NOT used** for the buyer Scout / feed-scroll path — it conflicts with the user's logged-in Chrome profile lock. There are no persisted Python generator scripts (`generate_*.py`, `run_*.py`); Python only runs inside ephemeral heredocs or one-off `sqlite3` / `curl` invocations. Existing files in `reports/` remain as historical reference but new work does not extend them.
- **Cadence and notification belong to the harness.** This skill library is invoked on-demand. Cron / scheduling / push delivery are not in scope here.
- **Negotiation gate = per-message.** Stage 4/5 drafts each outgoing seller message and requires user approval before it is sent. Not per-listing, not standing-approval. Tracked under memory `project-scout-vision`.
- **Image handling.** FB CDN URLs always downloaded to local relative paths under `reports/images/feed_<run_id>/`. Never embedded as remote URLs (they expire). Never use viewport screenshots as a substitute.
