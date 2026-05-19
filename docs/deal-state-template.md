# Deal State Template

Use this template to keep active chats and in-progress sales legible across Marketplace sessions.

Purpose:
- preserve continuity between narrow skills
- make queue order explicit
- record what is blocked on the user vs blocked on the counterparty
- support operator-first mode by default
- support bounded autonomous mode only when policy is explicit

---

## Template

```markdown
# Marketplace Deal State

## Meta
- mode: operator-first | bounded-autonomous
- operator_contact_path: <telegram / sms / hermes gateway / other>
- last_updated: <timestamp>
- owner: <user>
- workflow: buyer-side | seller-side
- listing_id: <local alias or facebook URL>
- item_title: <text>
- current_stage: <scout | assess | negotiate | pickup | listing-intake | draft | publish | inbox-triage | heartbeat>

## Policy
- price_mode: fixed | negotiable
- list_price: <amount>
- minimum_price: <amount or n/a>
- hold_policy: none | bounded | allowed
- queue_rule: first-real-pickup | seller-choice | other
- approved_windows: <text or none>
- availability_rule: ask-user-first | pre-approved-windows
- blocked_actions:
  - deposits
  - payments
  - off-platform payment handling
  - sensitive identity disclosure
- escalation_triggers:
  - price ambiguity
  - queue ambiguity
  - conflicting serious buyers
  - safety ambiguity
  - off-platform pressure

## Active Chats
| rank | thread_id | name | role | state | offered_price | pickup_ready | last_inbound | last_outbound | next_action | waiting_on |
|------|-----------|------|------|-------|---------------|--------------|--------------|---------------|-------------|------------|
| 1 | ... | ... | buyer/seller | candidate / scheduled-primary / backup-1 / stalled / suspicious | ... | yes/no | ... | ... | ... | user / counterparty / none |

## Primary / Backup Order
- primary: <thread_id>
- backup_1: <thread_id>
- backup_2: <thread_id>
- reason_for_order: <short rationale>
- primary_slot_status: open | scheduled | released
- backup_message_policy: tell backups someone is ahead | other

## In-Progress Sale Status
- sale_state: scouting | assessing | negotiating | ready-awaiting-user | ready-awaiting-counterparty | scheduled | pending-pickup | closed | abandoned
- confidence: high | medium | low
- worth_pursuing: yes | no | uncertain
- next_operator_action: <single sentence>
- next_autonomous_action_if_allowed: <single sentence>

## Clarifications Needed From User
- <question 1>
- <question 2>

## Notes
- facts learned
- safety concerns
- condition concerns
- timing constraints
- why the current path is still or is not worth pursuing
```

---

## How to use it

### Operator-first mode
Default mode.

Use this template to:
- summarize active chats
- show queue order
- mark what is waiting on the user
- ask for clarification through the operator’s open gateway when policy/state is incomplete

### Bounded autonomous mode
Only use after explicit policy is provided.

Use this template to:
- confirm the policy fields exist
- keep autonomous actions inside scope
- stop and route questions back to the user if the template shows missing fields or ambiguity

## Minimum required fields before any autonomous send/confirm action

- mode = bounded-autonomous
- operator_contact_path is set
- price_mode is set
- blocked_actions are explicit
- escalation_triggers are explicit
- queue_rule is explicit for seller-side flows
- availability_rule is explicit
- no unresolved clarification remains in `Clarifications Needed From User`

If any are missing:
- do not improvise
- ask the user through the open gateway

## Why this matters

A collection of Marketplace skills is only pragmatically useful if it can preserve continuity.
Without a durable state surface:
- active chats become hard to rank
- in-progress sales lose order
- policy drifts between skills
- the runtime becomes less trustworthy

This template is the minimum continuity layer that lets the collection behave like a real operational system instead of a bag of prompts.
