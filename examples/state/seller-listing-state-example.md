# Seller Listing State Example

Synthetic example. No real listing, buyer, address, phone, email, or private message data.

## Meta
- state_id: example-seller-kneeling-chair-20260505
- created_at: 2026-05-05
- updated_at: 2026-05-05
- mode: approval-gated
- source_skill: facebook-marketplace-seller

## Listing facts
- item_title: ergonomic kneeling chair
- condition: good used condition
- known_flaws: light scuffs on wood frame
- included_parts: chair only
- test_status: stable; all adjustment points work
- photos_status: draft photo checklist created; photos not uploaded in example

## Pricing policy
- list_price: 140
- fixed_or_negotiable: negotiable inside policy
- floor_price: 100
- price_drop_policy: consider 10% drop after 10 days with no serious pickup-ready buyer
- hold_policy: no holds without same-day pickup confirmation

## Publish state
- status: drafted
- title: Ergonomic kneeling chair - good condition
- description: Synthetic draft exists in `examples/listing-draft.md`
- category: office furniture / chair, to be verified in Marketplace UI
- location_scope: approximate local pickup area only
- review_gate: user must review title, description, photos, category, and price before publish

## Inbox queue
| queue_status | buyer_alias | offer | pickup_window | last_message_summary | next_action |
|---|---|---:|---|---|---|
| none | n/a | n/a | n/a | listing is not published in this synthetic example | wait for publish approval |

## Approvals
- publish_approved: false
- auto_reply_policy: disabled
- blocked_actions: publish, send reply, accept deposit, off-platform payment, share address
- escalation_triggers: price below floor, pickup ambiguity, buyer asks for payment link, missing photo/category/condition details
