# Design: shop-embed-mvp

## Context

- The viewer and API come from `tryon-viewer-mvp`. The viewer already supports embedded mode with the v1 message envelope.
- Shops differ widely: Shopify themes (often re-rendering on variant change), Shoptet templates, WooCommerce themes and custom stacks. Many shops run a strict CSP and cookie-consent tools.
- Shopify's guidance for theme app extensions suggests ≤ 10 KB of JS, and the App Store limits an app's impact to 10 Lighthouse points. These are useful budgets even outside Shopify.
- Manifests are hand-written for the demo and the first pilot (catalog sync comes in `brand-onboarding`).

## Goals / Non-Goals

**Goals:**

- One-line install that works on any HTML page.
- Zero visible effect when a product is not mapped or anything fails.
- No layout shift and nothing heavy before interaction.

**Non-Goals:**

- Platform apps (`platform-adapters`).
- Events and A/B tests (`pilot-analytics`).
- Automatic catalog sync (`brand-onboarding`).
- Variant selection inside the shop. The shop handles it from our event.

## Decisions

### D1. Script loader + custom element + lazy iframe modal

- The loader renders a small `<simiq-fit>` button in the page.
- The viewer runs in an iframe that is created only on click.
- Rejected alternatives:
  - **iframe-only embed:** needs a fixed size, looks foreign and cannot read the page's product or variant.
  - **Full SDK in the page:** CSS conflicts, a heavy bundle and the shop's CSP applies to all of our code.

### D2. Static per-shop manifest on the CDN

- **Location:** `/shops/<shop-key>/manifest.json`, cached for 5 minutes.
- **Contents:**
  - `allowed_origins`;
  - `products`: identifier → `{garment_id, sizes: {shop_label: garment_size}}`;
  - `settings`: `locale`, `fallback_size_chart_url`, theme variables.
- Deciding whether to show the button needs only the CDN, never the API. A CDN is far more available than a single API instance.
- Rejected alternative: an API lookup per page view. It adds latency, load and a failure point on every product page.

### D3. Placement and mounting

- **Placement:** a placeholder element `<div data-simiq-product="<identifier>"></div>`. The identifier is the SKU, product id or GTIN, whichever the manifest uses.
- **Programmatic alternative:** `simiq.mount(element, {product})`.
- **Scanning:** the loader scans on `DOMContentLoaded`. A `MutationObserver` handles themes that re-render placeholders on variant change.
- **Layout shift:** documented placeholder CSS (`min-height: 44px`) reserves space, so the button never shifts layout.

### D4. Style isolation

- The button lives in Shadow DOM.
- Theming goes through CSS custom properties (`--simiq-accent`, `--simiq-text`, `--simiq-radius`, `--simiq-font`) and `::part(button)`.

### D5. Modal via native `<dialog>`

- `showModal()` puts the modal in the browser's top layer. That avoids z-index fights with themes and gives ESC handling and focus containment for free.
- The modal creates the iframe `viewer/fit?embed=1&shop=…&garment=…&lang=…` on first open.
- When it closes, it returns focus to the button and unlocks page scroll.

### D6. Hand-off to the shop

- When the viewer sends `select-size` or `recommendation`, the loader dispatches `simiq:select-size` and `simiq:recommendation` CustomEvents on the placeholder element; they bubble up to `document`.
- The event detail carries `{product, sizeLabel}`.
- The loader also calls an optional `onSelectSize` callback from the config.
- The demo shop shows how to preselect a variant.

### D7. Failure isolation

- All entry points are wrapped, so an error inside the loader never surfaces as an uncaught error on the page.
- The manifest fetch times out after 3 s. On failure the loader renders nothing, or a plain link when `fallback_size_chart_url` is set.
- Diagnostics appear in the console only with `?simiq_debug=1`.

### D8. Versioning, caching and integrity

- **Moving URL:** `/v1/loader.js`, cached for 5 minutes, used by the default snippet.
- **Immutable URLs:** `/v<x.y.z>/loader.js`, cached long, with SRI hashes published in the release notes. Shops with strict policies pin these.
- The loader never loads other scripts into the host page.

### D9. Warm-up on intent

- On hover or focus of the button, the loader adds `preconnect` hints for the viewer and CDN origins. This makes the modal open faster without loading anything up front.

### D10. Demo shop

- `web/demo-shop` is a static cycling product page with a size selector and a fake "add to cart". It listens for `simiq:select-size`.
- A Shopify development store with the snippet pasted into the theme is a stretch goal and a preview of `platform-adapters`.

## Risks / Trade-offs

- [The shop's CSP blocks our script or frame] → the guide lists the exact `script-src`, `connect-src` and `frame-src` entries.
- [The shop doesn't reserve space, so the layout shifts] → the guide puts the placeholder CSS first; the button height is fixed.
- [Theme re-renders remove the button] → the `MutationObserver` re-mounts it.
- [Wrong size-label mapping in the hand-written manifest] → manifest schema validation plus a check that every mapped size exists in the garment.
- [A third party reuses a shop key elsewhere] → `allowed_origins` in the manifest; the loader renders nothing on other origins.

## Migration Plan

New assets only. Rollback by repointing `/v1/loader.js` to the previous immutable version.

## Open Questions

- The default button text per language (copy can change without affecting specs).
