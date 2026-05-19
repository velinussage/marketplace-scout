---
name: facebook-marketplace-watch-notifier
description: USE WHEN you want Hermes to notify the user after a scout or deal-assessment run, especially through a Hermes gateway chat, cron delivery target, or approved messaging target. DON'T USE WHEN you want Hermes to message sellers, negotiate, or send noisy notifications for weak leads.
version: 1.0.0
author: velinussage
metadata:
  hermes:
    tags: [shopping, facebook, marketplace, alerts, watchlist, gateway, notifications]
    related_skills: [facebook-marketplace-buyer, facebook-marketplace-scout, facebook-marketplace-deal-assessor]
    requires_toolsets: [terminal]
---

# Facebook Marketplace Watch Notifier

Use this skill after scouting or deal assessment when the user wants Hermes to push a summary or alert back through Hermes messaging / gateway surfaces.

Its job is to notify the user about:
- a new shortlist
- a high-quality candidate
- a strong or exceptional deal
- a notable price drop
- a watchlist hit worth reviewing

This skill does **not** contact sellers.

**Cadence is harness-owned, not skill-owned.** Scheduling, cron triggers, and push delivery live in the Hermes harness; this skill only formats the payload and chooses the delivery target. Do not invent a polling loop inside the skill.

## When to Use

Use this skill when:
- the user wants a post-scout summary pushed back automatically
- scouting or watch jobs run on a schedule
- Hermes is running inside a gateway-backed chat or channel
- the user wants asynchronous alerts for good deals

## Don't Use When

Do not use this skill when:
- the user is already actively watching the live chat and does not need delivery
- the result is weak / noisy / not worth interrupting the user for
- there is no valid gateway or messaging delivery path
- the task is to message a seller

## Delivery model

Hermes already has gateway-backed delivery patterns.

Preferred delivery order:
1. same Hermes gateway chat / channel the job ran in
2. cron auto-delivery target
3. explicit approved messaging target
4. no-send fallback: write or display the result locally

Practical guidance:
- for background or messaging-platform runs, prefer native Hermes result delivery back to the same chat
- for scheduled jobs, prefer cron-delivered summaries
- only use explicit message sending when a target exists and the user wants that behavior

## Procedure

### 1. Decide whether the result is notification-worthy

Notify only when one of these is true:
- a new shortlist was generated and the user asked to be updated
- a listing crossed a quality threshold
- a deal assessor labeled it `strong deal` or `exceptional deal`
- a watched item dropped into the user’s target band

Do not notify for weak or noisy findings unless the user asked for every run summary.

### 2. Build a compact notification

A good notification includes:
- product family
- top listing or shortlist count
- best price / deal label
- why it matters in one line
- direct listing URL(s)
- next suggested action

Example:

```md
Marketplace watch hit: strong deal
- Product: Varier Balans kneeling chair
- Best listing: $140 in Durham
- Why it matters: below typical branded used range and far below new-price anchors
- Link: https://www.facebook.com/marketplace/item/...
- Next action: review deal assessment, then approve outreach if you want to message
```

### 3. Prefer Hermes-native delivery when available

If Hermes is running in a gateway session or via background / cron delivery, prefer sending the result back to the same chat or channel.

Good patterns:
- background scout finishes and posts back to the same chat
- scheduled watch job delivers a concise summary to the configured destination

### 4. Use explicit messaging targets carefully

If the user wants delivery to a specific target, resolve the target first and keep the message concise.

Do not guess targets.
If the messaging tool requires target discovery, list targets first.

### 5. Keep notifications low-noise

Suggested notification thresholds:
- notify immediately: exceptional deal, strong deal, or very close match to the user’s brief
- batch in summary: fair deals or broad shortlist updates
- suppress: weak / overpriced / suspicious leads unless explicitly requested

## Pitfalls

- A notifier that fires on every mediocre listing becomes useless.
- Gateway delivery is better than ad hoc sends when the run already has a live chat context.
- Do not notify without URLs or concrete actionability.
- Notification content should be shorter than the assessment itself.
- Never use this skill to message sellers.

## Verification

Before finishing, verify:
- the result actually met the notification threshold
- the summary contains at least one concrete listing URL or shortlist reference
- the delivery path is valid
- the next suggested action is clear
- no seller-facing action was taken
