---
name: facebook-marketplace-listing-intake
description: USE WHEN you want Hermes to capture a clean Marketplace selling brief before drafting or publishing: exact item identity, condition, flaws, included parts, price floor, scheduling constraints, and automation boundaries. DON'T USE WHEN the listing is already fully specified and you only need copywriting or inbox handling.
version: 1.0.1
author: velinus
prerequisites:
  commands: [python3]
metadata:
  hermes:
    tags: [shopping, facebook, marketplace, seller, listing-intake, pricing, scheduling]
    related_skills: [facebook-marketplace-seller, facebook-marketplace-listing-drafter, facebook-marketplace-publish-manager, facebook-marketplace-buyer-inbox-triage, facebook-marketplace-inbox-heartbeat]
    requires_toolsets: [terminal]
---

# Facebook Marketplace Listing Intake

Use this skill to build the seller-side operating brief before drafting or publishing a Marketplace listing.

Its job is to capture the truth about the item and the seller's constraints.

## When to Use

Use this skill when:
- the user has an item to sell and the details are still messy or incomplete
- you need a clean structured brief before drafting a listing
- you want to define price floor, meetup constraints, and auto-sell boundaries up front

## Don't Use When

Do not use this skill when:
- the item facts, pricing rules, and scheduling boundaries are already clear
- the task is only to rewrite copy or triage buyers for an existing listing

## Capture these fields

### Item identity
- product family
- brand
- exact model
- color / finish / size
- age or approximate age if known
- serial / model number if relevant

### Condition truth
- working / partially working / untested
- cosmetic wear
- defects or missing parts
- repairs or maintenance history
- accessories included
- whether the item can be demonstrated or tested

### Practical selling constraints
- pickup only vs delivery vs shipping
- item weight / size / helper needed
- preferred neighborhood / meetup type
- actual availability windows
- urgency to sell

### Pricing boundaries
- target ask if the user wants to set it directly
- minimum acceptable price / walk-away floor
- whether bundle offers are allowed
- whether holds are allowed
- whether price drops are pre-approved
- whether the agent should price from comps if no explicit ask is given
- if pricing from comps is allowed, whether the agent should search similar Facebook Marketplace listings, expand the radius when local comps are weak, and apply a rule such as listing at half of comparable asking price

### Automation boundaries
- draft-only vs approval-gated vs bounded auto-sell
- whether the agent may publish automatically
- whether the agent may respond automatically in inbox
- whether title and description must be reviewed before publish
- whether the listing should be first-come, first-real-pickup rather than hold-friendly
- what buyer questions force escalation
- what timing / meeting commitments are allowed automatically
- what open gateway / operator contact path should be used when clarification is needed

### Continuity bootstrap
Capture enough state to start or update a per-listing record in `docs/deal-state-template.md`:
- listing identifier or working title
- workflow mode: operator-first or bounded-autonomous
- blocked actions
- escalation triggers
- approved windows or explicit availability-check rule
- whether active chats and in-progress sales should always route back through the user when ambiguity appears

## Output format

Return:
1. a concise seller brief
2. missing facts that block good drafting or publishing
3. explicit pricing rules, including whether price is user-set or comps-derived
4. explicit automation mode and blocked actions
5. continuity bootstrap fields for `docs/deal-state-template.md`
6. the next recommended seller-side stage

## Pitfalls

- If the flaw list is weak, the listing draft will overpromise.
- If the price floor is unclear, inbox triage will drift.
- If availability is vague, the agent will propose bad meeting windows.
- If testing status is unknown, say that explicitly instead of bluffing.
- If comp-based pricing is allowed but the fallback rule is vague, the agent will price inconsistently.

## Verification

Before finishing, verify:
- brand/model identity is as specific as the user can provide
- flaws and missing parts are stated clearly
- the minimum acceptable price is explicit
- the price source is explicit: user-set or comps-derived
- the automation mode is explicit
- the next stage is clear
