# Proposal: platform-adapters

> Waits for the first customer on Shopify, Shoptet or WooCommerce. The pilot brand, Isadore, runs a custom PHP (Nette) shop and integrates with the snippet from `shop-embed-mvp`, so the pilot needs no adapter. Build only the platform of the customer who signs.

## Why

Pilot brands and later customers run Shopify, Shoptet (about 28.6k Czech and 7.6k Slovak shops) or WooCommerce. Pasting a snippet by hand does not scale, Shopify requires theme app extensions for App Store apps, and measuring results needs order and return events from the platform. Thin adapters install the loader, keep product identifiers in sync and forward order and return events, so the core stays one codebase.

## What Changes

- Core ingestion contract: endpoints for catalog data, order events and return events, with per-shop authentication.
- Shopify app: OAuth install, theme app extension (app embed for the loader, app block for the button), Billing API, mandatory privacy webhooks, Web Pixel for completed checkouts, return and refund webhooks.
- Shoptet addon: partner API install, loader injection through template include, order webhooks, product data.
- WooCommerce plugin: settings page with shop key, loader and placement on product pages, order and refund events.
- Uninstall cleanup and data deletion on every platform.

## Capabilities

### New Capabilities

- `platform-adapters`: per-platform installation, compliance and event forwarding, all speaking one shared contract to the core.

### Modified Capabilities

None.

## Impact

- New code: `adapters/shopify/` (TypeScript, Shopify CLI app), `adapters/shoptet/`, `adapters/woocommerce/` (PHP plugin); ingestion endpoints in `api/`.
- External processes: Shopify App Store review, Protected Customer Data access request, Shoptet partner approval. Each can take weeks.
- Feeds `pilot-analytics` (orders, returns) and `brand-onboarding` (catalog-sync).
