---
name: facebook-marketplace-seller-communication
description: "USE WHEN you want the agent to communicate with a Facebook Marketplace seller in a natural buyer voice: ask for info, negotiate within limits, and arrange a meetup after validating availability — with a per-message approval gate (each outgoing draft requires exact-text approval; never standing approval). DON'T USE WHEN you want unattended payments, deposits, or commitments outside approved boundaries."
version: 2.0.0
author: velinussage
prerequisites:
  commands: [browser-harness]
metadata:
  hermes:
    tags: [shopping, facebook, marketplace, seller-communication, negotiation, meetup, messaging]
    related_skills: [facebook-marketplace-buyer, facebook-marketplace-negotiator, facebook-marketplace-pickup-manager, facebook-marketplace-deal-assessor, facebook-marketplace-message-sender, facebook-marketplace-safety-guard]
    requires_toolsets: [terminal]
---

# Facebook Marketplace Seller Communication

**v2.0+:** Actual message sending is delegated to the shared `facebook-marketplace-message-sender` skill; this skill remains the draft-and-tone authority for buyer-to-seller outreach. Outbound drafts are also pre-checked by `facebook-marketplace-safety-guard` for off-platform asks before sending. Every send still requires the per-message `approval_token` enforced by `message-sender`.

Use this skill when the user has identified a listing they actually want to pursue and now needs the agent to communicate like a competent Marketplace buyer.

This skill covers three linked jobs:
1. ask for missing information
2. negotiate if appropriate
3. trigger and coordinate a meetup after validating the user's availability

This skill is about **buyer-to-seller communication style**, not just pricing theory.

## What good output looks like

The agent should sound like a normal, serious local buyer:
- short
- clear
- casual but polite
- not robotic
- not overly verbose
- not salesy
- not full of negotiation jargon

Bad tone:
- corporate email voice
- long explanations
- obvious AI phrasing
- too many questions at once
- fake urgency
- saying "I am definitely buying" too early

Good tone:
- "Hey, is this still available?"
- "Does everything work as expected?"
- "If it checks out, I could meet tomorrow afternoon."
- "Would you take $X if I can pick up this weekend?"

## When to Use

Use this skill when:
- the user says they want a listing and wants the agent to reach out
- the user wants to ask condition / sizing / functionality questions first
- the user wants negotiation help tied to real pickup availability
- the user wants the agent to help line up a meeting time after checking their schedule
- the item is something practical like a cold plunge, chair, desk, appliance, furniture piece, or equipment listing where info + price + pickup are all part of one communication thread

## Don't Use When

Do not use this skill when:
- the user still needs scouting first
- the seller is already clearly suspicious (deposit asks, off-platform payment push, inconsistent listing)
- the user has not given price or scheduling boundaries
- the task requires autonomous deposits, payments, or sensitive identity disclosure

## Core rule

**Seller-facing messages must stay inside explicit user-approved boundaries.**

That means the agent should know before sending anything:
- whether the user wants info-only, info+offer, or ready-to-meet messaging
- the user's target price and hard stop
- the user's availability windows
- the user's pickup-distance tolerance
- whether the user is okay with same-day / next-day pickup

## Procedure

### 1. Build the communication brief

Before drafting or sending anything, gather:
- listing URL
- whether the listing came from a direct link, a bookmark, or an active highlighted Marketplace tab
- item title / ask price
- what the user wants to know first
- target price
- max price / hard stop
- whether the user wants to negotiate immediately or only after answers
- earliest day/time the user is actually available
- acceptable meetup windows
- pickup radius / location preference
- any special constraints
  - vehicle size
  - helper needed
  - power / plumbing / loading questions
  - whether testing is required before purchase

Before drafting, the agent should open the listing in the logged-in browser, confirm the message composer exists, and treat the resulting outbound text as a post from the user's own Facebook account rather than from the agent.

Tab hygiene rule:
- if the agent opens a fresh listing tab only for inspection, drafting, or message delivery, it should close that tab after the task completes
- if the agent is operating in the user's already-active listing tab, it should leave that tab in place
- the skill should not keep spawning throwaway Marketplace tabs across repeated runs

Important Marketplace UI behavior:
- opening the composer may surface Facebook's own prefilled opener such as "Hi [name], is this still available?"
- that prefilled opener must be treated as an unsent draft only
- exact-text approval for a custom message does **not** authorize sending Facebook's prefilled default
- the agent must replace the draft with the approved text before any send action

If the user says "I want it," do **not** skip schedule validation.
You must still validate real availability before proposing meetup windows.

### 2. Choose the communication mode

Pick one of these communication modes explicitly:

#### A. Info-first
Use when the listing needs clarification before price talk.
Examples:
- condition unclear
- dimensions unclear
- functionality unclear
- accessories / parts unclear

#### B. Info + soft negotiation
Use when the user wants to ask questions and float a price if answers are good.

#### C. Ready-to-buy with meetup trigger
Use when the user already wants the item if condition is confirmed and wants to line up pickup quickly.

### 3. Validate the user's availability before meetup messaging

Before suggesting times to the seller, confirm:
- what day(s) the user is available
- what time windows are actually realistic
- whether the user can do same-day pickup
- whether the user wants a public meetup vs seller address vs porch pickup

If the user hasn't provided real windows, ask first.

Good prompt to the user:
- "Before I propose pickup times, what windows are you actually available?"
- "Can you do today, tomorrow, or only this weekend?"

### 4. Draft messages in real Marketplace buyer style

Message rules:
- 1 to 4 short sentences
- one main purpose per message
- at most 1 to 3 questions
- sound local and practical
- mention pickup timing only when useful
- do not over-explain the negotiation logic

#### Information-gathering opener
Best for uncertain listings.

Pattern:
- availability
- one or two critical questions
- optional signal that you can pick up if it checks out

Example:
- "Hey, is this still available? I'm interested. Does everything work as expected, and are there any leaks or issues? If it checks out I may be able to pick up this weekend."

#### Soft-offer opener
Best when the item looks good and the user has a target price.

Pattern:
- availability
- short condition check
- offer tied to pickup ability

Example:
- "Hey, is this still available? If everything is working and the condition is as shown, would you take $250? I could pick up Saturday afternoon."

#### Meetup-trigger message
Best after the seller answered enough questions.

Pattern:
- acknowledge response
- propose 2 or 3 actual windows from the user's availability
- ask for what works best

Example:
- "Sounds good. I could come by tomorrow between 2–4pm or Sunday morning around 10–11. What works best for you?"

### 5. Special handling for larger / testable items

For listings like a cold plunge, sauna, appliance, electronics, or furniture requiring inspection, prefer asking for operational confirmation before price commitment.

Cold-plunge example checks:
- does it chill properly
- any leaks
- model / dimensions
- any maintenance issues
- can it be tested or seen running
- what help or vehicle is needed for pickup

Example opener for a cold plunge:
- "Hey, is this still available? I'm interested. Is it fully working and does it chill properly without leaks or issues? If so, I may be able to come take a look this weekend."

Example follow-up with price + timing:
- "Thanks — if it all checks out in person, would you take $X? I could come by Saturday afternoon or Sunday late morning."

### 6. Approval and sending mode

Default rule:
- the agent drafts first
- the user approves the exact text
- the agent sends only the approved text
- the message is posted through the user's own logged-in Facebook session, not as a separate agent identity

For speed, the user may explicitly approve a bounded communication plan such as:
- ask these two condition questions first
- negotiate within this price band
- propose these meetup windows

Even in that case, the agent should stay inside the approved bounds and not improvise larger commitments.

Never send beyond the approved boundaries on:
- price ceiling
- meeting time certainty
- saying the user is definitely buying
- off-platform contact

### 7. Reply handling

After each seller response, classify the reply:
- informative and responsive
- vague but normal
- firm on price
- flexible on price
- good candidate for meetup
- suspicious / avoid

Then choose the next message type:
- ask one follow-up question
- make / adjust offer
- move to scheduling
- walk away

### 8. Stop conditions

Stop and escalate to the user if:
- seller asks for a deposit
- seller pushes off-platform payment
- seller becomes inconsistent about condition
- seller wants commitment before answering basic questions
- seller pressure escalates unnaturally
- meetup logistics no longer fit the user's actual schedule

## Communication templates

### Template: info-first
- "Hey, is this still available? I'm interested. [Question 1]? [Question 2]?"

### Template: info + pickup intent
- "Hey, is this still available? I'm interested. [Critical question]? If it checks out, I could likely pick up [window]."

### Template: offer + pickup
- "Hey, is this still available? If [condition assumption], would you take [$X]? I could pick up [window]."

### Template: post-response scheduling
- "Great, thanks. I could meet [window A] or [window B]. What works best for you?"

## Pitfalls

- Do not propose meetup times before validating the user's real availability.
- Do not ask six questions in one message.
- Do not negotiate before clarifying condition when condition risk is high.
- Do not sound like a scripted reseller bot.
- Do not say the user is definitely buying unless explicitly approved.
- Do not promise same-day pickup if the user has not actually confirmed they can do it.

## Verification

Before finishing, verify:
- the listing URL is known
- the user's target price and hard stop are known
- the user's availability windows were validated before meetup messaging
- the drafted message sounds like a normal Marketplace buyer
- the exact text was shown before any send
- no deposit / payment / off-platform commitment was made
