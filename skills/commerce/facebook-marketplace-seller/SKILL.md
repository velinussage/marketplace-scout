---
name: facebook-marketplace-seller
description: "USE WHEN you want the agent to run an end-to-end Facebook Marketplace selling workflow: capture item facts, price the listing, draft and review the post, prepare or publish it, triage buyer messages, and coordinate pickup under explicit automation boundaries. DON'T USE WHEN you want unbounded autopilot that can take deposits, improvise pricing outside policy, or commit you to a sale without approved rules."
version: 1.0.1
author: velinus
prerequisites:
  commands: [browser-harness, python3]
metadata:
  hermes:
    tags: [shopping, facebook, marketplace, seller, listing, publishing, inbox-triage, scheduling, automation-policy]
    related_skills: [facebook-marketplace-listing-intake, facebook-marketplace-listing-drafter, facebook-marketplace-publish-manager, facebook-marketplace-buyer-inbox-triage, facebook-marketplace-inbox-heartbeat, facebook-marketplace-seller-reply-composer, facebook-marketplace-message-sender, facebook-marketplace-safety-guard]
    requires_toolsets: [terminal]
---

# Facebook Marketplace Seller

This is the top-level coordination skill for Marketplace selling workflows.

It routes the session through the right stage:
1. listing intake
2. pricing and listing draft
3. title / description review
4. publish preparation or publish execution
5. buyer inbox triage
6. scheduling and sale-state coordination

## When to Use

Use this skill when:
- the user wants one seller-side skill to manage the overall Marketplace selling workflow
- the user wants the agent to help go from item facts to a live listing
- the user wants repeated inbox handling with explicit boundaries
- the user wants to experiment with bounded auto-sell operations instead of one-off drafting only

## Don't Use When

Do not use this skill when:
- the task is purely buy-side scouting or negotiation
- the user expects unbounded autonomous selling without clear pricing, timing, and escalation policy
- browser-harness is not attached to the real logged-in browser for publish or inbox actions

## Workflow routing

### Stage 1 — listing intake

If the listing is not yet well specified, use `facebook-marketplace-listing-intake`:
- capture exact item facts
- capture condition, flaws, dimensions, included parts, and testing status
- capture either an explicit seller-chosen price or a fallback pricing policy
- capture meetup / pickup constraints
- capture automation boundaries before any publish or inbox work

### Stage 2 — listing draft

If the item facts are known but the listing is not ready, use `facebook-marketplace-listing-drafter`:
- produce a pricing strategy
- if no explicit ask is given, research similar Marketplace comps, expand the radius, and apply the configured pricing policy
- draft title, description, and photo checklist
- identify what must be verified before publishing

### Stage 3 — review before publish

Default rule:
- the user reviews the title and description before publishing
- the user may override this only with a bounded auto-publish policy

### Stage 4 — publish workflow

If the draft is ready and the user wants form-fill or publish help, use `facebook-marketplace-publish-manager`:
- prepare the listing form
- make sure all required Marketplace details are actually set and valid before treating the listing as ready
- keep category, condition, price, title, description, photos, and pickup details consistent
- if any required detail is still uncertain or invalid, save draft and ask the user to review before continuing
- require approval before final publish unless a bounded publish policy exists
- manage relist / renew / price-drop moves under policy

### Stage 5 — buyer inbox triage

If buyers are already messaging, use `facebook-marketplace-buyer-inbox-triage`:
- classify serious vs flaky vs suspicious buyers
- draft concise replies
- stay inside pricing and scheduling rules
- when a buyer is ready to pick up, check the seller's real availability first
- prioritize first real pickup over vague interest when the policy is first-come, first-pickup

### Stage 5b — reply composer (per inbound buyer message)

If a specific buyer message needs a tailored reply that's grounded in the listing facts and the seller's policy, use `facebook-marketplace-seller-reply-composer`. It resolves the inbound to its listing context (cached at `reports/listings/<listing_id>.json`), classifies the buyer's ask against the pattern catalog (still-available / counteroffer / shipping / hold / meetup / etc.), computes counter math against the seller's `floor`, and drafts 2–3 short variants that match real Marketplace-seller voice. All sends route through `facebook-marketplace-message-sender` with per-message approval; suspicious inbound messages are escalated via `facebook-marketplace-safety-guard` instead of replied to.

### Stage 6 — recurring heartbeat / sale-state continuity

If the listing is live and there are active chats or an in-progress sale, use `facebook-marketplace-inbox-heartbeat` to:
- check active chats repeatedly
- keep the per-listing buyer queue explicit
- track primary vs backup buyer order
- summarize what is waiting on the user vs the counterparty
- keep the in-progress sale legible across repeated sessions

Use `docs/deal-state-template.md` as the continuity surface for this stage.
If policy or state is incomplete, default to asking the user through the configured open gateway / operator contact path instead of improvising.

## Library sharing / public positioning

When preparing a README, demo, X post, Sage library share, or launch note for this skill library, use the positioning reference at `./references/facebook-marketplace-skill-library-sharing.md`.

Core framing: this is not an auto-lister or unattended selling bot. It is an approval-bounded Marketplace ops skill library that turns listing, pricing, inbox, and pickup judgment into reusable, inspectable workflow capability.

## Automation modes

Use one of these modes explicitly:

### Draft-only
- The agent can gather facts, produce drafts, summarize inbox state, and suggest the next action.
- The agent does not publish or send messages.

### Approval-gated
- The agent can prepare the exact listing text, form-fill plan, or reply text.
- The user approves before publish, send, hold, meetup confirmation, or any material change in terms.
- When policy or state is incomplete, the agent should ask the user for clarification through the open gateway / operator contact path instead of guessing.

### Bounded auto-sell
- The agent may publish or reply automatically only inside explicit rules.
- Rules must define:
  - whether the seller can choose the price directly
  - what happens if no explicit price is given
  - minimum acceptable price
  - whether holds are allowed
  - approved pickup windows
  - whether first confirmed pickup wins
  - what buyer behaviors force escalation
  - what actions remain blocked

## Never allowed automatically
- accepting deposits
- off-platform payment instructions
- shipping commitments outside policy
- sharing sensitive identity details
- promising a sale after policy is exceeded or facts are ambiguous

## Runtime Setup

If `browser-harness` is not installed, not attached to the user's Chrome, or the Facebook session is dead, route to **`facebook-marketplace-runtime-setup`** first. That skill covers the one-time `uv tool install -e .`, the Chrome remote-debugging attach, and the Facebook session verification. Every seller stage below assumes the runtime is healthy.

## Quick Reference

```bash
browser-harness --doctor
browser-harness --setup
hermes chat -q "Use the facebook-marketplace-seller skill and tell me which seller stage we are in." -s facebook-marketplace-seller
```

## Pitfalls

- Seller automation fails when intake is weak; missing flaws or dimensions create downstream problems.
- A publish workflow should not outrun photo quality or condition truthfulness.
- Fast inbox response is useful, but unbounded replies create bad commitments quickly.
- Bounded auto-sell must be policy-first; otherwise it becomes risky improvisation.
- Active chats and in-progress sales need a durable per-listing state, not just ad hoc memory.
- If operator contact path or clarification rules are missing, default back to asking the user before responding.
- If browser attachment fails, stop instead of pretending to publish or triage.

## Verification

Before finishing, verify:
- the correct seller stage was selected
- the automation mode was explicit
- the price source was explicit: user-set or comps-derived
- all required Marketplace details were actually set and valid before publish
- title and description were reviewed before publish unless policy says otherwise
- if there was uncertainty, the listing was saved as a draft and surfaced for user review
- publish and inbox actions stayed inside policy
- no deposit, payment, or identity-risk action was taken

## Absorbed Seller Subskills

This umbrella is the main seller-side discovery surface. Stage playbooks and recurring inbox-state recipes should live here as stage references, not as separate top-level skills.

### Stage references
- Shared browser UI runbook: `../../../docs/facebook-marketplace-ui-runbook.md` from the repo root, or `docs/facebook-marketplace-ui-runbook.md` when reading from the repo root
- State management and resume rules: `../../../docs/state-management.md` from the repo root, or `docs/state-management.md` when reading from the repo root
- Intake / policy capture: `./references/local/facebook-marketplace-listing-intake.md`
- Drafting / pricing / photo plan: `./references/local/facebook-marketplace-listing-drafter.md`
- Publish / relist / price-drop execution: `./references/local/facebook-marketplace-publish-manager.md`
- Single-pass buyer-thread triage: `./references/local/facebook-marketplace-buyer-inbox-triage.md`
- Repeated inbox monitoring / queue management: `./references/local/facebook-marketplace-inbox-heartbeat.md`
- Per-inbound reply composer with listing-context loader (Stage 5b): `./references/local/facebook-marketplace-seller-reply-composer.md`
- Shared outbound send executor: `../../facebook-marketplace-message-sender/SKILL.md`
- Shared pre-send + inbound safety guard: `../../facebook-marketplace-safety-guard/SKILL.md`

## Consolidation Rule

If the maintainer would describe the task as “help me sell on Marketplace,” use this umbrella and route by stage. Avoid making skill search choose among multiple narrow seller-side session artifacts first.
