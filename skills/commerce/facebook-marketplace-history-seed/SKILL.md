---
name: facebook-marketplace-history-seed
description: USE WHEN you want Hermes to inspect local Chrome history and turn prior Marketplace searches and product research into candidate search phrases (for Stage 1 scout) or a recency-weighted bias signal (180-day lookback, 21-day exponential decay, for Stage 0 algorithmic-feed re-ranking). DON'T USE WHEN the user already has a clear brief and does not want history input, or Chrome history is unavailable.
version: 1.1.0
author: velinussage
prerequisites:
  commands: [sqlite3]
metadata:
  hermes:
    tags: [shopping, facebook, marketplace, chrome-history, search-seeding, wishlist]
    related_skills: [facebook-marketplace-scout, facebook-marketplace-buyer, wishlist]
    requires_toolsets: [terminal]
---

# Facebook Marketplace History Seed

Use this skill to borrow signal from local Chrome history before a live Marketplace scout run.

Its job is narrow:
- inspect Chrome history safely
- recover prior Facebook Marketplace search terms and listing visits
- recover repeated product / brand / model research
- turn that evidence into a small candidate search-phrase set
- hand those phrases to the scout skill

This skill does **not** browse Marketplace directly and does **not** replace the current buying brief.

## When to Use

Use this skill when:
- the user wants prior browsing to inform what to search for on Facebook Marketplace
- the user says things like "use my Chrome history," "check what I searched before," or "borrow my old Marketplace searches"
- the product family is still ambiguous and browsing history may reveal the user’s actual brand/model vocabulary
- you want to recover previous Marketplace search phrasing before live scouting
- **Stage 0 (algorithmic feed scroll) needs a recency-weighted bias signal.** In that mode this skill's output is consumed not as candidate phrases but as `seen_listings`, `seen_searches`, `recurring_domains`, and a `title_vocab` map. The buyer skill re-ranks the 100-card Browse-All capture using a 21-day exponential decay over the per-visit timestamps in Chrome's `visits` table (180-day lookback). See `../facebook-marketplace-buyer/references/local/facebook-marketplace-feed-scroll.md`.

## Don't Use When

Do not use this skill when:
- the current buying brief is already clear and history adds little value
- the user does not want past browsing used
- Chrome history is unavailable
- you need live listing ranking rather than search-phrase seeding

## Borrowed source

This skill borrows the workflow shape from the local Sage library:
- library: `chromehistory-to-facebookmarketplace`
- skill: `wishlist`

Use that as conceptual guidance, but keep this skill focused on one narrow deliverable: **history-informed Marketplace search seeds**.

## Procedure

### 1. Start with the current brief

Lock in the current brief first if available:
- product family
- wanted brands/models
- excluded brands/models
- max budget and target price
- acceptable condition
- pickup radius
- urgency
- whether generic clones are acceptable

History must not silently override this brief.

### 2. Read Chrome history safely

Do not query the live SQLite DB directly if Chrome may have it open.

Preferred path:
- copy the Chrome `History` SQLite DB first
- query the copied DB
- read shopping-like evidence from the copied file

Useful Chrome profile locations:
- `~/Library/Application Support/Google/Chrome/Default/History`
- `~/Library/Application Support/Google/Chrome/Profile 1/History`

Default lookback guidance:
- do **not** default to only the last few days
- a good normal starting window is **60 to 180 days** depending on browsing volume
- if the user explicitly wants older intent recovery, bias wider first rather than fresher first
- only narrow to recent history when the user specifically wants current / trending intent

### 3. Prioritize the highest-signal history rows

Strongest signals:
- prior `facebook.com/marketplace/...search?...query=...`
- prior `facebook.com/marketplace/item/...` listing visits
- repeated branded product pages
- repeated review / comparison pages
- repeated retailer pages for the same model family

Weak signals to suppress:
- generic category terms on their own
- unrelated furniture terms
- account pages
- one-off noisy tabs with no supporting evidence

### 4. Normalize into product families before extracting phrases

Do not treat every literal string as a separate intent.

First cluster history evidence into product families and aliases.

Example rule:
- `varier chair`, `varier balans`, `stokke varier`, `balans chair`, `kneeling chair`, `kneeling desk chair`, and `ergonomic kneeling chair` may all belong to the **same kneeling-chair family** even when the wording differs

The goal is to recover the user's actual shopping family, not just the freshest literal query.

Within a family, keep **subtype diversity** when the evidence supports it.

For kneeling-chair history, useful subtype buckets may include:
- premium branded kneeling chairs (`varier`, `balans`, `stokke varier`)
- generic bentwood / rocking kneeling chairs
- office-style padded kneeling chairs
- adjacent ergonomic seating that may still matter, but should stay labeled as adjacent rather than identical intent

Important rule:
- keep true aliases together
- keep adjacent-but-different products separate but nearby
- do not split one family just because the user used both branded and generic search phrases

### 5. Extract candidate phrases

Turn the normalized family evidence into a small candidate set such as:
- exact prior Marketplace search strings
- repeated brand/model phrases
- product-family + brand combinations
- 1 or 2 subtype-diverse family probes
- one generic fallback only if the history is too sparse

Prefer compact, product-shaped phrases over broad nouns.

Good examples:
- `varier balans`
- `stokke varier balans`
- `kneeling desk chair`
- `ergonomic kneeling chair`
- `bentwood kneeling chair`
- `capisco chair` only if the agent labels it as adjacent ergonomic seating rather than the same kneeling-chair intent

Bad examples:
- `chair`
- `furniture`
- a seller-specific title copied verbatim
- a location phrase with no product signal
- treating `varier chair` and `kneeling chair` as unrelated families when the browsing trail says otherwise

### 6. Reconcile history against the current brief

Apply the brief as a filter:
- if the user wants branded only, drop clone-heavy generic phrases
- if the user excludes a brand, drop those history phrases
- if the budget changed, keep the phrase but not the old price assumptions
- if the product target changed, do not import adjacent old searches

Simple rule:
- current brief wins
- history seeds the search

### 7. Hand off to scout

Return a compact handoff like:
- current brief summary
- normalized product family or families
- strongest history-derived candidate phrases
- which came from prior Marketplace searches
- which came from listing visits or product research
- which subtype buckets were retained
- which phrases were rejected and why
- recommended first 2 to 5 live Marketplace queries for the scout skill

When the evidence supports it, include a **diverse query set** inside the same family rather than one narrow literal string.

Example for kneeling-chair family:
- premium branded probe: `varier balans`
- second premium alias probe: `stokke varier kneeling chair`
- generic family probe: `kneeling chair`
- subtype probe: `bentwood kneeling chair`
- office-style subtype probe: `kneeling desk chair`

## Example output

```md
History-informed search seeds

Current brief
- kneeling chair family
- budget under $250
- branded preferred, but compare against strong generic subtypes too

Normalized family
- kneeling-chair family
- aliases seen: varier chair, varier balans, kneeling desk chair

Recovered history signals
- prior Marketplace search: varier chair
- prior Marketplace search: kneeling desk chair
- repeated product research: Stokke Varier / Balans-style seating

Recommended live queries
1. varier balans
2. stokke varier kneeling chair
3. kneeling chair
4. bentwood kneeling chair
5. kneeling desk chair

Rejected seeds
- chair (too broad)
- office chair (too generic)
```

## Pitfalls

- Old browsing can be stale. Do not treat it as current intent without checking against the brief.
- Prior Marketplace searches may reflect exploration, not preference.
- Listing-title phrases often make bad recurring search queries.
- Generic category words create noise quickly.
- Do not mistake alias diversity for product-family diversity: `varier chair` and `kneeling chair` may be the same family, not separate intents.
- Do not overfit to the freshest local generic query if older branded history clearly belongs to the same family.
- If the user is present and the brief is missing, ask instead of overfitting to history.

## Verification

Before finishing, verify:
- Chrome history was read from a copied DB or equivalent safe method
- the lookback horizon was long enough to recover older still-relevant product intent
- prior Marketplace search terms were extracted if present
- repeated product/brand/model evidence was normalized into product families instead of only literal strings
- alias terms like `varier chair` and `kneeling chair` were clustered correctly when the evidence supports it
- subtype diversity was preserved when useful
- history was used to seed phrases, not override the current brief
- the output contains a compact but diverse set of candidate search phrases for the scout skill
