# Publication Sanitization Checklist

Use this checklist before publishing the Marketplace skills repo to GitHub or Sage.

## 1. Remove operator-local details

Check every `README.md`, `SKILL.md`, and `docs/*.md` file for:
- absolute paths such as `/Users/...`
- home-relative paths that assume one machine layout
- references to one operator's preferred clone location
- account-specific browser state or private browsing history
- copied terminal output that exposes local machine structure

Preferred replacements:
- `<repo-root>/skills`
- "present on `PATH`"
- "logged-in browser session"
- "a live Marketplace listing"

## 2. Remove one-off Marketplace artifacts

Do not publish:
- specific listing URLs unless they are intentional public examples
- specific item IDs that came from real live runs
- seller names from one-off tests
- message transcripts that belong to a real person
- screenshots containing personal account state unless explicitly intended

Preferred replacements:
- `https://www.facebook.com/marketplace/item/...`
- "a live Marketplace listing"
- "a seller-facing thread"
- generic example text

## 3. Keep reusable runtime truth

Preserve findings that are portable across operators, such as:
- browser-harness can suffer stale websocket failures
- direct Marketplace item links can be valid entrypoints
- Facebook may prefill a default opener when the composer opens
- exact-text approval must not be interpreted as approval for the default prefilled opener
- temporary Marketplace tabs should be closed after inspection or messaging steps
- Messenger popup reply automation needs stronger exact-text-safe guards

## 4. Keep the skill layer honest

Before publishing, verify the skills:
- do not claim full autonomy where approval gates still exist
- do not claim exact-text-safe sending if the runtime still has edge cases
- clearly separate drafting, supervised sending, and bounded autonomous mode
- document dependencies on browser-harness or other runtime components explicitly

## 5. Make repo setup fork-friendly

Before publishing, verify:
- docs refer to this repo's `skills/` directory generically
- host-specific setup instructions (e.g. Hermes `skills.external_dirs`, Claude Code skill paths) do not assume one person's local path
- runtime assumptions are described in generic terms
- commands are phrased to work from any clone location where possible

## 6. GitHub publication pass

Before pushing to GitHub:
- repo name is descriptive
- root `README.md` explains buyer-side and seller-side flows clearly
- docs mention what is proven vs not yet proven
- no accidental secrets, session artifacts, or copied live-account details remain
- any intentionally local runtime notes are moved into a clearly marked non-portable section or removed

## 7. Sage publication pass

Before publishing into Sage:
- `SKILL.md` files are honest and portable
- examples do not leak local paths or private listing history
- repo-level docs do not depend on one operator's browser/session state
- external runtime dependencies are declared explicitly
- the shareable asset is the policy/workflow layer, not hidden account state

## 8. Final operator check

Ask:
- could another operator fork this repo and understand the workflow without my machine?
- could they tell which parts are portable skill logic vs runtime-specific caveats?
- would I be comfortable with every URL, name, and transcript fragment in this repo being public?

If any answer is no, sanitize again before publication.
