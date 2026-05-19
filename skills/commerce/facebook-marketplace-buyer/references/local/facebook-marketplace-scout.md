---
name: facebook-marketplace-scout
description: USE WHEN you want the agent to search Facebook Marketplace from your logged-in browser, compare listings, benchmark price and condition, capture fresh screenshots of promising listings, and produce a ranked shortlist with links and notes. The scout always validates current user interest and captures visual evidence before finishing.
version: 1.2.0
author: velinussage
prerequisites:
  commands: [browser-harness, python3]
metadata:
  hermes:
    tags: [shopping, facebook, marketplace, browser-automation, scouting, pricing, chrome-history, screenshots]
    related_skills: [facebook-marketplace-buyer, facebook-marketplace-watch-notifier, facebook-marketplace-deal-assessor, facebook-marketplace-report-generator]
    requires_toolsets: [terminal]
---

# Facebook Marketplace Scout (Improved)

Use this skill to run a high-quality, evidence-based Marketplace scouting workflow.

The purpose is to turn a shopping goal into a ranked shortlist with:
- Accurate titles and pricing
- Fresh screenshots of promising listings
- Deal quality reasoning
- Links and visual evidence for reporting

## When to Use

Use this skill when:
- You want a proper research-grade shortlist (not just raw search results)
- You want screenshots captured for the final report
- You want current user interest validated before searching

## Core Rules

1. Always validate current interest first (never reuse old interests like “varier chair”).
2. Capture fresh screenshots of the top promising listings.
3. Improve title and price extraction using better selectors.
4. Prepare data for cross-location comparison in the report.

## Procedure

### 1. Validate the browser path

Verify browser-harness is attached and the user is logged into Facebook.

### 2. Validate current interest before searching

Check recent browser history or ask the user to confirm the current product family, budget, brands, and condition preferences.

Never silently use stale interests.

### 3. Search and extract listings

Use improved selectors for better title and price parsing:

- Look for links containing `/marketplace/item/`
- Extract title from nearby text or alt attributes
- Extract price using currency patterns near the title

Capture for each listing:
- Title (improved parsing)
- Price
- Location
- Listing URL
- Image URL (if available)

### 4. Rank the shortlist

Compare against:
- Local used comps
- New retail price anchors
- Brand/model quality
- Condition signals

### 5. Capture fresh screenshots (New)

After ranking, capture screenshots of the top 3–5 listings:

- Open each promising listing URL
- Scroll to the main content area
- Take a clean screenshot
- Save to `reports/screenshots/listing_[rank].png`

These screenshots will be used by the report generator.

### 6. Prepare data for report generation

Output structured data including:
- Improved titles and prices
- Screenshot paths
- Deal reasoning
- Suggested offer strategy

This data can be fed directly into `facebook-marketplace-report-generator`.

## Screenshot Capture Rule

Every time this scout runs and identifies promising listings, fresh screenshots **must** be captured. The report generator should never rely on old screenshots.

## Verification

Before finishing, verify:
- Current interest was explicitly validated
- At least 3–5 fresh screenshots were captured
- Titles and prices were parsed with improved selectors
- Data is structured for the report generator

This version ensures the scout produces high-quality, visual, and research-ready output.