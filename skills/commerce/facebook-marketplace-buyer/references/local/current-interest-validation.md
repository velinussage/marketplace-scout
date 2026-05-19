# Current Interest Validation Pattern

## Rule
Before any live Marketplace search or scout, the agent MUST validate the user's current interest using recent signals and explicit confirmation.

## Why this matters
Old interests (e.g. "varier chair" from months ago) frequently pollute results when history is used naively. The user expects the skill to surface recent signals, ask for confirmation, and only then proceed.

## Required behavior
1. Check recent browser history / wishlist signals (prefer last 30-60 days).
2. Summarize the strongest current signals to the user.
3. Explicitly ask for confirmation or updated preferences.
4. Only run live search after user approval of the current target.

Old signals may be mentioned only as historical context, never as the default search target.

## Trigger phrases
- "validate current interest"
- "don't use old searches"
- "check what I'm actually looking for right now"

## Implementation location
This rule is enforced in the scout behavior and should be referenced by any Marketplace buyer workflow that involves discovery.