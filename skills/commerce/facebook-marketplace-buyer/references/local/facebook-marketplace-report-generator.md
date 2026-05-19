---
name: facebook-marketplace-report-generator
description: USE WHEN you want to turn scout, feed-scroll, or deal-assessment output into a clean, self-contained, bookmarkable HTML report for offline review. The agent authors the HTML directly with Write/Edit — no Python templating, no generator scripts. Produces ranked shortlist, deal quality labels, offer ladders, red flags, and recommended next actions. DOES NOT contact sellers.
version: 2.5.0
author: velinussage
prerequisites:
  agent:
    - Write / Edit tools available
    - Access to the captured JSON + screenshot directory from a prior scout / feed-scroll run
metadata:
  hermes:
    tags: [shopping, facebook, marketplace, reporting, html, deal-analysis, agent-authored]
    related_skills:
      - facebook-marketplace-buyer
      - facebook-marketplace-feed-scroll
      - facebook-marketplace-scout
      - facebook-marketplace-deal-assessor
    requires_toolsets: [filesystem]
---

# Facebook Marketplace Report Generator

Generates a self-contained Facebook-themed HTML report from Marketplace feed-scroll or scout data. The report renders in any modern browser without a build step.

## Core Principle: Agent-Authored, Not Templated

**Write the HTML directly.** Do not create or persist a `generate_*.py`, a Jinja template, or any other generator script. The Claude agent reads the captured JSON, looks at the screenshots, and writes one HTML file using the `Write` tool.

This is non-negotiable for this skill library — see memory `feedback-reports-html` and `project-scout-vision`.

The pattern follows Simon Willison's single-file-HTML-tool convention: CDN dependencies only (Tailwind), inline `<style>` and `<script>`, relative image paths, no React/Vite/Parcel toolchain. Theme constraints (Facebook visual language) are locked into CSS custom properties at the top of the `<style>` block so the agent doesn't drift toward generic AI-slop on re-runs.

## When to Use

Use this skill when:
- A feed-scroll or scout run has produced a JSON listings file and per-card screenshots, and you want a reviewable artifact.
- You want a single bookmarkable file the user can keep open in a tab.

## Don't Use When

- You still need to collect Marketplace data → use `facebook-marketplace-feed-scroll` (Stage 0) or `facebook-marketplace-scout` (Stage 1) first.
- The user wants real-time seller messaging → that's Stage 4.

## Input Contract

Read from a structured JSON file produced by the upstream stage. Schemas:

### From feed-scroll (Stage 0, v0.4.0+)
```json
{
  "run_id": "20260519-1042",
  "captured_at": "...",
  "source": "marketplace_browse_all_feed",
  "bias_profile_path": "reports/bias_20260519-1042.json",
  "history_available": true,
  "marketplace_items_in_history": 438,
  "listings_seen": 23,
  "top": [
    { "rank": 1, "url": "...", "title": "...", "price": 85,
      "location": "Greensboro, NC",
      "feed_position": 4, "score": 9.4,
      "bias_matches": ["ikea hovet"],
      "vocab_matches": [["hovet", 1.0]],
      "url_seen_before": true, "prior_visit_count": 4,
      "images": [
        "images/feed_20260519-1042_1/00.jpg",
        "images/feed_20260519-1042_1/01.jpg",
        "images/feed_20260519-1042_1/02.jpg"
      ]
    }
  ],
  "rest": [ ... ]
}
```

Read the bias profile from `bias_profile_path` for the "Why these three" explainer.

### From scout / deal-assessor (Stages 1–3)
Adds `deal_label` (alias for `deal_tone`), `confidence`, `reason`, `offer_ladder`, `new_price_anchor`, `red_flags`, `comparison`, `recommendation`.

If the input is feed-scroll-only (no scoring yet), call the deal-assessor on each card before generating the report.

## Procedure

1. Read the input JSON.
2. Verify every `screenshot_path` exists. If any are missing, surface the gap; do not silently render broken `<img>` tags.
3. Decide on the output path:
   - Default: `reports/scout_report_<run_id>.html`
   - If overwriting the rolling current view: `reports/current_scout_report.html`
4. Author the HTML by `Write`-ing the file directly. Use the structural skeleton below.
5. State the absolute path of the generated file.

## HTML Skeleton

The agent should write something shaped like this. Adapt freely — the skeleton is a starting point, not a template:

```html
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Marketplace Scout Report</title>
<script src="https://cdn.tailwindcss.com"></script>
<style>
  :root {
    --fb-blue: #1877F2;
    --fb-blue-hover: #166FE5;
    --fb-surface: #F0F2F5;
    --fb-card: #FFFFFF;
    --fb-text: #050505;
    --fb-text-muted: #65676B;
    --fb-border: #E4E6EB;
  }
  html, body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI",
                 "Helvetica Neue", Helvetica, Arial, sans-serif;
    background: var(--fb-surface);
    color: var(--fb-text);
  }
  .fb-shadow { box-shadow: 0 1px 2px rgba(0,0,0,0.10), 0 1px 4px rgba(0,0,0,0.08); }
</style>
</head>
<body>
  <header class="bg-[var(--fb-blue)] text-white">
    <!-- FB-style top bar with the f-logo and a "Marketplace Scout" wordmark -->
  </header>
  <main class="max-w-5xl mx-auto px-4 py-6">
    <!-- Summary card: counts of strong/fair/weak deals, total reviewed -->
    <!-- One <article> per listing:
         - Image gallery (main + thumbs) on the left
         - Title, location, price on the top right
         - Deal-label pill, confidence pill
         - Reason paragraph
         - Two-col grid: Offer Ladder | Anchor & Comparison
         - Recommendation footer with FB-blue clock icon
         - "Open on Marketplace ↗" link colored FB blue
    -->
  </main>
</body>
</html>
```

## Theme Constraints (Facebook Visual Language)

- **Primary:** FB blue `#1877F2` for header, links, primary buttons.
- **Surface:** `#F0F2F5` page background, `#FFFFFF` cards.
- **Text:** `#050505` primary, `#65676B` muted.
- **Border:** `#E4E6EB` ring on cards.
- **Type:** system sans (Segoe UI on Windows, San Francisco on macOS) — no Google fonts, no Inter.
- **Radius:** `rounded-xl` on cards, `rounded-md` on buttons, `rounded-full` on pills.
- **Shadow:** subtle two-layer (`0 1px 2px / 0 1px 4px`).
- **Deal-tone palette:** emerald for strong, amber for fair, rose for weak/skip.

## Image Handling

- Reference images by **relative path** from the HTML file. The feed-scroll v0.5.0+ convention is `images/feed_<run_id>/001.jpg`, `002.jpg`, … `050.jpg` — one thumbnail per ranked listing.
- These files are **downloaded copies of FB feed-card CDN thumbnails** (no FB chrome, natural aspect ratios). Do not screenshot the viewport for the report. See memory `feedback-listing-images`.
- Use a CSS `aspect-square` (or 4:5) container with `object-cover` on each `<img>`. The aspect ratio container keeps the layout uniform across listings whose photos vary.
- Do **not** inline images as base64. Files stay on disk; the HTML links to them.
- Do **not** reference remote `scontent.fbcdn.net` URLs in the saved HTML — they expire (the `oe=` param is the expiry timestamp).

## Price-Analysis Card (default, top-N = 50) — redesigned in v2.5.0

The card was redesigned after user feedback (see memory `feedback-card-quality`): too much chip-noise, too compressed, weak CTA. The new card de-emphasizes per-card bias chips, foregrounds price comparison + offer ladder, and uses a real button for the marketplace CTA.

### Layout

```
┌────────────┬──────────────────────────────────────────────────────┐
│            │ #N  Title (2-line clamp)                       $XXX │
│  THUMB     │ Location · feed pos · score                  $YYY −Z%│
│ 140px sq   │                                                       │
│ object-    │ ╔══════════════╗   Medium conf   seen 3d ago         │
│ cover      │ ║  IMV  −12%   ║                                      │
│ rounded-md │ ║  Great deal  ║                                      │
│            │ ╚══════════════╝                                      │
│            ├──────────────────────────────────────────────────────┤
│            │ Comp median $330 · Floor $280 (Good 0.85×)            │
│            │ Retail anchor $650 · Trust 1/5                        │
│            ├──────────────────────────────────────────────────────┤
│            │ ┌────────┐  ┌────────┐  ┌────────┐                    │
│            │ │ Open   │  │ Likely │  │  Walk  │                    │
│            │ │ $250   │  │ $280   │  │  $310  │                    │
│            │ └────────┘  └────────┘  └────────┘                    │
│            ├──────────────────────────────────────────────────────┤
│            │ 1–2 line reason                                       │
│            │                                                       │
│            │                        [ Open on Marketplace ↗ ]    ←│
└────────────┴──────────────────────────────────────────────────────┘
```

- **Left:** 140 px square thumbnail (was 120; bumped for legibility), `object-cover`, `rounded-md`. If missing, muted placeholder. Each `<img>` has `loading="lazy"` since the report has 50 cards.
- **Right top:** rank number prefix `#N` (small, gray), title (2-line clamp, `text-[15px] font-semibold`). Asking price `text-2xl font-bold tabular-nums` on the right. **If `original_price` is present**, render it as `<span class="text-sm text-[#65676B] line-through tabular-nums ml-2">$YYY</span>` followed by the saving percentage `<span class="text-xs font-semibold text-emerald-700 ml-1">−Z%</span>`.
- **Meta line:** `Location · feed pos · score` (`text-xs text-[#65676B]`).
- **IMV Verdict block** (visual headline): colored band, ~100×70 px, showing `imv_delta_pct` as large signed % and the deal-label name (see "IMV Delta bands" below). To its right: confidence pill (Low/Medium/High) and `seen before · N days ago` badge if relevant. **No bias-match chip row** — those tags add noise per the user's feedback.
- **Price-analysis grid** (two short rows, `text-[13px]`):
  - Row 1: `Comp median ${comp_median_90d} · Floor ${adjusted_floor} ({condition_label} {condition_multiplier}×)`
  - Row 2: `Retail anchor ${depreciation_anchor} · Trust {trust_signal_score}/5`
  - Drop the per-card `STR` line — it's a sourcing signal not a buying signal; keep in the JSON but don't render.
- **Offer ladder** — three labeled cells in a row (`grid grid-cols-3 gap-2`), each a small `rounded-md` block with the label `text-[10px] uppercase text-[#65676B]` on top and the price `text-base font-bold tabular-nums` below. Open / Likely / Walk.
- **Reason:** 1–2 lines, `text-[13px] text-[#050505]/85`.
- **Footer button (right-aligned):** the marketplace CTA is now a real button:
  ```html
  <a href="{url}" target="_blank" rel="noopener"
     class="inline-flex items-center gap-1.5 px-4 py-2 rounded-md
            bg-[#1877F2] hover:bg-[#166FE5] text-white text-sm font-semibold
            shadow-sm transition">
    Open on Marketplace
    <svg class="size-3.5" viewBox="0 0 20 20" fill="currentColor">
      <path d="M11 3a1 1 0 100 2h2.586l-7.293 7.293a1 1 0 101.414 1.414L15 6.414V9a1 1 0 102 0V4a1 1 0 00-1-1h-5z"/>
      <path d="M5 5a2 2 0 00-2 2v8a2 2 0 002 2h8a2 2 0 002-2v-3a1 1 0 10-2 0v3H5V7h3a1 1 0 000-2H5z"/>
    </svg>
  </a>
  ```

50 cards in single-column on narrow, `lg:grid-cols-2` on wide. Card height ~240–290 px (slightly taller than v2.4 because the offer ladder is now 3 cells and the CTA is a button).

### IMV Delta bands (color + label)

| Range | Label | Background | Text color |
|---|---|---|---|
| `≤ −10%` | Great deal | `#DCFCE7` emerald-50 | `#15803D` emerald-700 |
| `−10% < d ≤ −5%` | Good deal | `#CCFBF1` teal-50 | `#0F766E` teal-700 |
| `−5% < d < +5%` | Fair | `#FEF3C7` amber-50 | `#92400E` amber-700 |
| `+5% ≤ d < +10%` | High | `#FFEDD5` orange-50 | `#9A3412` orange-700 |
| `≥ +10%` | Overpriced | `#FEE2E2` rose-50 | `#B91C1C` rose-700 |
| `null` (insufficient data) | No comps | `#F3F4F6` gray-100 | `#374151` gray-700 |

The IMV block is the visual headline — make it prominent (~80×64 px) so a 50-card scroll lets the user spot Greats and Overprices by color alone.

### When data is thin

If the agent couldn't estimate `comp_median_90d` (no recognizable brand/model, vague title), render the IMV block as "No comps" and fill the price-analysis strip with "—" for the missing fields. The card still shows; it just admits its limits. Do not fabricate specifics.

## Featured Deep-Dive Section (optional)

If the feed JSON's top entries carry the older multi-image `images[]` array (from the featured deep-extraction subset), render those as full-width gallery cards at the top of the listings section before the compact 50. Each featured card uses the v0.4.0 hero+thumbs gallery pattern (hero `<img>` with `id="hero-{rank}"`, thumb row that swaps the hero on click via a delegated handler).

Default behavior — when the user didn't ask for a featured subset — is **no featured section, all 50 cards uniform compact**.

## "Why these top picks" Header

For the top-N broad survey, the header explainer is:

> "Top {top_n} re-ranked from {listings_seen} feed cards using your recent browsing. **{marketplace_items_in_history}** Marketplace items viewed in the last {lookback_days} days. Recent themes: {top 5 `bias_terms.term` joined by ' · '} (each shown with last-visit age)."

## "Why these three" Header

After the summary stats and before the listings, add a small explainer that surfaces the bias signal:

- If `history_available: true`:
  > "Re-ranked using your recent browsing — **{marketplace_items_in_history}** Marketplace items viewed in the last 180 days. Strongest themes: {top 5 `bias_terms.term` joined by ' · '}."
- If `history_available: false`:
  > "History unavailable — ranked by feed position and price/brand heuristic only."

For each card, surface its `bias_matches` and `url_seen_before` as small chips below the title (e.g. "match: kneeling chair", "seen before · 4 prior visits"). This makes the bias mechanism transparent.

## "Previously viewed" Section (required)

Render a "Previously viewed" section near the bottom of the report — after the rest-of-feed table, before the footer. This section shows the user the breadth of intent the bias profile was built from, so the bias mechanism stays inspectable.

Read from the bias profile JSON (`bias_profile_path` from the feed JSON). The section has three blocks in a `grid lg:grid-cols-3` layout:

1. **Top viewed Marketplace listings (spans 2 cols).** A scrollable table (`max-h-[22rem]`) of the top 30 entries from `seen_listings`, ordered by `visit_count` desc. Each row: a tone-coded visit pill (≥5×: rose, ≥3×: amber, ≥1×: gray), then the cleaned title as an FB-blue link to the listing URL.
   - **Title cleanup is required.** Chrome stores titles like `"🟢 (3) Marketplace - Lg c5 Oled Tv | Facebook"`. Strip the green-circle emoji, the leading `(N) ` visit-number, the `Marketplace - ` prefix, and the ` | Facebook` suffix. Fall back to `"(untitled listing)"` if the result is empty.
   - Caption below: `"Showing top 30 of N unique listings, ordered by visit count."`

2. **Top Marketplace searches.** Top 10 `seen_searches` entries as inline chips: query text + small `N×` count. Use the existing `chip` / `chip-num` styling.

3. **Recurring research domains.** Top 10 `recurring_domains` entries as inline chips, same chip styling.

Header copy:
> "What the bias profile was built from — your last {lookback_days} days of Chrome activity. **{marketplace_items_seen}** Marketplace items · **{marketplace_searches_seen}** Marketplace searches · **{N}** recurring research domains."

If `history_available: false`, render the section as a single muted card saying "Chrome history was not available for this run — bias signal is neutral. To enable history-informed ranking, ensure the Chrome `History` SQLite DB is readable."

### Why this section exists

The bias profile drives every rank in the report. If the user can't see the underlying `seen_listings` / `seen_searches` / `recurring_domains` data, the ranking is opaque and they can't tell whether the bias is actually capturing their real intent. The section is the transparency layer — it surfaces 30+ concrete data points the user can scan to verify their browsing patterns are being read correctly.

See memory `feedback-history-thoroughness` for why thoroughness (not summary) matters.

## Output

- A single `.html` file rendering cleanly in any browser.
- Tailwind via CDN; all custom CSS inline in `<style>`; all JS inline in `<script>`.
- No external dependencies after generation other than the screenshot files in the relative path.

## Pitfalls

- **Don't templatize this.** If you find yourself wanting to write a `for` loop in Python, you're on the wrong path. Either expand the loop inline in HTML or use the `Edit` tool to append cards one at a time.
- **Don't generate against missing data.** If the input JSON's `recommendation` or `offer_ladder` is empty, route back through the deal-assessor first.
- **Don't overstate deal quality.** Pills are computed from the deal-assessor's label, not editorialized.
- **Don't auto-imply seller contact.** "Open on Marketplace" is a link to the listing page, not a draft-message action.

## Verification

Before finishing:
- The HTML file was written and is non-empty.
- Every `<img src>` resolves to a file that exists on disk.
- No `<form>` or `<button>` performs any kind of network action.
- "Requires explicit approval" language is preserved for any seller-facing next steps that are mentioned.
- Open the file in the browser (or via chrome-devtools MCP) and take a screenshot to confirm the layout renders as expected before declaring done.
