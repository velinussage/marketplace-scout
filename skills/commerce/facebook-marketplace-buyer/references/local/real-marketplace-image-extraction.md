# Real Marketplace Image Extraction Pattern

**Date**: 2026-05-19  
**Context**: Extracting actual product images and listing URLs from Facebook Marketplace using browser-harness.

## Working Selector (as of May 2026)

```js
Array.from(document.querySelectorAll("a[href*='/marketplace/item/'] img"))
  .map(img => ({
    src: img.src,
    alt: img.alt || "",
    url: img.closest("a").href.split("?")[0]
  }))
```

## Why this works

- Facebook Marketplace renders listing cards as links containing `/marketplace/item/`.
- The primary product image is the first `<img>` inside that link.
- This avoids profile pictures and UI chrome that dominate generic `img` selectors.

## Recommended Extraction Flow

1. Navigate to search: `https://www.facebook.com/marketplace/?query=...`
2. Wait for load + scroll to trigger lazy loading.
3. Run the selector above.
4. Filter results where `url` contains `/marketplace/item/`.
5. Use the `src` directly in HTML reports (they are stable Facebook CDN URLs).

## Known Limitations

- Title and price extraction from surrounding text is brittle due to heavy client-side rendering.
- Some results may be sponsored or low-quality listings.
- Requires a logged-in session with real Marketplace access.

## Usage in Report Generator

When building HTML reports, prefer this extraction method over placeholder images. Store the full `image_url` and `url` in the report data structure.

This pattern should be re-tested after major Facebook UI changes.