# Facebook Marketplace Inbox Reply Policy

This policy is for seller-side Marketplace listings where the goal is to keep replies short, maintain ordering across multiple buyers, and prioritize the first buyer who can actually pick up.

## Core policy

- price is fixed unless the seller explicitly says otherwise
- do not negotiate if the listing is in fixed-price mode
- do not offer holds unless the seller explicitly allows holds
- first-come means **first real pickup**, not first message
- do not promise pickup times until the seller's actual availability is known or pre-approved windows already exist
- keep replies short, direct, and normal Marketplace tone
- escalate suspicious, ambiguous, or off-policy threads

## Default reply rules

### Still available
Reply briefly:
- "Yes, it's still available."

### Fixed price
If asked for a discount in fixed-price mode:
- "Price is firm at $200."
- optional softer variant: "I'm keeping it at $200 for now."

### Serious pickup intent
If a buyer sounds ready to pick up:
- confirm they are serious
- check seller availability if no approved windows exist
- only then propose actual pickup windows

### Holds
If holds are not allowed:
- "I'm not doing holds, but if you can pick up first once I confirm availability, it's yours."

### Backup buyer
If someone else is ahead in the queue:
- "I have someone ahead for the earliest pickup slot. If that falls through, I'll message you next."

### After one pickup is scheduled
Once one buyer is `scheduled-primary`:
- stop offering pickup windows to additional buyers
- do not imply that multiple buyers can all come meet
- move later serious buyers into `backup-1`, `backup-2`, or `candidate` depending on readiness
- tell backup buyers clearly that one buyer is ahead and they are next only if that falls through
- only re-open scheduling with backups if the primary buyer stalls, cancels, misses the confirmation window, or the seller explicitly changes the queue decision

## Queue policy

Maintain an explicit ordered queue per listing.
Use `docs/deal-state-template.md` to preserve this queue and the active-chat / in-progress-sale state across sessions.

Suggested fields:
- buyer name / thread identifier
- thread link if available
- thread status
- offered price
- earliest pickup time they can do
- whether their timing matches seller availability
- last outbound message
- last inbound message time
- queue rank

## Queue states

- `new` — first message received, not yet classified
- `info` — asking normal questions, not yet pickup-ready
- `ready-awaiting-seller` — buyer can pick up but seller availability not yet checked
- `candidate` — buyer is a real pickup candidate once seller windows are known
- `scheduled-primary` — confirmed for the earliest seller-compatible pickup slot
- `backup-1`, `backup-2` — next buyers in line if primary fails
- `stalled` — buyer stopped responding or cannot confirm timing
- `closed` — sold elsewhere, declined, or no longer relevant
- `suspicious` — do not advance without human review

## Ordering rule

Sort buyers by:
1. seriousness / real readiness
2. ability to match the earliest seller-compatible pickup window
3. policy compliance (no weird payment / hold / off-platform behavior)
4. message freshness only as a tie-breaker

This means:
- a vague early message does not outrank a later buyer who can actually pick up first
- a buyer asking only "still available?" is not automatically first in line
- a buyer who can meet a real approved pickup window becomes the primary candidate

## Heartbeat cadence

Use a repeating inbox check cadence.

Recommended defaults:
- active selling hours: every 30 to 60 minutes
- quiet hours / overnight: every 2 to 4 hours or next morning
- immediately after a new serious buyer message: run a focused heartbeat

## Heartbeat checklist

Each heartbeat should:
1. scan active chats, new threads, and updated buyer threads
2. classify each thread
3. update the ordered pickup queue
4. identify the top real pickup candidate
5. check whether seller availability is needed
6. draft or send the next approved reply
7. move stale or non-serious threads down the queue
8. surface any escalation items to the seller through the open gateway / operator contact path
9. update the per-listing sale state so in-progress sales remain legible

## Escalation triggers

Always escalate if:
- buyer wants payment off-platform
- buyer asks for a hold outside policy
- buyer is pressuring for unusual urgency
- pickup safety is unclear
- multiple serious buyers want the same slot and policy does not resolve it cleanly
- the agent cannot tell who should be first in line with confidence

## Good reply examples

### Fixed-price response
- "Yes, it's available. Price is firm at $200."

### Pickup-ready but seller windows unknown
- "Yes, it's available. If you're ready to pick up, I can check my availability and get back to you with windows."

### Primary candidate scheduling
- "I can do today between 5:30-7 or tomorrow 10-12. Which works for you?"

### Backup candidate
- "I have someone ahead for the first pickup slot. If that falls through, I'll message you next."

## Bad reply patterns

- long explanations
- apologetic negotiation essays
- promising holds automatically
- offering pickup windows before checking seller availability
- letting multiple buyers think they each have first claim to the same slot
