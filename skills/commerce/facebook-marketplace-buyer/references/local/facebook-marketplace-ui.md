---
title: Facebook Marketplace Browser UI Runbook
description: Verified URL patterns, DOM selectors, extraction logic, and failure modes for Facebook Marketplace automation using browser-harness.
---

# Facebook Marketplace Browser UI Runbook

This document captures field-tested browser automation patterns for Facebook Marketplace.

**Last verified**: 2026-05-19 (with browser-harness + Chrome)

## URL Patterns

### Home / Search
- Base Marketplace: `https://www.facebook.com/marketplace/`
- Search with query: `https://www.facebook.com/marketplace/?query=varier%20chair`
- Category example: `https://www.facebook.com/marketplace/category/furniture/`

### Item Detail
- Pattern: `https://www.facebook.com/marketplace/item/<item_id>/`

### Inbox / Messages
- `https://www.facebook.com/marketplace/inbox/`

## Key Selectors (Stable as of May 2026)

### Search Results Page
- Listing card container: `div[aria-label*="Marketplace"] article` or `div[data-testid="marketplace-feed-item"]`
- Price: `span[aria-label*="price"]` or `div[role="button"] span:first-child`
- Title: `span[aria-label*="title"]` or first strong text in card
- Location: text containing city/neighborhood near price

### Item Detail Page
- Title: `h1` or `span[role="heading"]`
- Price: large text near title with currency symbol
- Location / Seller: elements containing "miles away" or seller name
- Message button: `div[aria-label*="Message"]` or button with "Message" text

### Message Composer
- Composer textarea: `div[role="textbox"][aria-label*="message"]`
- Send button: `div[aria-label*="Send"]` or button with send icon

## Extraction Logic (Python + browser-harness pattern)

```python
# Example extraction from search results
def extract_listings(page):
    listings = []
    cards = page.query_selector_all('div[aria-label*="Marketplace"] article')
    for card in cards[:15]:
        try:
            price = card.query_selector('span[aria-label*="price"]').inner_text()
            title = card.query_selector('span[aria-label*="title"]').inner_text()
            url = card.query_selector('a').get_attribute('href')
            listings.append({"title": title, "price": price, "url": url})
        except:
            continue
    return listings
```

## Known Failure Signatures

- CAPTCHA or "We detected unusual activity"
- Login wall / session expired
- "This listing is no longer available"
- Lazy-loaded results requiring scroll
- Pre-filled default message when composer opens

## Recommended Browser-Harness Discipline

- Always start with `browser-harness --doctor`
- Keep exactly one Marketplace search tab as anchor
- Use temporary detail tabs and close them after extraction
- Never leave the browser in an inconsistent state

## Self-Inspection Block

When selectors break, run:

```python
browser-harness <<'PY'
from browser_harness import page
print(page.title())
print(page.url)
# Dump relevant DOM structure
print(page.evaluate("document.querySelectorAll('article').length"))
PY
```

## Verification Checklist

- [ ] Can reach Marketplace home while logged in
- [ ] Search returns visible listing cards
- [ ] Can open item detail and extract price + title
- [ ] Message composer opens without sending
- [ ] All temporary tabs are closed after use

This runbook should be updated whenever Facebook changes its Marketplace DOM.