---
name: facebook-marketplace-deal-assessor
description: USE WHEN you want the agent to judge how good a Facebook Marketplace deal really is by comparing the listing against local used comps, wider-radius comps, and current new-price anchors, then build a normal price distribution and recommend whether to pursue, negotiate, or skip. DON'T USE WHEN you only need a raw shortlist, or when you want the agent to message sellers or commit to buy without review.
version: 1.0.0
author: velinussage
prerequisites:
  commands: [browser-harness, python3]
metadata:
  hermes:
    tags: [shopping, facebook, marketplace, pricing, deal-analysis, comps, negotiation]
    related_skills: [facebook-marketplace-buyer, facebook-marketplace-scout, facebook-marketplace-negotiator, facebook-marketplace-history-seed]
    requires_toolsets: [terminal]
---

# Facebook Marketplace Deal Assessor

Use this skill after scouting when you want a more serious pricing judgment than a simple shortlist rank.

Its job is to answer:
- how good is this deal really?
- what does the broader market look like?
- is the ask below, near, or above a believable market distribution?
- is the item worth negotiating for, or should the user skip it?

This skill does **not** contact sellers. It produces pricing judgment, deal quality, and next-step recommendations.

## When to Use

Use this skill when:
- the user wants to know whether a listing is actually a strong deal
- the scout found promising candidates and you want better comp work
- local Marketplace results are sparse and you want to expand the search radius
- you want a more disciplined offer band before negotiation starts
- you want a broader view than one search page of nearby listings

## Don't Use When

Do not use this skill when:
- the user only wants a first-pass shortlist
- the product family is still unclear
- the current brief is missing essential budget / brand / condition constraints
- the task is to send seller messages or commit to buy

## Core idea

This skill should build a **distribution**, not just a vibe.

For each serious candidate, reason from:
1. nearby used comps
2. expanded-radius used comps
3. current public new-price anchors
4. brand/model quality
5. condition and convenience adjustments

Then decide whether the listing is:
- exceptional deal
- strong deal
- fair
- weak
- overpriced
- suspicious

## Procedure

### 1. Lock the comparison brief

Before assessing, confirm:
- product family
- target listing URL
- asking price
- brand/model preference
- max budget
- target price
- acceptable condition
- pickup radius
- clone tolerance

If these are missing, ask first.

### 2. Collect local used comps

Start with the strongest nearby comps from the scout session.

Capture for each comp:
- price
- title
- location
- condition signal
- brand/model clue
- listing age if visible
- URL

Prefer same-model or same-brand comps over generic category matches.

### 3. Expand the radius when needed

If the local sample is too small or too noisy, expand the search radius deliberately.

Expansion order:
- same city / immediate metro
- nearby metro cluster
- wider regional radius

Do not expand forever. The goal is to build a believable comparison set, not scrape the entire state.

When expanding, note which comps are:
- local-core
- near-regional
- wide-regional

Distance matters. Wider comps should influence the distribution less when pickup friction is high.

### 4. Capture new-price anchors

For the same product family or model, capture 1 to 5 public new-price anchors from places like:
- manufacturer site
- Amazon
- Walmart
- Target
- Office Depot
- specialty retailers

Prefer exact-model matches.
If exact-model matches are unavailable, use close family matches and label them as approximate.

### 5. Build a usable price distribution

Do not pretend to have a statistically perfect market if the sample is small.

Use a practical distribution summary such as:
- sample size
- low end
- median / typical zone
- upper end
- count of close brand/model matches
- count of generic matches

If the sample is large enough, you may describe rough quartiles.
If the sample is small, say "small sample" clearly.

The purpose is to answer:
- where does the target listing sit relative to the distribution?
- how much of the apparent value is coming from brand, condition, or convenience?

### 6. Adjust for quality and friction

Apply explicit adjustments for:
- brand reputation / premium model value
- exact model match vs generic lookalike
- condition quality
- accessories / extras
- listing freshness or staleness
- travel inconvenience / pickup burden
- seller quality clues

Do not treat a far-away comp as equal to a nearby comp if pickup friction is materially worse.

### 7. Score the deal

Return a structured judgment such as:
- deal label
- confidence
- why it earned that label
- reasonable offer ladder
- walk-away price
- whether it is worth messaging now, watching, or ignoring

Suggested labels:
- exceptional deal
- strong deal
- fair
- weak
- overpriced
- suspicious

Suggested confidence bands:
- high
- medium
- low

### 8. Hand off to negotiation only if justified

If the deal is weak or overpriced, say so plainly.
If the deal is strong enough, provide a negotiation handoff:
- ideal opener band
- likely settle band
- hard stop
- key fact to verify before messaging

## Example output

```md
Deal assessment: strong deal
Confidence: medium

Target
- $140
- Brand: Varier Balans
- Location: Durham

Used comp distribution
- 8 comps total
- local-core: 4
- near-regional: 3
- wide-regional: 1
- typical local zone: $160-$240
- best generic clone zone: $40-$90

New price anchors
- Manufacturer / premium retailer: ~$399-$499
- Secondary retailer: ~$379

Assessment
- The listing sits below the local branded used zone
- It is far above clone pricing, which is expected for this brand
- Distance friction is acceptable
- Condition appears consistent with the ask

Offer guidance
- opening: $120-$130
- likely settle: $130-$145
- hard stop: $160

Next step
- worth messaging
```

## Pitfalls

- Generic clones will contaminate the distribution if you mix them with branded premium models.
- A bigger radius is useful, but too much distance makes the comps less relevant.
- Small samples should reduce confidence, not trigger fake precision.
- New-price anchors help, but new retail is not the same as used resale value.
- A low ask can still be suspicious if the listing quality is poor or the seller signals are bad.

## Verification

Before finishing, verify:
- the target listing and current brief were clear
- both local and, when needed, expanded-radius comps were considered
- at least one new-price anchor was captured or the absence was stated clearly
- the result includes a usable price distribution summary
- the deal label and confidence are explicit
- a walk-away price or hard stop is stated
- no seller-facing action was taken
