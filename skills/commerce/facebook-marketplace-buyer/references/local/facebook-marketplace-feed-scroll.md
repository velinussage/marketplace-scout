---
name: facebook-marketplace-feed-scroll
description: USE WHEN you want the agent to discover Marketplace listings by passively scrolling the default Browse All feed and letting Facebook's own ranking surface what's interesting, then re-ranking those cards against the user's recent Chrome history bias. Captures detail-page screenshots for the top 3 candidates, then hands off to the report generator. No search query against Marketplace; the feed stays Browse All.
version: 0.7.0
author: velinussage
prerequisites:
  commands: [browser-harness]
  browser:
    - browser-harness daemon attached to the user's logged-in Chrome (run `browser-harness --doctor` to verify)
metadata:
  hermes:
    tags: [shopping, facebook, marketplace, browser-automation, feed-scroll, discovery, algorithmic, agent-led]
    related_skills:
      - facebook-marketplace-buyer
      - facebook-marketplace-scout
      - facebook-marketplace-deal-assessor
      - facebook-marketplace-report-generator
      - facebook-marketplace-seller-communication
    requires_toolsets: [terminal]
---

# Facebook Marketplace Feed Scroll (Stage 0)

Use this skill to discover Marketplace listings without supplying a query. Open Marketplace, scroll the **default Browse All feed**, and trust Facebook's ranking to surface interesting posts. Then score and report.

This is the buyer-agent counterpart to passive newsfeed reading: the user delegates discovery itself, not just search.

## When to Use

Use this skill when:
- The user wants ambient Marketplace discovery ("what's worth looking at right now?") instead of searching for something specific.
- The user has approved a feed-driven buyer's-agent loop and is not supplying a search brief.
- An on-demand scout run should kick off without prior interest input.

## Don't Use When

- The user has a specific product brief, brand, or budget bracket → use `facebook-marketplace-scout` (Stage 1) instead.
- The user is mid-negotiation with an existing seller → route to `facebook-marketplace-seller-communication`.
- `browser-harness --doctor` reports the daemon isn't alive or Chrome isn't attached; or the user is not signed into Facebook in that Chrome.

## Core Principles

1. **No buying-brief gate, but a Chrome-history bias pass.** The skill never asks "what are you shopping for." Instead, it reads recent Chrome history (via the existing `facebook-marketplace-history-seed` reference) to build a *bias profile* — categories, brands, product families the user has actually been engaging with. Browse All discovery stays algorithmic; bias only affects which cards get re-ranked into the top 3 for the report. History informs the lens; it does not gate or filter the feed.
2. **Agent-led, end-to-end via browser-harness.** The Claude agent drives `browser-harness` directly through ephemeral Bash heredocs. No persisted Python generators, no `generate_*.py`. See memory `feedback-reports-html`, `feedback-browser-tool`, and `project-scout-vision`.
3. **Top 50 broad survey by default.** The report ships with the **fifty highest-scoring** cards — a wide scannable view of what the algorithm + bias surface together, not a 3-card deep dive. Capture broadly during the scroll (~80 unique cards), score all, render the top 50 as compact cards. See memory `feedback-top-n-50`.
4. **Recency-weighted bias scoring.** Per-visit timestamps drive an exponential decay (21-day half-life) so a click from yesterday outweighs ten clicks from five months ago. The previous "raw visit_count" approach buried fresh signal under accumulated long-tail. See memory `feedback-recency-bias`.
5. **Images come from feed-card thumbnails downloaded locally, not detail-page extraction at this scale.** 50 detail-page opens would be ~12 minutes of automation and ~16 MB of gallery downloads. Instead, each of the top 50 uses its `thumb_url` (the `scontent.fbcdn.net` URL already captured during the scroll), downloaded with `curl` to `reports/images/feed_<run_id>/<rank>.jpg`. One image per listing, ~30–50 KB each. The detail-page deep extraction (`feed_<run_id>_<rank>/00..05.jpg` gallery layout) is opt-in only — invoked explicitly when the user wants a tighter "featured" subset.
6. **No seller-facing action.** This skill never opens a listing-message composer, never types into one, never sends. Detail pages are not opened at all in the default top-50 flow. Seller contact is gated to Stage 4 with per-message approval.

## Procedure

The whole flow runs inside `browser-harness <<'PY' ... PY` heredocs invoked from Bash. Helpers like `ensure_real_tab`, `open_url`, `new_tab`, `wait`, `js`, `scroll`, `screenshot`, and `page_info` are pre-imported. See `docs/facebook-marketplace-ui-runbook.md` for the field-tested snippets this skill builds on. Note: the harness helper is `new_tab(url)`; some older drafts used `open_url`. Prefer `new_tab` so we don't clobber the user's currently active tab.

### 0. Build a Chrome-history bias profile (thorough)

Before touching Marketplace, derive a *bias profile* from the user's recent Chrome history. This is the "lens" through which the feed will be re-ranked. Reuse the safe-copy + read pattern documented in the sibling `facebook-marketplace-history-seed` SKILL.

**Be thorough.** A typical active Marketplace user has 200–500 distinct `/marketplace/item/` visits in 180 days. Do not compress that down to a handful of theme summaries — keep the full list and use the title tokens as the scoring vocabulary. See memory `feedback-history-thoroughness`.

1. **Copy** the Chrome `History` SQLite file to a temp path (Chrome locks the live DB):
   - `~/Library/Application Support/Google/Chrome/Default/History`
   - or the active profile (e.g. `Profile 1/History`)

2. **Default lookback: 180 days**, not 90. Widen further only if sparse.

3. **Pull the full seen-listings list with per-visit timestamps.** The `urls` table's `visit_count` alone hides recency — a click from yesterday should outweigh ten clicks from five months ago. Join to the `visits` table to apply exponential decay. See memory `feedback-recency-bias`.

   ```sql
   -- Per-visit rows for every marketplace item visit in the window.
   SELECT u.url, u.title, u.visit_count,
          (v.visit_time - 11644473600000000) / 1000000 AS unix_visit_time
   FROM urls u
   JOIN visits v ON v.url = u.id
   WHERE u.url LIKE '%facebook.com/marketplace/item/%'
     AND u.title != ''
     AND v.visit_time > (strftime('%s', 'now', '-180 days') * 1000000 + 11644473600000000)
   ORDER BY v.visit_time DESC;
   ```

   In post-processing:
   - Canonicalize each URL (strip query string after `/marketplace/item/<id>/`).
   - Group by canonical URL.
   - For each URL, compute `recency_weight = Σ exp(-age_days / 21)` across all its visits. (21-day half-life; shorter kills slow-cooked interests, longer lets long-tail dominate.)
   - Also track `last_visit_age_days = (now - max(unix_visit_time)) / 86400` and raw `visit_count`.
   - Cap output at 500 entries, sorted by **`recency_weight`** desc (not `visit_count`).

   Store as `seen_listings: [{ url, title, visit_count, recency_weight, last_visit_age_days }]`.

4. **Pull marketplace search queries with the same per-visit recency treatment.** Apply the same decay formula. Store as `seen_searches: [{ query, visit_count, recency_weight, last_visit_age_days }]`, sorted by `recency_weight` desc.

5. **Pull recurring retailer / review / brand domains.** Aggregate per-visit `recency_weight` by domain (not raw visit_count), exclude noisy ubiquitous domains (`google.com`, `youtube.com`, `github.com`, `claude.ai`, `chatgpt.com`, `linear.app`, `docs.google.com`, etc.), and keep the top 30 by `recency_weight`. Store as `recurring_domains: [{ domain, visit_count, recency_weight, last_visit_age_days }]`.

6. **Build the title vocabulary, recency-weighted.** Tokenize every title in `seen_listings`, lowercase, drop stopwords (`marketplace`, `facebook`, `for`, `sale`, `the`, `a`, `an`, `with`, `and`, `or`, `in`, `on`, `of`, `to`, common emojis like `🟢`, parenthesized numbers like `(1)`), then **sum `recency_weight` per token across all matching listings**. Keep tokens whose recency_weight summed across ≥2 distinct listings exceeds a small floor (e.g. 0.2 — guards against one-off noise). Store as `title_vocab: { "varier": 7.4, "kneeling": 5.1, "steelcase": 2.3, ... }`.

7. **Cluster a small set of human-readable themes** (3–10) for the report's "Why these top picks" explainer — `bias_terms` sourced from the top entries in `title_vocab` (recency-sorted) plus the recency-sorted `seen_searches`. These are display-only; scoring uses the full `title_vocab`.

8. Emit the bias profile to `reports/bias_<run_id>.json`:

```json
{
  "run_id": "20260519-1042",
  "lookback_days": 180,
  "decay_half_life_days": 21,
  "history_available": true,
  "marketplace_items_seen": 438,
  "marketplace_searches_seen": 27,
  "seen_listings": [
    { "url": "https://www.facebook.com/marketplace/item/...",
      "title": "Varier Kneeling Chair",
      "visit_count": 9,
      "recency_weight": 6.42,
      "last_visit_age_days": 1.8 }
  ],
  "seen_searches": [
    { "query": "kneeling chair", "visit_count": 4, "recency_weight": 2.91, "last_visit_age_days": 3.2 }
  ],
  "recurring_domains": [
    { "domain": "estatesales.net", "visit_count": 716, "recency_weight": 142.5, "last_visit_age_days": 0.4 }
  ],
  "title_vocab": { "varier": 7.4, "kneeling": 5.1, "steelcase": 2.3, "hovet": 1.6 },
  "bias_terms": [
    { "term": "kneeling chair", "aliases": ["varier", "balans"], "weight": 6.4,
      "recency_weight": 6.42, "last_visit_age_days": 1.8,
      "source": "Varier Thatsit listing clicked 2 days ago + recurring kneeling searches" }
  ],
  "negative_terms": []
}
```

Note: `weight` and `recency_weight` are now the same value for bias_terms — both surfaced for clarity. Display the `last_visit_age_days` in the report so the user can see how fresh each theme is.

If the history DB cannot be read (Chrome locked, profile missing), fall back to `history_available: false` and a neutral scoring profile — note it in the report header so the user knows the run wasn't history-informed.

### 1. Preflight

```bash
browser-harness --doctor
```

Require `chrome running` and `daemon alive`. If either fails, stop and tell the user — do not try to relaunch their browser.

### 2. Land on Browse All and verify session

Open the feed in a fresh tab and report the surface state in one heredoc:

```bash
browser-harness <<'PY'
ensure_real_tab()
new_tab("https://www.facebook.com/marketplace/")
wait(3)
state = js("""
  (() => {
    const text = document.body.innerText || '';
    const url = location.href;
    return {
      url,
      logged_out: /\\/login|Log in|Email address or phone number/i.test(url + ' ' + text),
      checkpoint: /checkpoint|two-factor|security check/i.test(url + ' ' + text),
      card_count: document.querySelectorAll('a[href*="/marketplace/item/"]').length,
      excerpt: text.slice(0, 600)
    };
  })()
""")
print(state)
PY
```

If `logged_out` or `checkpoint` is true, stop and ask the user to fix the session manually — do not type credentials. If `card_count == 0` after a 3s wait, the feed didn't render; bail out cleanly.

Do **not** apply category filters, search queries, or radius changes — the whole point of Stage 0 is the default feed.

### 3. Scroll-and-collect loop

Use the runbook's `scroll_and_collect` pattern, capped at **~100 unique cards** (was 80). Default to **12–14 scrolls** (was 10–12). The wider capture gives the top-50 ranking real selection pressure — without it, "top 50 of 25" is meaningless. The cap was bumped from 80 → 100 because ~25% of feed anchors turn out to be "Just listed" / "Sponsored" badges that the atomic extractor (step 4) correctly skips; you need raw capture room to absorb that loss before quality filtering. Collect visible cards *before* each scroll because Facebook virtualizes the feed:

**Critical: scope title and thumb extraction to the SAME card anchor**, never combine `anchor.href` with text from a surrounding container. Otherwise a section header ("Moving out everything has to go") can attach to the wrong listing's image. See memory `feedback-card-quality`.

```bash
browser-harness <<'PY'
ensure_real_tab()
listings = js("""
  (() => {
    const anchors = Array.from(document.querySelectorAll('a[href*="/marketplace/item/"]'));
    const cards = anchors.map(a => {
      // ATOMIC: read title/price/img only from text INSIDE this anchor's subtree.
      // Surrounding container text often pulls in section headers from neighboring cards.
      const text = (a.innerText || '').trim();
      const href = a.href ? a.href.split('?')[0] : null;
      if (!href || !text) return null;             // drop cards with no title text
      // FB renders ribbon/badge anchors ("Just listed", "Sponsored", "Free")
      // using the same `a[href*="/marketplace/item/"]` pattern. Skip these
      // early so they don't burn a top-N slot only to be quality-dropped later.
      const text_norm = text.toLowerCase().trim();
      if (text_norm.length < 4) return null;
      if (/^(just listed|sponsored|free|popular|new listing|featured)$/i.test(text)) return null;
      const priceMatch = text.match(/\\$([0-9][0-9,]*)(?:\\.\\d{2})?/);
      const price = priceMatch ? parseInt(priceMatch[1].replace(/,/g, ''), 10) : null;
      // Detect "$current$original" price-drop pairs (FB renders as "$300$450").
      const dropMatch = text.match(/\\$([0-9][0-9,]*)\\$([0-9][0-9,]*)/);
      const original_price = dropMatch ? parseInt(dropMatch[2].replace(/,/g, ''), 10) : null;
      const lines = text.split('\\n').map(s => s.trim())
        .filter(Boolean)
        .filter(s => !/^\\$[0-9,]+(\\$[0-9,]+)?$/.test(s));  // skip price-only lines
      const img = a.querySelector('img');
      return { href, lines: lines.slice(0, 6), price, original_price, thumb: img ? img.src : null };
    }).filter(Boolean);
    const seen = new Map();
    for (const c of cards) if (!seen.has(c.href)) seen.set(c.href, c);
    return Array.from(seen.values());
  })()
""")
print(len(listings), "cards visible before scroll")
for _ in range(14):
    scroll(700, 500, dy=900)
    wait(1.6)
PY
```

After scrolling, run the same `js(...)` collector again and merge results, deduping by canonical `/marketplace/item/<id>/` URL. Cap the merged set at 100 unique cards (drop the tail past 100, ordered by feed_position ascending).

### 4. Per-card metadata extraction

For each unique card surfaced in step 3, record:

| Field          | Source |
|----------------|--------|
| `url`          | The card's `a[href*="/marketplace/item/"]` href, canonical (strip query string). |
| `title`        | First non-price line in the card text (typically the first entry in `lines`). |
| `price`        | The currency-prefixed token (`$\d+`); parse to int when possible. |
| `location`     | A later line in `lines` that matches `[City], [ST]` or contains ` in `. |
| `thumb_url`    | The card `<img>` `src` (Facebook CDN; signed and short-lived). |

No screenshots are taken at this step — the feed-card thumbnails are too small and the visual screenshot of the feed gets reused across adjacent cards. Screenshots happen in step 6, against detail pages.

### 4.5. Filter by block list

Before scoring, read the user's block list at `reports/.scout_block_list.txt` (one pattern per line, lines starting with `#` are comments, blank lines ignored). For each captured card, if its lowercased title contains any block-list pattern as a substring, **drop the card from the candidate set entirely**. Record the count of dropped cards for the report header.

Default block list ships with patterns like `gown`, `costume`, `weight loss`, `mlm`, `vape`, `crypto`, etc. The user is expected to edit this file over time. If the file is missing, skip this step with no blocks applied. See memory `feedback-selectivity`.

### 5. Score and pick the top N (default 50)

Score each captured card against the recency-weighted bias profile from step 0. **Use `title_vocab` and `seen_listings` with their `recency_weight` fields — not raw `visit_count`.** See memories `feedback-history-thoroughness`, `feedback-recency-bias`, and `feedback-selectivity`.

```
score = base_feed_rank_factor          (later cards score lower; e.g. 1.0 - position * 0.01
                                        with a soft floor; gentler decay than before
                                        because we want 80 cards in play, not 25)

      + url_match_bonus                        (recency-weighted; details below)

      + Σ title_vocab[token] * 0.2             (for each lowercased token of card.title that
                                                appears in title_vocab; cap each token's
                                                contribution at 2.0; cap the per-card vocab
                                                total at 5.0. Coefficient is 0.2 because
                                                title_vocab values are decayed weights
                                                (~0.2–100) — empirically 0.5 produced score
                                                inflation past 100 when common tokens like
                                                "chair" or "vintage" matched.)

      + Σ min(bias_term.weight, 0.4)           (per matched bias_term cluster; cap the
                                                per-card cluster total at 1.5. bias_term.weight
                                                values are recency-weighted cluster sums that
                                                can be very large; the 0.4 cap and 1.5 ceiling
                                                prevent any one theme from dominating.)

      - 1.0 per negative_term match

      + deal_signal                            (rough heuristic on price vs. title — e.g.
                                                "Steelcase" + low $; cap at +0.5)

      + price_drop_signal                      (when the card displays an `$current$original`
                                                pair and `current ≤ 0.80 * original`, that's
                                                a motivated-seller signal — add +0.3.
                                                Cap at +0.3.)
```

**`url_match_bonus` (recency-weighted + title-gated):**

A static +5.0 for `card.url ∈ bias.seen_listings` was previously inflating the score of one-off curiosity visits (e.g. a "Cinderella gown" the user opened once nine days ago). The new bonus:

- Only applies if the card title also matches at least one entry in `title_vocab` with `weight > 0.5`, OR at least one `bias_terms` cluster. If neither, the URL match is recorded (`url_seen_before: true` stays in the JSON for transparency) but contributes 0 to the score.
- When gated in, the bonus is recency-weighted: `5.0 * exp(-prior_last_visit_age_days / 21.0)`. A visit from yesterday gives ~4.8; from 6 months ago gives ~0.04.

See memory `feedback-selectivity`.

**Apply the quality filter before taking top-N.** Drop cards where any of the following holds:
- `price` is null OR `price == 0` (curb pickup, pricing error, or unparsed).
- `imv_label == "No comps"` AND `confidence == "Low"` (the agent could not meaningfully evaluate — don't occupy a slot).
- Title is empty/whitespace after extraction.

Record the dropped count and the per-reason breakdown — surface it in the report header so the user sees the abstention rate. See memory `feedback-card-quality`.

Then take the **top 50** by score from the remaining set. Configurable downward via `top_n` if a future invocation wants a tighter list.

If `history_available` is false in the bias profile, fall back to pure feed rank + price-vs-title heuristic, and note this in the report header so the user knows the run wasn't history-informed.

Record per-card scoring breadcrumbs so the report can explain *why* each card surfaced:
- `feed_position`, `score`
- `bias_matches`: list of `bias_term.term` strings that matched
- `vocab_matches`: top 5 title tokens by contribution
- `url_seen_before`: bool, with `prior_visit_count` and `prior_last_visit_age_days` if true
- `url_match_bonus_applied`: bool (true only when the gating conditions were met and the bonus contributed to the score). Helpful for debugging "why didn't this seen-before listing rank higher?"
- `blocked_by` (only present in `rest[]`): the block-list pattern that matched, if any

### 6. Thumbnail download for the top 50 (default)

**Do not open detail pages for all 50 listings** — that's ~12 minutes of automation and ~16 MB of downloads. Instead, use the `thumb_url` (FB CDN URL) each card already exposed during the scroll, and `curl` each to local disk. One image per listing, ~30–50 KB. See memory `feedback-top-n-50`.

The `thumb_url` was captured in step 4 from the card's `<img>` element. It's a `scontent-*.xx.fbcdn.net` URL, signed and short-lived (the `oe=` param is the expiry). Download immediately:

```bash
mkdir -p "${REPO_ROOT:-.}/reports/images/feed_${RUN_ID}"
for ENTRY in "${TOP_ENTRIES[@]}"; do
  # ENTRY format: "<rank> <thumb_url>"
  RANK=$(echo "$ENTRY" | cut -d' ' -f1)
  URL=$(echo "$ENTRY" | cut -d' ' -f2-)
  curl -sS \
    -A "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36" \
    -H "Referer: https://www.facebook.com/" \
    --max-time 10 \
    -o "${REPO_ROOT:-.}/reports/images/feed_${RUN_ID}/$(printf '%03d' $RANK).jpg" \
    "$URL"
done
```

After downloads:
- Verify each file is ≥ 4 KB (anything smaller is likely a redirect or error response — flag, do not crash).
- Skip card thumbs that returned the FB UI overlay PNG (size + identical md5 across listings → suspect).
- If a thumb_url is missing on a card (rare; some listings don't expose an `<img>` in the feed card), the report renders the card without a hero image rather than skipping the listing.

#### Optional: featured deep extraction (top 3–5 only)

If the user explicitly asks for "deeper images" or a "featured" subset, run the previous v0.4.0 detail-page extraction flow against the top 3–5 by score. That flow opens each detail page, clicks the hero to expand, scrapes every `scontent.fbcdn.net` URL with `naturalWidth >= 300`, and downloads up to 6 images each to `reports/images/feed_<run_id>_<rank>/00..05.jpg`. The report can then render those listings as multi-image galleries while the rest use single-thumbnail cards.

Default behavior: **single-thumbnail per card across all 50** — no detail-page opens, uniform card layout.

```bash
browser-harness <<'PY'
ensure_real_tab()
LISTING_URL = "https://www.facebook.com/marketplace/item/.../"
RANK = 1
RUN_ID = "20260519-1042"

new_tab(LISTING_URL)
wait(4)

state = js("""
  (() => {
    const text = document.body.innerText || '';
    const url = location.href;
    return {
      is_item: /\\/marketplace\\/item\\//i.test(url),
      logged_out: /\\/login|Log in|Email address or phone number/i.test(url + ' ' + text),
      checkpoint: /checkpoint|two-factor|security check/i.test(url + ' ' + text),
      unavailable: /listing is no longer available|listing isn't available|this item is sold|marked as sold|no longer for sale|item is pending/i.test(text),
      title: document.querySelector('h1')?.innerText || null
    };
  })()
""")
if not state.get("is_item") or state.get("logged_out") or state.get("checkpoint") or state.get("unavailable"):
    print("ABORT", state)
else:
    # Some listings reveal additional images only after a click on the hero
    # (opens a lightbox or expands the carousel). One click is enough; no retry loop.
    js("""
      (() => {
        const imgs = Array.from(document.querySelectorAll('img'))
          .filter(i => /scontent[\\w-]*\\.xx\\.fbcdn\\.net/.test(i.currentSrc || i.src))
          .filter(i => i.naturalWidth >= 300 && i.naturalHeight >= 300)
          .sort((a,b) => (b.naturalWidth*b.naturalHeight) - (a.naturalWidth*a.naturalHeight));
        const hero = imgs[0];
        if (!hero) return;
        const clickTarget = hero.closest('[role="button"], [tabindex]') || hero;
        clickTarget.click();
      })()
    """)
    wait(1.5)
    # After the click, the lightbox or carousel may have rendered additional
    # high-res variants. Pull them all now.
    image_urls = js("""
      (() => {
        const urls = new Set();
        for (const img of document.querySelectorAll('img')) {
          const src = img.currentSrc || img.src || '';
          if (!/scontent[\\w-]*\\.xx\\.fbcdn\\.net/.test(src)) continue;
          if (img.naturalWidth < 300 || img.naturalHeight < 300) continue;
          // Skip the FB UI overlay PNG (identical across all listings)
          if (/\\/m1\\/v\\/t0\\.65075-6\\//.test(src)) continue;
          urls.add(src);
        }
        return Array.from(urls).slice(0, 8);
      })()
    """)
    print({ "rank": RANK, "title": state["title"], "image_urls": image_urls })

js("window.close()")
wait(0.5)
PY
```

The heredoc emits a JSON-shaped line with the image URLs. Pipe that out, parse it, then download each URL with `curl` to a per-rank directory:

```bash
mkdir -p "${REPO_ROOT:-.}/reports/images/feed_${RUN_ID}_${RANK}"
for IDX in $(seq 0 $((${#URLS[@]} - 1))); do
  URL="${URLS[$IDX]}"
  curl -sS \
    -A "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36" \
    -H "Referer: https://www.facebook.com/" \
    --max-time 15 \
    -o "${REPO_ROOT:-.}/reports/images/feed_${RUN_ID}_${RANK}/$(printf '%02d' $IDX).jpg" \
    "$URL"
done
```

**Important — these CDN URLs are signed and short-lived.** The `?oh=...&oe=<hex>` parameters carry an expiry timestamp (typically hours-to-days out). The report **must** reference the downloaded local files, never the remote URLs, or it will silently break after a day or two.

Save layout:
```
reports/images/feed_<run_id>_<rank>/00.jpg
reports/images/feed_<run_id>_<rank>/01.jpg
reports/images/feed_<run_id>_<rank>/02.jpg
...
```

Cap per-listing image count at 6. The first downloaded image (`00.jpg`) is the hero; the rest are thumbs in the gallery. The HTML report references these by **relative path** from `reports/`.

If extraction yields zero usable URLs (rare — usually means the listing has no images at all), fall back to the listing thumbnail URL captured in step 3. Do not screenshot the page.

### 6.5. Deal assessment (per top-N card)

For each of the top 50, produce the six price-analysis fields documented in memory `project-price-analysis`. The agent estimates these from training-data knowledge of retail prices, brand depreciation, and condition norms — this is approximation, not a queryable comp pipeline.

**Required fields per card:**

| Field | How to estimate |
|---|---|
| `comp_median_90d` | Best estimate of the 90-day median sold price for a condition-matched listing on eBay or peer marketplaces. Use brand + model + size cues from the title. `null` if the title is too vague. |
| `imv_delta_pct` | `round((asking − comp_median_90d) / comp_median_90d × 100)`. `null` if `comp_median_90d` is `null`. |
| `imv_label` | Map `imv_delta_pct` to one of `Great deal` / `Good deal` / `Fair` / `High` / `Overpriced` / `No comps`. See the bands in the report-generator skill. |
| `sell_through_rate` | Rough STR estimate for the category (active demand). For volume electronics: 40–70%. For niche/specialty: 10–30%. For furniture in non-trendy regions: 15–35%. Round to nearest 5%. |
| `condition_multiplier` | Map verbal condition in the title/listing to a multiplier: Like New 1.0, Good 0.85, Fair 0.65, Parts 0.30. Default 0.85 (Good) if unstated. |
| `adjusted_floor` | `round(comp_median_90d * condition_multiplier)`. The price the listing should be approaching. |
| `depreciation_anchor` | `round(retail_msrp * (dep_rate ** age_years))`. Premium ergonomic furniture: dep_rate 0.86 (≈50% retained at 5yr); commodity furniture: 0.70; electronics yr1+: 0.75; vintage/MCM: appreciation possible — set to `null` or to comp median. |
| `dep_years` | Estimated item age in years. Use date cues in the title ("2024", "vintage 1970s") or default to 3 for modern goods, 30+ for vintage. |
| `trust_signal_score` | Count verifiable signals in the listing title/snippet (max 5): receipt, multi-angle photos of mechanism, "tested" or "working", warranty/return policy, no-smoke/pet. |
| `trust_signals_present` / `trust_signals_missing` | Two arrays summing to ≤ 5 entries. |

**Be honest about uncertainty.** When title is vague (e.g. "Office Chair", "Brown couch"), set `comp_median_90d: null`, `imv_label: "No comps"`, `confidence: "Low"`, and admit it in the `reason`. Do not fabricate brand or model.

**Use category-level fallback comps before giving up.** When the title doesn't name a brand/model but DOES name a recognizable category (e.g. "Mid-century teak sideboard", "Outdoor sectional", "Standing desk"), produce a category-level comp range and set `confidence: "Medium"` — NOT "Low". Reserving "Low" + "No comps" for genuinely opaque titles ("Stuff", "$0 listing", "Free pickup") prevents the quality filter from dropping 70%+ of an honest feed. A v0.7.0 first pass dropped 78/100 cards before this fallback was added; with category-level comps it dropped 38/100, which is the right rate.

### 7. Structured output

Emit a structured array the downstream stages can consume. The JSON keeps **all** captured cards (up to 80) for traceability; the top 50 each have a single `image_path` referencing the downloaded thumbnail:

```json
{
  "run_id": "20260519-1142",
  "captured_at": "2026-05-19T11:42:00-04:00",
  "source": "marketplace_browse_all_feed",
  "top_n": 50,
  "viewport_count": 12,
  "bias_profile_path": "reports/bias_20260519-1142.json",
  "history_available": true,
  "listings_seen": 78,
  "marketplace_items_in_history": 438,
  "top": [
    {
      "rank": 1,
      "url": "https://www.facebook.com/marketplace/item/2051040935507757/",
      "title": "IKEA HOVET Mirror",
      "price": 85,
      "location": "Greensboro, NC",
      "feed_position": 4,
      "score": 9.4,
      "bias_matches": ["ikea hovet"],
      "vocab_matches": [["hovet", 1.0], ["ikea", 0.9], ["mirror", 0.4]],
      "url_seen_before": true,
      "prior_visit_count": 4,
      "prior_last_visit_age_days": 2.3,
      "thumb_url": "https://scontent-iad3-1.xx.fbcdn.net/...",
      "image_path": "images/feed_20260519-1142/001.jpg",

      "comp_median_90d": 330,
      "imv_delta_pct": -3,
      "imv_label": "Fair",
      "sell_through_rate": 45,
      "condition_multiplier": 0.85,
      "condition_label": "Good",
      "adjusted_floor": 280,
      "depreciation_anchor": 650,
      "dep_years": 5,
      "trust_signal_score": 1,
      "trust_signals_present": ["good condition stated"],
      "trust_signals_missing": ["original receipt", "mechanism photos", "tested/working", "warranty", "smoke/pet disclosure"],

      "offer_ladder": { "opening": 250, "likely": 280, "hard_stop": 310 },
      "reason": "Comp median around $330 for used-good Leap V2; asking $320 sits within the Fair band. Low trust signal in description.",
      "confidence": "Medium"
    }
  ],
  "rest": [
    { "rank": null, "url": "...", "title": "...", "price": 50, "location": "...",
      "feed_position": 60, "score": 0.4, "bias_matches": [], "thumb_url": "..." }
  ]
}
```

Notes:
- `top[]` length = `top_n` (default 50). Each entry has a single `image_path` (the downloaded feed thumbnail), not a multi-image `images[]` gallery. That gallery shape is reserved for the optional featured deep-extraction subset.
- `rest[]` holds the remaining captured cards (no downloaded image, just `thumb_url` retained for reference). Drop entries beyond rank 80 — they were past the scroll cap.

Write this to `reports/feed_<run_id>.json`. The report generator reads `top[]` for the visible cards and surfaces `marketplace_items_in_history` + `listings_seen` + the count of `rest[]` as context in the report header.

### 8. Hand-off

State explicitly which files were produced, how many listings were seen, how many made the top 3, and whether history bias was available. The report generator picks it up from there.

## Output Contract

This skill returns:
- A bias profile at `reports/bias_<run_id>.json` with full `seen_listings`, `seen_searches`, `recurring_domains`, `title_vocab`, and the human-readable `bias_terms` summary — each entry recency-weighted (or a note that history was unavailable).
- A scored feed JSON at `reports/feed_<run_id>.json` matching the schema above.
- A single image directory at `reports/images/feed_<run_id>/` containing up to 50 downloaded thumbnails named `001.jpg`, `002.jpg`, …, `050.jpg`.
- A one-line console summary: items in history, cards seen, top-N picked, run_id.

## Approval Policy

This stage is read-only. No approval is required to scroll the feed and capture cards. Approval gates apply only at the seller-communication stage.

## Anti-patterns

- **Don't fall back to topic search** if the feed looks sparse. Sparse algorithmic results are a real signal; surface them as "low-yield run" rather than papering over them with a query.
- **Don't filter cards client-side before scoring.** Capture all visible cards in step 3; bias scoring (step 5) decides which 3 advance to detail capture.
- **Don't reuse a previous run's `run_id`.** Each invocation gets a fresh timestamped run, so deltas across runs stay legible.
- **Don't write a `generate_feed_scroll.py`** or any Python orchestrator. The agent drives `browser-harness` directly through ephemeral Bash heredocs.
- **Don't screenshot anything for the report.** Product images come from downloading `scontent.fbcdn.net` URLs the detail page exposes, never from `screenshot()` on the viewport. See memory `feedback-listing-images`.
- **Don't embed remote FB CDN URLs in the saved HTML.** They expire (the `oe=` parameter is the expiry timestamp). Always download to local disk and reference by relative path.
- **Don't keep the listing tab open** after capture. `js("window.close()")` after each detail screenshot — the user shouldn't end up with three orphan Marketplace tabs.
- **Don't message sellers.** Step 6 opens detail pages strictly for image capture; never click "Message" or open the composer.

## Pitfalls

- Facebook's CDN image URLs are signed and short-lived; capture screenshots in the same pass, don't rely on `thumb_url` being valid an hour later.
- The feed re-shuffles between sessions; don't expect deterministic results across runs.
- Scrolling too fast can cause cards to be virtualized out of the DOM before capture — pace the scroll with explicit waits.
- Login redirects are silent: a `marketplace/` URL can land on a login wall without changing the URL bar. Verify a card is present before declaring the page ready.
- **`ensure_real_tab()` is not enough** when the user already has Marketplace-domain tabs open (e.g. a previous report). After `new_tab(url)`, capture the new target's id (via `list_tabs()` and compare to the pre-call snapshot) and explicitly `switch_tab(target_id)` before running JS against it. Otherwise the next `js(...)` call may execute against the old report tab and you'll get DOM from the wrong page. **Note:** `list_tabs()` returns entries keyed as `targetId` (not `id`); using the wrong key is a `KeyError`-by-design.
- **Viewport resize for deterministic screenshots.** The harness has no `resize_page()` helper. Use `cdp("Emulation.setDeviceMetricsOverride", {width: 1440, height: 900, deviceScaleFactor: 1, mobile: false})` — but the override gets **cleared between heredoc invocations**, so it must be re-applied inside the same heredoc that takes the screenshot.
- **The `h1` element on a Marketplace detail page is not the listing title.** It's usually "Chats" or another navigation label. Use the URL pattern (`/marketplace/item/`) for validation; do not assert title via `h1`.
- **Skip these CDN paths when extracting images** — they're UI overlays or auth-required carousel previews, not the product photos:
  - `m1/v/t0.65075-6/An_DmLLt…` — generic FB UI overlay PNG, identical across all listings (~800×800).
  - `t45.5328-4/…` — carousel previews that often return a ~22-byte "URL signature mismatch" error body outside a real session. They occasionally work, so don't hard-skip; the ≥8 KB post-download size check naturally filters the bad ones.
- **Title extractor: handle `$current$original` price pairs.** Some feed cards show a price drop as `"$300$450"` on the first text line with no human-readable title there — the actual title lives on a later line. The extractor must skip lines that match `/^\$[\d,]+\$[\d,]+/` and pick the next non-price line as the title. The two prices are useful: capture them as `price` (current) and `original_price` so the scoring `price_drop_signal` heuristic can fire.
- **Calibration caveat on `comp_median_90d`.** The Terapeak/eBay methodology assumes shipping-included comps. FB Marketplace is mostly local pickup, so FB prices tend to run 10–20% below eBay comps for similar condition. When estimating `comp_median_90d`, anchor it to **FB Marketplace** sold ranges where the agent can — not raw eBay. Otherwise the "Great deal" share of the top 50 inflates artificially because comps are too high.
- Clicking the hero image sometimes opens a full-screen lightbox; other times it just enlarges in place. Either is fine — the screenshot captures whatever state the click produced. Do not try to detect lightbox vs. enlarge and branch on it; the heuristic is "one click attempt, then shoot."
- If a listing was deleted between the scroll and the detail-page open, the page will say "Listing isn't available" — log the failure, drop that rank, and promote rank 4 (or rank 5) into the top 3 so the report still has 3 cards.
- Keep the "unavailable" regex narrow. Broad patterns like `/sold/` will match seller copy such as "sold as a set" or "sold individually" on live listings, costing you a wasted tab. The regex in this skill requires strong phrasing (`listing is no longer available`, `this item is sold`, `marked as sold`, etc.) so live listings don't false-trip.

## Verification

Before finishing, verify:
- A bias profile JSON exists at `reports/bias_<run_id>.json` with `seen_listings` populated and each entry carrying `recency_weight` + `last_visit_age_days` (or the report header notes "history unavailable").
- The bias profile is sorted by `recency_weight` desc, not raw `visit_count` — spot-check that the top entry has the smallest `last_visit_age_days`.
- The number of distinct marketplace items in `seen_listings` is in the ballpark of what `sqlite3 SELECT COUNT(*)` returns for the same window — if your bias profile says "12 items seen" but the History DB has 400, the extraction is broken; widen and re-pull.
- A feed JSON exists at `reports/feed_<run_id>.json` with `top` of length `top_n` (default 50) and each top entry has a non-null `image_path`.
- The `image_path` files exist on disk in `reports/images/feed_<run_id>/` and are non-empty JPEGs (≥ 4 KB each for thumbnails — smaller indicates a redirect or error body).
- The downloaded thumbnails are visually distinct across listings — spot-check by md5'ing rank 1's, rank 25's, and rank 50's images.
- No detail page was opened, no message composer surfaced, no tabs left open.
- The user is still logged in (Marketplace still renders account-specific surfaces).
