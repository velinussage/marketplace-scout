---
name: facebook-marketplace-negotiator
description: USE WHEN you want Hermes to draft or supervise Facebook Marketplace seller outreach, reason about offer ranges, and manage negotiation with explicit approval gates before every seller-facing action. DON'T USE WHEN you want unattended messaging, automatic deposits, or autonomous commitment to buy.
version: 1.0.0
author: velinussage
prerequisites:
  commands: [browser-harness, python3]
metadata:
  hermes:
    tags: [shopping, facebook, marketplace, negotiation, messaging, browser-automation, pricing]
    related_skills: [facebook-marketplace-buyer, facebook-marketplace-scout, facebook-marketplace-deal-assessor, facebook-marketplace-pickup-manager]
    requires_toolsets: [terminal]
---

# Facebook Marketplace Negotiator

Use this skill after a promising listing has already been identified.

Its job is to help Hermes:
- decide whether a listing is worth messaging
- draft strong opener and counteroffer messages
- interpret seller responses
- manage negotiation state
- prepare the user for a likely deal outcome

## When to Use

Use this skill when:
- the user picked one or more serious candidate listings
- the user wants help drafting an opener
- the user wants suggested offer bands
- the user wants help interpreting seller replies
- the user wants Hermes to optionally send messages, but only with explicit approval

## Don't Use When

Do not use this skill when:
- the user still needs a shortlist first
- the user expects fully unattended messaging
- the seller is asking for deposits or suspicious off-platform payment
- the user has not approved seller outreach

## Core rule

**Every seller-facing action requires explicit approval.**

That means Hermes must pause and ask before:
- sending the first message
- sending a counteroffer
- agreeing to a price
- sharing phone number
- confirming the user is definitely buying

## Procedure

### 1. Build the negotiation dossier

Before drafting anything, summarize:
- listing URL
- asking price
- likely fair range
- target price
- max price
- urgency level
- pickup radius / availability constraints
- any visible seller signals
- any risk flags
- deal-assessment summary if available

If these are missing, ask for the minimum missing values.

If a serious deal-assessment pass has not happened and pricing confidence is low, prefer routing through `facebook-marketplace-deal-assessor` before negotiation.

### 2. Draft the opener

Default opener goals:
- confirm availability
- verify one or two critical facts
- keep tone friendly and short
- avoid overcommitting too early

Good opener types:
- availability check
- condition + pickup readiness check
- soft-offer opener
- bundle opener if relevant

### 3. Suggest a price ladder

Always reason in ranges, not one number:
- ideal opening offer
- likely settle range
- hard stop

Explain why the range makes sense using:
- comp listings
- listing age
- condition
- seller motivation clues
- convenience / pickup friction

### 4. Handle seller replies

Classify seller posture as:
- responsive and flexible
- firm but real
- vague / flaky
- suspicious
- low-value to continue

For each reply, draft the next best response and explain:
- what signal the seller gave
- what Hermes would send next
- whether to continue or walk away

### 5. Approval-gated sending mode

If and only if the user explicitly says to send, Hermes may use browser-harness to send the exact approved message.

Required pattern:
1. show the exact message draft
2. wait for explicit user approval
3. send only that message
4. report what was sent
5. re-read the thread before proposing the next message

Never silently paraphrase the approved text.

### 6. Stop conditions

Stop and escalate to the user if:
- seller requests deposit
- seller pushes off-platform payment quickly
- seller tries to move to text/phone before trust is established
- listing details are inconsistent
- seller becomes abusive or manipulative
- price exceeds the user’s max band

## Pitfalls

- Over-negotiating a strong listing can lose the deal.
- Lowballing too early can reduce response rate.
- Some sellers respond badly to long explanations; keep messages short.
- Never let “I can pick up today” become a commitment unless the user approved the plan.
- Do not confuse fast reply speed with trustworthiness.

## Verification

Before finishing, verify:
- a listing URL and price context were present
- a target range and hard stop were stated
- every seller-facing draft was shown before any send
- no deposit or payment was approved
- no autonomous commitment to buy occurred
