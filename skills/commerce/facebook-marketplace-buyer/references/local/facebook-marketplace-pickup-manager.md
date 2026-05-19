---
name: facebook-marketplace-pickup-manager
description: USE WHEN you want the agent to reason about Facebook Marketplace pickup timing, meeting safety, routing, and confirmation messaging with explicit approval before any seller-facing commitment. DON'T USE WHEN you want the agent to autonomously confirm a meeting, share sensitive details, or handle payment.
version: 1.0.0
author: velinussage
prerequisites:
  commands: [browser-harness, python3]
metadata:
  hermes:
    tags: [shopping, facebook, marketplace, pickup, scheduling, safety, logistics]
    related_skills: [facebook-marketplace-buyer, facebook-marketplace-scout, facebook-marketplace-negotiator]
    requires_toolsets: [terminal]
---

# Facebook Marketplace Pickup Manager

This skill handles the last-mile logistics of a promising Marketplace deal.

It helps the agent:
- choose reasonable pickup windows
- balance urgency vs convenience
- draft safe meeting language
- reason about route, timing, and batching
- keep commitments explicit and reversible

## When to Use

Use this skill when:
- the seller is responsive and a deal looks realistic
- the user wants help planning the pickup window
- the user wants the agent to draft confirmation messages
- the user wants help deciding whether a pickup is worth the time

## Don't Use When

Do not use this skill when:
- the seller has not responded yet
- negotiation is still unresolved
- the user has not approved a pickup plan
- the transaction requires deposit or risky off-platform steps

## Core safety rule

**Pickup planning may be reasoned about automatically, but pickup confirmation still requires explicit approval.**

## Procedure

### 1. Build the pickup brief

Gather:
- agreed or near-agreed price
- candidate time windows
- pickup area
- user travel radius
- item size / vehicle implications
- urgency level
- whether a public meeting place is possible

### 2. Evaluate whether the pickup is worth doing

Reason about:
- price advantage vs travel/time cost
- same-day convenience vs rushing into a sketchy deal
- whether the item condition justifies the trip
- whether multiple errands or pickups can be batched

If the trip is not worth it, say so plainly.

### 3. Draft confirmation options

Prepare concise seller-facing options such as:
- same-day pickup window
- next-day pickup window
- public-place meeting suggestion if appropriate
- “please confirm the item is still available and condition is unchanged” message

Keep language short and practical.

### 4. Approval-gated send/confirm mode

Before any seller-facing confirmation:
1. show the exact message
2. wait for explicit user approval
3. send only the approved message if the user says yes
4. confirm back what was sent

Do not silently change pickup times or places.

### 5. Keep a deal-state summary

Track:
- listing URL
- current seller status
- latest agreed price band
- next proposed pickup slot
- blockers or uncertainty
- whether the deal is still worth pursuing

## Pitfalls

- Never confirm a pickup if the price is still ambiguous.
- Avoid private residential details unless the user explicitly accepts that tradeoff.
- Do not let the agent create urgency that the user did not ask for.
- Large items can add vehicle, weather, and helper constraints; call them out explicitly.
- If the seller becomes inconsistent on time or item condition, downgrade the deal.

## Verification

Before finishing, verify:
- the deal had progressed past initial scouting
- the pickup window options were explicit
- safety considerations were surfaced
- any seller-facing message was shown before sending
- no final meeting was confirmed without approval
