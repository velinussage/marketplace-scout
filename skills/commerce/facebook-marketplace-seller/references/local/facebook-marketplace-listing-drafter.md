---
name: facebook-marketplace-listing-drafter
description: USE WHEN you want Hermes to turn a seller brief into a strong Marketplace listing draft: pricing approach, title, description, photo checklist, and publish-ready field guidance. DON'T USE WHEN the item facts are still unclear or when the task is to autonomously publish or manage buyer replies without a draft review step.
version: 1.0.1
author: velinus
prerequisites:
  commands: [browser-harness, python3]
metadata:
  hermes:
    tags: [shopping, facebook, marketplace, seller, listing-draft, pricing, photos, copywriting]
    related_skills: [facebook-marketplace-seller, facebook-marketplace-listing-intake, facebook-marketplace-publish-manager, facebook-marketplace-buyer-inbox-triage, facebook-marketplace-inbox-heartbeat]
    requires_toolsets: [terminal]
---

# Facebook Marketplace Listing Drafter

Use this skill after intake when you want a listing that is honest, attractive, and operationally useful.

Its job is to produce:
- pricing strategy
- title
- description
- photo checklist
- category / condition guidance
- publish readiness notes

## When to Use

Use this skill when:
- the seller brief is mostly complete
- the user wants a better listing than a quick one-line post
- you want to prepare publish-ready copy and pricing guidance
- you want optional pricing or copy variants before publishing

## Don't Use When

Do not use this skill when:
- the item facts are still too incomplete to describe honestly
- the task is to send live buyer messages or manage active inbox threads
- the user expects direct publish without draft review or policy

## Procedure

### 1. Validate the intake brief

Before drafting, confirm:
- exact product identity
- condition truth
- included parts / accessories
- pickup or delivery constraints
- target ask and minimum acceptable price
- whether price is user-set or should be derived from Marketplace comps
- any claims that must not be overstated

### 2. Build the pricing plan

Return:
- suggested list price
- ideal settle zone
- minimum acceptable price
- whether early price-drop steps are pre-approved
- which facts justify the pricing

If the user gave an explicit ask, respect it unless it obviously conflicts with the floor or the user asks for a recommendation.

If the user did not give an explicit ask and the policy allows fallback pricing:
- search for similar Facebook Marketplace listings
- expand the radius when the local sample is too small or noisy
- summarize the comp set clearly
- apply the configured policy such as pricing at half of comparable asking price
- state exactly what evidence was used and where confidence is weak

If comps are weak, say so.
Do not fake certainty.

### 3. Draft the listing title

A good title should:
- name the item clearly
- include brand/model when valuable
- be as tight as possible for the exact item identity
- avoid spammy adjectives and unnecessary slash-separated variations
- stay human and Marketplace-native

If the item identity is already clear, prefer the simplest accurate title over cleverness.
For example, use `Precor Stretch Machine` instead of a looser or padded variant unless the model name is actually known.

### 4. Draft the description

A good description should:
- say what it is immediately
- state condition truthfully
- list included parts
- mention flaws clearly but calmly
- explain pickup / testing reality
- avoid robotic formatting

### 5. Build the photo checklist

Suggest a practical photo order:
- hero shot
- front / side / back
- brand / model tag
- working / powered-on proof if relevant
- accessories included
- flaws / wear close-ups

### 6. Publish-readiness notes

Call out what still blocks publication:
- missing dimensions
- unclear model number
- no proof of working condition
- poor photos
- policy not decided for auto-replies
- any required Marketplace field still invalid or unset
- title and description review still needed before publish

Also state the downstream handoff explicitly:
- if the draft is ready, hand off to `facebook-marketplace-publish-manager`
- once the listing is live and buyers are messaging, hand off to `facebook-marketplace-buyer-inbox-triage`
- if the listing is live and there are multiple active chats or an in-progress sale, hand off to `facebook-marketplace-inbox-heartbeat` and keep continuity in `docs/deal-state-template.md`

If the draft is good but some Marketplace field is still uncertain, recommend saving draft and asking the user to review rather than forcing a risky publish.

## Output format

Return:
1. suggested list price and reasoning
2. title draft
3. description draft
4. photo checklist
5. publish-readiness blockers
6. explicit note that the user should review the title and description before publish unless policy says otherwise
7. explicit note to save draft and ask for review if any Marketplace field is still uncertain or invalid
8. explicit operator-clarification note for any missing policy/state that would affect active chats or in-progress sales after publish
9. optional alternate version if the user wants faster or more premium positioning

## Pitfalls

- A pretty draft is bad if it hides flaws.
- Overpricing makes inbox triage noisy and low quality.
- Underpricing without a policy floor creates fast but bad outcomes.
- Photo strategy matters almost as much as copy.
- Comp-derived pricing must state the rule being used, not just the result.

## Verification

Before finishing, verify:
- the draft matches the seller brief
- flaws are disclosed clearly
- the price plan includes a floor
- the price source is explicit: user-set or comps-derived
- the publish blockers are explicit
