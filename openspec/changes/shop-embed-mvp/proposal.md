# Proposal: shop-embed-mvp

## Why

simiq has to drop into any e-shop (Shopify, Shoptet, WooCommerce, custom) without slowing or breaking it; large shops reject scripts that block rendering, shift layout or throw errors. For demo day we need a real-looking product page where a "How will it fit?" button opens the viewer and hands the chosen size back to the shop, plus the snippet and guide that become the first integration tutorial.

## What Changes

- `loader.js` (at most 10 KB compressed) that renders a `<simiq-fit>` button only for products listed in the shop's static manifest on the CDN.
- Modal with a lazily created iframe to the viewer; accessible and closes cleanly.
- Host-page events and an optional callback so the shop can preselect the recommended size.
- Failure isolation: no uncaught errors, a manifest timeout, and fallback to nothing or a size-chart link.
- Versioned, cacheable releases with integrity hashes; an integration guide for the HTML snippet.
- A static demo shop page for demo day (a Shopify development store is a stretch goal).

## Capabilities

### New Capabilities

- `shop-embed`: how a shop installs simiq, when the button appears, how the modal and messaging work, and the guarantees towards the host page.

### Modified Capabilities

None.

## Impact

- New code: `web/widget/`, `web/demo-shop/`; `docs/integration.md`.
- CDN layout: `/v1/loader.js`, `/v<x.y.z>/loader.js`, `/shops/<shop-key>/manifest.json`.
- Depends on `tryon-viewer-mvp` (embedded mode, postMessage protocol).
- Manifests are hand-written in this change; `brand-onboarding` (catalog-sync) automates them later. Platform apps come in `platform-adapters`, A/B and events in `pilot-analytics`.
