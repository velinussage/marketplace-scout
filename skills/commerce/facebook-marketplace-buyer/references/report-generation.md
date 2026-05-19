# Marketplace Report Generation Patterns

This document captures the evolved approach for generating high-quality, reviewable Marketplace reports as part of the buyer workflow.

## Core Principles

- **Fresh visual evidence**: Screenshots must be recaptured on every scout and report execution. Never reuse stale images.
- **Agent judgment, not just data**: The report must include deal quality assessment, price comparisons (local + retail + cross-location), red flags, offer strategy, and clear recommendations.
- **Real Marketplace data**: Titles, prices, and images should reflect actual scraped listings. Avoid generic placeholders when possible.
- **Cross-location context**: Include price ranges from multiple cities/radii to show where the best value currently exists.

## Required Sections in a Good Report

1. **Executive Summary** — Quick view of opportunities and best value location.
2. **Cross-Location Price Comparison** — Table showing asking prices across nearby metros / radii relevant to the user (e.g., 4–5 surrounding cities at progressively wider radii).
3. **Retail Benchmarks** — New retail price anchors for each model.
4. **Detailed Listing Cards** — Each with:
   - Screenshot (fresh)
   - Deal quality label + confidence
   - Reasoning
   - Offer strategy
   - Recommendation
   - Direct Marketplace link

## Workflow Rules

- The scout skill should trigger screenshot capture for promising listings before handing off to the report generator.
- The report generator must always use the latest screenshots from the current run.
- Title extraction should prioritize model names and key attributes over generic terms like "Office Chair".
- When the user requests richer analysis (deal details, comparisons, cross-location), expand the report rather than keeping it minimal.

## Pitfalls to Avoid

- Reusing old screenshots from previous runs.
- Showing the same generic title across multiple listings.
- Capturing only the top of the Marketplace page instead of scrolling to the relevant listing content.
- Omitting retail price context or cross-location data when the user has asked for comparative analysis.