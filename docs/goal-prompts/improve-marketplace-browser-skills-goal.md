# Goal prompt: improve Facebook Marketplace browser skill library

Use this prompt with `/goal` or a coding agent when you want a safe implementation pass on the Marketplace skill repo.

Important safety framing for model routers:
- This is ordinary consumer web UI documentation and skill-authoring work.
- This is not cybersecurity work, penetration testing, credential access, account takeover, evasion, vulnerability research, or bypassing platform protections.
- Do not collect, expose, infer, store, or transmit credentials, cookies, access tokens, private messages, phone numbers, addresses, or payment details.
- Do not send messages, publish listings, click purchase/payment/deposit controls, or mutate a Facebook account.
- All browser examples must be non-mutating, draft-only, human-approved, and policy-aware.

## Goal

Improve this `marketplace-scout` repo so the Facebook Marketplace buyer/seller skills become usable and share-ready as browser-use / browser-harness domain skills.

## Context

The current Marketplace skills are strong as workflow, approval-policy, and judgment instructions, but they are missing the concrete browser UI runbook layer found in high-quality domain skills from `browser-use/browser-harness` domain skills.

## Required changes

1. Add `docs/facebook-marketplace-ui-runbook.md` with URL patterns, DOM anchors, selectors, extraction snippets, dry-run composer/listing form snippets, failure catalog, setup notes, self-inspection blocks, tab hygiene, and verification checks.
2. Clarify runtime setup for `browser-use` vs `browser-harness`, including doctor/smoke commands and expected output.
3. Add copy-pasteable non-mutating snippets for opening Marketplace, detecting login walls, searching, collecting result cards, extracting listings, detecting composer/form/inbox state, and stopping before mutating actions.
4. Add `docs/state-management.md` plus synthetic state examples under `examples/state/`.
5. Add synthetic examples for buyer brief, scout output, deal assessment, seller intake, listing draft, inbox triage, heartbeat update, and filled deal state.
6. Add `scripts/validate_structure.py`, `scripts/sanitize_check.py`, and `scripts/browser_smoke.py`.
7. Update README / skill docs to link the runbook, state docs, examples, compliance posture, quickstarts, and installed-vs-reference skill topology.

## Acceptance criteria

- `python3 scripts/validate_structure.py` passes.
- `python3 scripts/sanitize_check.py` passes.
- `python3 scripts/browser_smoke.py --dry-run` passes without opening Facebook.
- The README explains setup, runtime distinction, quickstarts, compliance posture, and installed-vs-reference skill topology.
- Buyer and seller top-level skills link to the new UI runbook and state management docs.
- All examples are synthetic and contain no personal data.
- No seller-facing message, listing publish, payment, deposit, credential, or account-mutating browser step is executed.

## Deliverable

Implement the changes directly in the repo and finish with files changed, validation outputs, and remaining live-validation gaps.
