---
name: facebook-marketplace-buyer-inbox-triage
description: USE WHEN you want the agent to manage the seller-side Marketplace inbox: classify incoming buyers, draft or send bounded replies, hold pricing and scheduling boundaries, and escalate suspicious or ambiguous threads. DON'T USE WHEN you want unlimited auto-replies, off-platform payment handling, or meeting commitments outside explicit rules.
version: 1.0.1
author: velinus
prerequisites:
  commands: [browser-harness, python3]
metadata:
  hermes:
    tags: [shopping, facebook, marketplace, seller, inbox-triage, buyer-messages, scheduling, automation-policy]
    related_skills: [facebook-marketplace-seller, facebook-marketplace-publish-manager, facebook-marketplace-listing-intake, facebook-marketplace-inbox-heartbeat]
    requires_toolsets: [terminal]
---

# Facebook Marketplace Buyer Inbox Triage

This is the seller-side inbox skill.

The "buyer" here means the people contacting your listing.

Use this skill to:
- sort serious buyers from flaky or suspicious ones
- draft concise replies
- enforce price floor and scheduling policy
- decide when a thread should escalate to a human decision
- prioritize the first real pickup opportunity when that is the configured selling policy

## When to Use

Use this skill when:
- a listing is live and buyers are messaging
- the user wants the agent to handle or pre-handle the inbox
- the user wants bounded auto-sell behavior for repetitive questions and narrow negotiation bands

## Don't Use When

Do not use this skill when:
- the listing is not yet live
- the price floor or scheduling policy is unclear
- the user expects unbounded autonomous deal-making
- the thread involves deposits, shipping complexity, or unusual trust risk

## Triage classes

Classify each incoming buyer as one of:
- serious and ready
- normal but early-stage
- lowball but still possible
- flaky / low-signal
- suspicious / avoid
- needs human judgment

## Procedure

### 1. Load seller policy

Before replying, know:
- current list price
- whether the price is fixed or negotiable
- minimum acceptable price if negotiation is allowed
- whether holds are allowed
- whether the listing is first-come, first-real-pickup
- approved pickup windows
- whether same-day meetup is allowed
- whether the agent may auto-reply or only draft
- what open gateway / operator contact path should be used if policy or state is incomplete
- whether a per-listing record already exists in `docs/deal-state-template.md`

### 2. Read the thread state

Summarize:
- what the buyer asked
- what has already been answered
- whether the buyer acknowledged location, condition, or price
- whether the next step is info, negotiation, or scheduling
- whether the buyer appears realistically able to pick up soon

### 3. Draft or send bounded replies

This skill should follow `docs/facebook-marketplace-inbox-policy.md` and keep per-listing continuity in `docs/deal-state-template.md`.

Good replies should be:
- short
- normal
- specific
- inside policy

Default operator-first rule:
- first outbound buyer reply
- any counteroffer
- any hold promise
- any pickup confirmation
- any material term change
- any ambiguous queue-resolution decision

all require explicit approval unless bounded autonomy policy clearly authorizes them.

Allowed automatic actions in bounded mode may include:
- answering still-available questions
- repeating clear pickup area / window info
- restating condition truth
- in fixed-price mode, politely restating that the price is firm
- if negotiation is allowed, declining offers below floor
- drafting the next reply for a serious buyer

Scheduling rule:
- do not promise pickup windows until the user's real availability has been checked
- when a buyer shows serious interest in picking up, trigger availability check with the user first unless pre-approved windows already exist
- if the policy is first-come, first-real-pickup, prioritize the buyer who can actually pick up first rather than the buyer who only shows vague interest
- maintain an explicit queue ordered by real readiness, seller-window match, and latest confirmation state, not by message count alone
- once one buyer is `scheduled-primary`, stop offering pickup windows or meet-up language to other buyers; move them into backup states and tell them someone is ahead

Actions that should escalate by default:
- requests for holds outside policy
- bundle requests that change price materially
- unusual shipping asks
- pressure to move off-platform quickly
- ambiguous safety situations
- multiple serious buyers colliding on the same pickup window without a clear policy answer

### 4. Maintain sale-state summary

Track:
- hottest thread
- fixed-price or negotiation mode
- best offer so far if negotiation is allowed
- next approved meetup window
- who is pending, declined, blocked, or most likely to pick up first
- the ordered pickup queue
- whether the listing should stay active or move toward pending
- what is waiting on the user vs what is waiting on the buyer
- what clarification should be sent back through the open gateway if policy/state is incomplete

If the listing has multiple active chats or an in-progress sale that will need repeated checks, hand off to `facebook-marketplace-inbox-heartbeat` after the current pass.

## Pitfalls

- Fast replies are good, but fast bad commitments are not.
- A serious buyer can still become suspicious later; re-evaluate each thread.
- Repeating the same long explanation to every buyer is bad inbox style.
- Never auto-accept a price below the floor or invent exceptions.
- Do not confuse first message with first real pickup candidate.

## Verification

Before finishing, verify:
- the reply mode matched the policy
- the thread classification was explicit
- fixed-price vs negotiable mode was handled correctly
- price and scheduling stayed inside rules
- user availability was checked before pickup scheduling unless pre-approved windows existed
- the pickup queue order is explicit and current
- suspicious or ambiguous threads were escalated
