---
name: facebook-marketplace-publish-manager
description: USE WHEN you want the agent to prepare, review, or execute the Marketplace listing publish workflow: map the draft into form fields, check consistency, publish with approval or policy, and manage relist / renew / price-drop actions. DON'T USE WHEN the listing brief is still incomplete or when unbounded autonomous publishing is expected.
version: 1.0.1
author: velinus
prerequisites:
  commands: [browser-harness, python3]
metadata:
  hermes:
    tags: [shopping, facebook, marketplace, seller, publish, relist, price-drop, browser-automation]
    related_skills: [facebook-marketplace-seller, facebook-marketplace-listing-intake, facebook-marketplace-listing-drafter, facebook-marketplace-buyer-inbox-triage, facebook-marketplace-inbox-heartbeat]
    requires_toolsets: [terminal]
---

# Facebook Marketplace Publish Manager

Use this skill when the listing draft is ready and the task moves into form-fill, publish, renew, relist, or controlled price adjustments.

## When to Use

Use this skill when:
- the user wants help turning a draft into a live Marketplace listing
- the listing text is mostly ready and now needs operational execution
- the user wants bounded automation around relist or price-drop flows

## Don't Use When

Do not use this skill when:
- the underlying seller brief is incomplete
- the photos, flaws, or price floor are still uncertain
- the user expects unbounded autonomous publishing without policy

## Procedure

### 1. Validate publish readiness

Before publish, confirm:
- title and description are final enough
- category and condition selection are coherent
- all required Marketplace details are actually set and no required field still shows as invalid
- price floor exists
- price source is traceable: user-set or comps-derived
- pickup / delivery language is correct
- photo set is adequate
- automation mode is explicit
- title and description have been reviewed by the user unless a bounded publish policy explicitly allows skipping that review

### 2. Map the draft into form fields

Prepare and verify:
- category
- title
- price
- condition
- description
- location / pickup notes
- tags / attributes if the form needs them

Do not assume a field is committed just because text is visible. Re-check the actual form state after interaction, especially category and other combobox-style fields.

### 3. Publish policy

Default behavior:
- draft-only or approval-gated mode requires final confirmation before publish
- the user reviews title and description before publish
- if any required Marketplace detail is still uncertain, invalid, or not committed, save draft and ask the user to review instead of forcing a publish

Bounded auto-publish is only acceptable when:
- the title / description template is pre-approved
- price is inside policy
- blocked phrases / claims are defined
- the item does not require nuanced risk review

If price was derived from comps, report:
- the comp logic used
- whether the search radius had to be expanded
- the exact pricing rule applied, such as listing at half of comparable asking price

### 4. Post-publish operational moves

This skill may also manage:
- renew listing
- relist listing
- pre-approved price drop ladder
- mark pending or unavailable when policy allows

Do not let these actions contradict the configured floor or hold policy.

### 5. Reporting

After any publish-side action, report:
- what action happened
- which fields were used
- whether all required Marketplace details were successfully set
- current listing price
- whether the user review gate was used or skipped by policy
- whether the listing was saved as draft due to uncertainty
- any warning or policy edge hit
- next expected seller-side workflow stage
- whether the next stage is `facebook-marketplace-buyer-inbox-triage` or `facebook-marketplace-inbox-heartbeat`
- whether `docs/deal-state-template.md` was created or updated for this listing

Once the listing is live, treat active chats and in-progress sales as a continuity problem, not a one-shot publish result.
If post-publish policy is incomplete, route clarification back to the user through the open gateway / operator contact path before enabling autonomous reply behavior.

## Pitfalls

- Publishing before flaw disclosure is complete creates avoidable buyer conflict.
- Auto price drops without a floor invite bad outcomes.
- Relist and renew actions should follow policy, not impatience.
- If browser control is degraded, stop instead of pretending to publish.
- A published listing without continuity state for active chats and in-progress sales is operationally incomplete.
- If inbox autonomy is intended after publish, missing policy fields should route back to the user for clarification instead of silently enabling auto-replies.

## Verification

Before finishing, verify:
- the listing was publish-ready
- all required Marketplace details were actually set and valid
- the action matched the automation mode
- no publish-side rule violated the price floor or blocked actions
- the review gate before publish was respected unless policy explicitly overrode it
- if there was uncertainty, draft was saved and the user was asked to review
- a post-action report was produced
