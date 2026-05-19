---
name: facebook-marketplace-inbox-heartbeat
description: USE WHEN you want Hermes to run recurring seller-side Facebook Marketplace inbox checks, keep an ordered buyer queue, enforce fixed-price or approved pricing policy, and coordinate first-real-pickup scheduling. DON'T USE WHEN the listing is not live, the seller policy is undefined, or you want unlimited autonomous deal-making.
version: 1.0.0
author: velinus
prerequisites:
  commands: [browser-harness, python3]
metadata:
  hermes:
    tags: [shopping, facebook, marketplace, inbox, heartbeat, seller, scheduling, queue-management, automation-policy]
    related_skills: [facebook-marketplace-buyer-inbox-triage, facebook-marketplace-seller, facebook-marketplace-publish-manager, facebook-marketplace-listing-intake, facebook-marketplace-listing-drafter]
    requires_toolsets: [terminal]
---

# Facebook Marketplace Inbox Heartbeat

Use this skill for repeated seller-side inbox checks after a listing is live.

Its job is to:
- check active chats and new or updated buyer threads
- keep an ordered buyer queue
- enforce fixed-price or approved pricing rules
- identify the first real pickup candidate
- coordinate scheduling only after seller availability is known
- maintain clear state for in-progress sales across multiple simultaneous interactions
- surface what is waiting on the user vs what is waiting on the counterparty

## When to Use

Use this skill when:
- a Marketplace listing is live
- the seller wants repeated inbox monitoring
- there may be multiple active buyer threads at once
- the operating rule is first real pickup, not first vague message
- the seller wants Hermes to keep order without losing context

## Don't Use When

Do not use this skill when:
- the listing is not yet live
- the seller policy is unclear
- the price mode (fixed vs negotiable) is not defined
- the seller wants unbounded autonomous negotiation or risky commitments

## Required policy before use

Before heartbeat mode starts, Hermes should know:
- listing title or identifier
- current listed price
- whether price is fixed or negotiable
- minimum acceptable price if negotiation is allowed
- whether holds are allowed
- whether the rule is first-come, first-real-pickup
- whether same-day pickup is allowed
- approved pickup windows, or the fact that seller availability must be checked each time
- what open gateway / operator contact path should be used when policy or state is incomplete
- where the per-listing state record lives in `docs/deal-state-template.md`

## Heartbeat loop

Each heartbeat should do this in order:

### 1. Read the live inbox state
- identify active chats
- identify new threads
- identify updated threads
- identify unanswered threads
- identify stalled threads
- identify which in-progress sales are waiting on the user vs the counterparty

### 2. Classify each thread
Use one of:
- new
- info
- ready-awaiting-seller
- candidate
- scheduled-primary
- backup-1
- backup-2
- stalled
- closed
- suspicious

### 3. Update the buyer queue
Maintain an explicit ordered queue.

Sort by:
1. real seriousness
2. ability to meet the earliest seller-compatible pickup window
3. policy compliance
4. time freshness only as a tie-breaker

### 4. Enforce price mode
If price is fixed:
- do not negotiate
- restate price briefly and move the buyer toward pickup readiness or out of the queue

If negotiation is allowed:
- stay inside the approved price bounds
- do not let lowball threads outrank ready full-price pickup candidates

### 5. Decide whether seller availability is needed
If a buyer is serious and ready to pick up, but there are no approved windows:
- ask the seller for availability before proposing times
- do not invent or imply windows

### 6. Draft or send the next reply
Keep replies:
- short
- direct
- Marketplace-native
- consistent with queue order and policy
- consistent with the single active pickup slot once a `scheduled-primary` buyer exists

Default operator-first rule:
- first outbound buyer reply
- any counteroffer
- any hold promise
- any pickup confirmation
- any material term change
- any ambiguous queue-resolution decision

all require explicit approval unless bounded autonomy policy clearly authorizes them.

### 7. Maintain the sale-state summary
After each heartbeat, update:
- current queue order
- primary candidate
- backups
- next seller action needed
- whether the listing should stay active, move to pending, or escalate
- active chats for this listing
- in-progress sale state
- what is waiting on the user vs the counterparty
- what clarification should be sent back through the open gateway / operator contact path

Use `docs/facebook-marketplace-inbox-policy.md` as the inbox decision policy and `docs/deal-state-template.md` as the per-listing continuity surface.
If required policy fields are missing, stop and ask the user for clarification instead of improvising.

## Reply rules

### Fixed-price mode
Default style:
- "Yes, it's available. Price is firm at $200."

### Pickup-ready buyer
If no seller windows yet:
- "Yes, it's available. If you're ready to pick up, I can check my availability and get back to you with times."

If approved windows exist:
- offer only the real approved windows

### Backup buyer
- "I have someone ahead for the earliest pickup slot. If that falls through, I'll message you next."

## Multiple-buyer handling

Never let two buyers both think they have the same primary slot.

When multiple serious buyers exist:
- keep one clear primary candidate
- keep one or two backups
- demote vague or slow buyers
- if the primary stalls or misses the response window, advance the next buyer
- once a buyer is `scheduled-primary`, freeze scheduling language for everyone else until that slot is clearly released
- backup buyers should get queue-aware replies, not parallel meetup offers

## Suggested cadence

- every 30 to 60 minutes during active selling hours
- every 2 to 4 hours during quiet periods
- immediate rerun after any serious new buyer message

## Pitfalls

- first message is not the same as first real pickup candidate
- fixed-price mode should not drift into casual negotiation
- scheduling before checking seller availability creates chaos
- long replies slow everything down and confuse queue order
- without an explicit queue, the agent will lose ordering across multiple threads
- without a per-listing state record, active chats and in-progress sales will drift between sessions
- if operator contact path or clarification rules are missing, do not continue in autonomous mode

## Verification

Before finishing a heartbeat, verify:
- fixed-price vs negotiable mode was respected
- the buyer queue order is explicit
- the primary pickup candidate is clear
- seller availability was checked before scheduling unless approved windows existed
- no off-policy hold, payment, or risky commitment was made
