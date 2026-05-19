# Facebook Marketplace UI Runbook

This is the concrete browser-operation layer for the Marketplace buyer/seller skills. It is non-mutating by default: browse, inspect, extract, draft, and verify only. Do not send messages, publish listings, confirm pickups, share sensitive identity details, or perform payment/deposit actions unless the user separately approves the exact action.

## Field-tested status

Current status: starter runbook assembled from local browser-use/browser-harness conventions plus prior non-mutating Marketplace smoke notes. Before treating a selector as stable, run a local smoke pass in the user's logged-in browser and update this section with date, runtime, page tested, selectors confirmed, and failures observed.

## Runtime choice

### browser-harness

This repo currently targets `browser-harness` for deeper Python/CDP workflows and domain-skill style snippets.

```bash
browser-harness --setup
browser-harness --doctor
```

Expected for live Marketplace work:
- Chrome running: OK
- daemon alive: OK
- if either check fails, live Marketplace browsing is not ready; stop or reconnect before proceeding

### browser-use CLI

`browser-use` is useful for interactive CLI driving, screenshots, state inspection, and quick smoke checks.

```bash
browser-use doctor
browser-use connect
browser-use open https://www.facebook.com/marketplace/
browser-use state
```

Use `browser-use connect` or a real Chrome profile when the task depends on the user's logged-in Facebook session.

Expected for quick checks:
- `browser-use doctor` exits 0
- `browser-use state` can summarize the active page without exposing private content in logs
- `python3 scripts/browser_smoke.py --dry-run` prints the planned Marketplace URLs and `OK: dry-run completed without opening Facebook`

## Compliance and safety posture

This library is for human-in-the-loop Marketplace operations. It uses the user's own browser session, defaults to draft-only or approval-gated workflows, does not send spam, does not perform payments/deposits, does not handle credentials, and does not claim to bypass platform policy. Users are responsible for complying with Facebook's terms.

Never automate login, checkpoint/2FA, seller-facing sends without exact approval, listing publish without explicit publish approval, payment/deposit/shipping commitments, off-platform payment instructions, or sensitive identity disclosure.

## URL patterns

| Surface | URL pattern | Use |
|---|---|---|
| Home | `https://www.facebook.com/marketplace/` | availability, location prompt, broad entry |
| Search | `https://www.facebook.com/marketplace/search/?query={url_encoded_query}` | search with conservative query terms |
| Item detail | `https://www.facebook.com/marketplace/item/{item_id}/` | safest entrypoint for one listing |
| Inbox | `https://www.facebook.com/marketplace/inbox/` | read-only triage and heartbeat |
| Create listing | `https://www.facebook.com/marketplace/create/item/` | dry-run mapping or approved publish preparation |

Prefer visible UI filters unless query parameters have been confirmed in the current session.

## DOM anchor map

Facebook/Comet markup changes often, so prefer semantic anchors and visible text over brittle class names. Treat every selector below as a candidate that must be verified in the current page state.

| Surface | Stable-ish anchors | Candidate selectors / text probes | Non-mutating use |
|---|---|---|---|
| Marketplace shell | `location.href` contains `/marketplace` and page text contains `Marketplace` | `a[href*="/marketplace/"]`, `h1`, `[role="main"]` | confirm you are in the Marketplace surface |
| Search results | item links and card text | `a[href*="/marketplace/item/"]`, nearest `[role="article"]`/`[aria-label]`/parent `div` | collect visible cards and canonical item URLs |
| Listing detail | item URL, title, price, availability text | `h1`, `img`, `[role="button"]`, buttons with `Message`/`Send`/`Ask` | extract item facts and composer candidates |
| Message composer | visible editable text input | `[contenteditable="true"]`, `textarea`, `input[type="text"]` | inspect or draft only; stop before Send |
| Inbox | thread rows/links and snippets | `a[href*="marketplace"]`, `a[role="link"]`, nearest `[role="row"]`/`[role="listitem"]` | classify threads read-only |
| Listing form | visible controls and comboboxes | `input`, `textarea`, `[contenteditable="true"]`, `[role="combobox"]`, buttons | map fields or fill draft; stop before Publish |
| Mutating controls | button text | `Send`, `Publish`, `Pay`, `Deposit`, `Confirm`, `Place order`, `Buy now` | hard stop unless exact action approval exists |

## Non-mutating navigation helpers

Use these snippets as copy-pasteable primitives for browser-harness style sessions. They intentionally avoid sends, publishes, payments, deposits, credential entry, or account mutation.

```python
from urllib.parse import quote_plus

MARKETPLACE_HOME = 'https://www.facebook.com/marketplace/'
MARKETPLACE_INBOX = 'https://www.facebook.com/marketplace/inbox/'
MARKETPLACE_CREATE_ITEM = 'https://www.facebook.com/marketplace/create/item/'


def marketplace_search_url(query):
    return f'https://www.facebook.com/marketplace/search/?query={quote_plus(query)}'


def open_marketplace_home(open_url, wait):
    open_url(MARKETPLACE_HOME)
    wait(2)
    return 'opened-home-read-only'


def open_marketplace_search(open_url, wait, query):
    open_url(marketplace_search_url(query))
    wait(2)
    return {'opened_search': query, 'mode': 'read-only'}


def open_marketplace_inbox_read_only(open_url, wait):
    open_url(MARKETPLACE_INBOX)
    wait(2)
    return {'opened_inbox': True, 'mode': 'read-only'}


def open_listing_form_dry_run(open_url, wait):
    open_url(MARKETPLACE_CREATE_ITEM)
    wait(2)
    return {'opened_create_form': True, 'mode': 'dry-run-form-mapping'}
```

State detection before acting:

```python
def detect_marketplace_surface(js):
    return js('''
    (() => {
      const text = document.body.innerText || '';
      const url = location.href;
      const buttons = Array.from(document.querySelectorAll('button, [role="button"]'))
        .map(b => (b.innerText || b.getAttribute('aria-label') || '').trim()).filter(Boolean);
      const editableCount = document.querySelectorAll('[contenteditable="true"], textarea, input[type="text"]').length;
      return {
        url,
        is_marketplace: /\/marketplace\//i.test(url) || /Marketplace/i.test(text),
        is_search: /\/marketplace\/search/i.test(url),
        is_item: /\/marketplace\/item\//i.test(url),
        is_inbox: /\/marketplace\/inbox/i.test(url),
        is_create_form: /\/marketplace\/create/i.test(url),
        has_composer_like_input: editableCount > 0,
        mutating_button_candidates: buttons.filter(x => /^(Send|Publish|Pay|Deposit|Confirm|Place order|Buy now)$/i.test(x)).slice(0, 20),
        page_excerpt: text.slice(0, 1200)
      };
    })()
    ''')
```

Hard-stop guard for any automation plan:

```python
def assert_non_mutating_plan(action_name):
    blocked = {'send', 'publish', 'pay', 'deposit', 'confirm', 'buy_now', 'place_order'}
    if action_name in blocked:
        raise RuntimeError(f'STOP: {action_name} requires exact human approval outside this runbook')
```

## Authentication and login-wall behavior

Detect these states before extraction:
- logged out: URL contains `/login` or page text asks the user to log in
- checkpoint / 2FA: URL or text contains `checkpoint`, `two-factor`, `security check`, or `confirm your identity`
- Marketplace unavailable: page text says Marketplace is unavailable or restricted
- location prompt: page requests a location before showing results

Browser-harness style check:

```python
def detect_facebook_gate(js):
    return js('''
    (() => {
      const text = document.body.innerText || '';
      const url = location.href;
      return {
        url,
        login: /\/login|Log in|Email address or phone number/i.test(url + ' ' + text),
        checkpoint: /checkpoint|two-factor|security check|confirm your identity/i.test(url + ' ' + text),
        marketplace_unavailable: /Marketplace isn't available|Marketplace is not available|not available to you/i.test(text),
        location_prompt: /Choose Location|Update location|location to show/i.test(text)
      };
    })()
    ''')
```

If `login` or `checkpoint` is true, stop and ask the user to fix the session manually. Do not type credentials.

## Search results: scroll-and-collect pattern

Facebook virtualizes feeds. Collect visible cards before scrolling; do not scroll first and then assume old cards are still mounted.

```python
MARKETPLACE_ITEM_RE = '/marketplace/item/'

def collect_visible_marketplace_cards(js):
    return js('''
    (() => {
      const anchors = Array.from(document.querySelectorAll('a[href*="/marketplace/item/"]'));
      const cards = anchors.map(a => {
        const container = a.closest('[role="article"], div[aria-label], div') || a.parentElement;
        const text = (container?.innerText || a.innerText || '').trim();
        const href = a.href ? a.href.split('?')[0] : null;
        const price = (text.match(/\$[0-9][0-9,]*(?:\.\d{2})?/) || [null])[0];
        const lines = text.split('\n').map(s => s.trim()).filter(Boolean);
        return { href, text, price, lines: lines.slice(0, 12) };
      }).filter(x => x.href);
      const seen = new Map();
      for (const c of cards) if (!seen.has(c.href)) seen.set(c.href, c);
      return Array.from(seen.values());
    })()
    ''') or []

def scroll_and_collect(js, scroll, wait, target=25, max_scrolls=8):
    seen = {}
    for _ in range(max_scrolls):
        for card in collect_visible_marketplace_cards(js):
            seen.setdefault(card['href'], card)
        if len(seen) >= target:
            break
        scroll(700, 500, dy=900)
        wait(1.5)
    return list(seen.values())
```

Verification: every result should have a canonical `/marketplace/item/` URL; dedupe by canonical URL; report count collected and scroll count used; if zero cards, inspect gates before saying no results exist.

## Listing detail extraction

Open direct item links in a new tab when possible. Close temporary tabs after extraction.

```python
def extract_marketplace_listing_detail(js):
    return js('''
    (() => {
      const text = document.body.innerText || '';
      const title = document.querySelector('h1')?.innerText?.trim() || null;
      const price = (text.match(/\$[0-9][0-9,]*(?:\.\d{2})?/) || [null])[0];
      const unavailable = /sold|pending|no longer available|listing is no longer available/i.test(text);
      const messageButtons = Array.from(document.querySelectorAll('[role="button"], button'))
        .map((b, i) => ({ index: i, text: b.innerText || b.getAttribute('aria-label') || '' }))
        .filter(b => /message|send|ask|available/i.test(b.text));
      const imageCount = document.querySelectorAll('img').length;
      return { url: location.href.split('?')[0], title, price, unavailable,
        message_button_candidates: messageButtons.slice(0, 10), image_count: imageCount,
        body_excerpt: text.slice(0, 2500) };
    })()
    ''')
```

Verification: title/body identifies the item; price is checked against visible page text; sold/unavailable state is explicit; composer candidate exists before drafting outreach.

## Message composer behavior

Marketplace may prefill a default opener such as “Hi, is this still available?” Treat any prefilled text as an unsent draft only.

Rules:
- opening the composer does not authorize sending
- exact-text approval for a custom message does not authorize sending Facebook's prefilled default
- replace the draft with the approved text before any send
- verify the text box value after replacement
- stop before clicking Send unless the user approved that exact send action

Draft-only discovery:

```python
def find_message_textbox(js):
    return js('''
    (() => {
      const boxes = Array.from(document.querySelectorAll('[contenteditable="true"], textarea, input[type="text"]'));
      return boxes.map((el, i) => ({ index: i, tag: el.tagName, role: el.getAttribute('role'),
        label: el.getAttribute('aria-label'), text: el.innerText || el.value || '',
        visible: !!(el.offsetWidth || el.offsetHeight || el.getClientRects().length)
      })).filter(x => x.visible);
    })()
    ''')
```

Draft-only composer planning. This does not click Message or Send and does not type into the page; it only reports whether a visible composer-like field exists and records the exact approved draft text the operator would need to review before any separate send approval.

```python
def plan_message_draft_only(js, draft_text):
    boxes = find_message_textbox(js)
    return {
        'mode': 'draft-only',
        'will_type': False,
        'will_send': False,
        'draft_text_for_human_review': draft_text,
        'composer_candidates': boxes,
        'stop_condition': 'Do not type or click Send until the operator approves the exact next action.'
    }
```

For real typing after separate approval, prefer native keystrokes through browser-harness/browser-use rather than synthetic value assignment. Many React/Comet inputs only enable buttons after real input events.

## Seller inbox extraction

Inbox read-only triage should collect thread candidates and visible snippets without replying.

```python
def extract_marketplace_inbox_threads(js):
    return js('''
    (() => {
      const text = document.body.innerText || '';
      const links = Array.from(document.querySelectorAll('a[href*="marketplace"], a[role="link"]'));
      const threads = links.map(a => {
        const row = a.closest('[role="row"], [role="listitem"], div') || a;
        const rowText = (row.innerText || a.innerText || '').trim();
        return { href: a.href || null, text: rowText.slice(0, 1000) };
      }).filter(x => x.text && /\$|available|pickup|interested|Marketplace/i.test(x.text));
      const seen = new Map();
      for (const t of threads) {
        const key = (t.href || t.text).slice(0, 200);
        if (!seen.has(key)) seen.set(key, t);
      }
      return { url: location.href, thread_candidates: Array.from(seen.values()).slice(0, 30), page_excerpt: text.slice(0, 2000) };
    })()
    ''')
```

Verification: report read-only mode, classify candidates without sending, avoid reply/send controls, and preserve queue ambiguity.

## Listing creation / publish form mapping

Use create-listing pages only for dry-run mapping unless a user explicitly approves publish.

Fields to inspect: photos upload, title, price, category, condition, description, location, availability, pickup preferences.

```python
def inspect_listing_form(js):
    return js('''
    (() => {
      const controls = Array.from(document.querySelectorAll('input, textarea, [contenteditable="true"], [role="combobox"], [role="button"], button'));
      return controls.map((el, i) => ({ index: i, tag: el.tagName, role: el.getAttribute('role'),
        type: el.getAttribute('type'), label: el.getAttribute('aria-label') || el.innerText?.slice(0, 80) || null,
        value: el.value || el.innerText || '', disabled: !!el.disabled || el.getAttribute('aria-disabled') === 'true',
        visible: !!(el.offsetWidth || el.offsetHeight || el.getClientRects().length)
      })).filter(x => x.visible);
    })()
    ''')
```

Dry-run listing form plan. This does not upload photos, set fields, click Next, or click Publish. It maps likely controls to proposed synthetic listing fields so the operator can verify the UI before any separate form-fill approval.

```python
def plan_listing_form_dry_run(js, listing_draft):
    controls = inspect_listing_form(js)
    proposed_fields = {
        'title': listing_draft.get('title'),
        'price': listing_draft.get('price'),
        'category': listing_draft.get('category'),
        'condition': listing_draft.get('condition'),
        'description': listing_draft.get('description'),
        'location_scope': listing_draft.get('location_scope'),
    }
    return {
        'mode': 'dry-run-form-mapping',
        'will_fill': False,
        'will_publish': False,
        'visible_controls': controls,
        'proposed_fields_for_human_review': proposed_fields,
        'stop_condition': 'Do not fill required fields or click Publish until the operator approves the exact next action.'
    }
```

Publish safety: never click Publish by default; verify required fields are committed; if a combobox/category looks filled but not committed, treat publish readiness as false; if uncertainty remains, save draft or stop for user review.

## Modal handling

Common modal/interstitial types: login prompt, location prompt, seller profile modal, photo carousel, confirmation dialog, unsaved changes dialog. Before each click, record modal state. After each click, re-run state extraction because element indices and DOM structure may change.

## Tab hygiene

Use a new tab for temporary listing inspection, close temporary listing tabs after extracting or drafting, leave user-owned active tabs in place, report which tabs were opened/closed, and do not accumulate hidden Marketplace tabs across runs.

## Failure catalog

| Failure | Likely signal | Response |
|---|---|---|
| Login wall | `/login` URL or login text | Stop; ask user to log in manually |
| Checkpoint / 2FA | `checkpoint`, `security check` | Stop; never automate credentials |
| Marketplace unavailable | unavailable text | Stop; report account/region issue |
| Location prompt | choose/update location text | Ask user whether to set location manually |
| Virtualized feed lost cards | collected count drops after scroll | collect before each scroll, dedupe by URL |
| Missing price/location | card text lacks price/location | mark field unknown, do not infer |
| Sold/unavailable item | sold/pending/no longer available text | mark unavailable, do not message |
| Prefilled opener | composer already contains text | replace only after exact approval |
| Send disabled | disabled button after draft | use native typing; verify draft text |
| Field not committed | visible value but disabled publish | use native input/combobox selection and re-check |
| Category not selected | combobox text but no committed chip | stop before publish |
| Inbox order changed | thread list reorders after open | re-extract and preserve timestamps/snippets |
| Stale CDP websocket | browser-harness daemon errors | reconnect/setup; do not pretend to browse |

## Self-inspection blocks

### Page summary

```js
(() => ({
  url: location.href,
  title: document.title,
  h1: Array.from(document.querySelectorAll('h1')).map(x => x.innerText).slice(0, 5),
  buttons: Array.from(document.querySelectorAll('button, [role="button"]')).map(x => x.innerText || x.getAttribute('aria-label')).filter(Boolean).slice(0, 40),
  links: Array.from(document.querySelectorAll('a[href]')).map(a => a.href).filter(h => h.includes('/marketplace/')).slice(0, 40),
  text: document.body.innerText.slice(0, 3000)
}))()
```

### Visible controls

```js
(() => Array.from(document.querySelectorAll('input, textarea, [contenteditable="true"], button, [role="button"], [role="combobox"]')).map((el, i) => ({
  i,
  tag: el.tagName,
  role: el.getAttribute('role'),
  label: el.getAttribute('aria-label'),
  text: (el.innerText || el.value || '').slice(0, 120),
  disabled: !!el.disabled || el.getAttribute('aria-disabled') === 'true',
  rect: (() => { const r = el.getBoundingClientRect(); return {x:r.x, y:r.y, w:r.width, h:r.height}; })()
})).filter(x => x.rect.w > 0 && x.rect.h > 0))()
```

## Success verification checklist

Before reporting success:
- state whether the run used browser-use or browser-harness
- state whether the page was logged in and Marketplace was available
- state whether the operation was read-only, draft-only, approval-gated, or bounded-auto
- include canonical listing URLs when listings were collected
- include counts and uncertainty markers
- verify no message was sent unless explicitly approved
- verify no listing was published unless explicitly approved
- verify no payment/deposit/credential step occurred
- update or produce deal/listing state when continuity matters
