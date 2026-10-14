# Tasks

Starts when the first customer on Shopify, Shoptet or WooCommerce signs (Isadore, the pilot, runs a custom shop and needs none). Build group 1 if `pilot-analytics` has not already added Postgres, then only that customer's platform group.

## 1. Core ingestion contract

- [ ] 1.1 Add Postgres to `api/` with migrations for shops, products, variants, orders, order lines and returns; verify migrations apply and roll back on a fresh database
- [ ] 1.2 Implement `catalog`, `orders` and `returns` endpoints with HMAC shop signatures and idempotency keys; verify tests for valid, invalid-signature and duplicate deliveries
- [ ] 1.3 Implement shop secrets issuance and rotation; verify a rotated secret invalidates the old one
- [ ] 1.4 Document the contract as OpenAPI plus `docs/adapters.md`; verify an example request from the docs succeeds against staging
- [ ] 1.5 Add `simiq.getSessionId()` and cart-attribute/cookie writing to the loader; verify the widget size check still passes and the id is set only after interaction

## 2. Shopify app

- [ ] 2.1 Scaffold the app with Shopify CLI in `adapters/shopify`, OAuth install on a development store; verify install and uninstall work
- [ ] 2.2 Build the theme app extension: app embed loading `loader.js` and the product app block with identifier setting; verify the button appears on a mapped product without theme edits
- [ ] 2.3 Implement privacy webhooks forwarding to core deletion; verify each webhook is handled and acknowledged in tests
- [ ] 2.4 Forward `orders/create`, `returns/request` and `refunds/create` with `_simiq_sid` and reason mapping; verify a size return arrives with `size_too_small`
- [ ] 2.5 Add catalog sync on install and on product updates; verify a new variant arrives within 15 minutes
- [ ] 2.6 Integrate the Billing API with the pilot plan; verify a test charge on the development store
- [ ] 2.7 Run Lighthouse with and without the app on the development store; verify the difference is at most 10 points and save the report
- [ ] 2.8 Request Protected Customer Data access and submit for App Store review; verify submission confirmation

## 3. Shoptet addon

- [ ] 3.1 Complete Shoptet partner registration and confirm cart-to-order attribute and return webhook options; verify answers recorded in `adapters/shoptet/README.md`
- [ ] 3.2 Implement OAuth install and template-include injection; verify the loader appears on a test shop without template edits
- [ ] 3.3 Forward `order:create` and catalog data; verify orders and products arrive in the core from the test shop
- [ ] 3.4 Test placement on the three most common templates and document manual placement; verify on each template

## 4. WooCommerce plugin

- [ ] 4.1 Create the plugin in `adapters/woocommerce` with a settings page for the shop key and identifier choice; verify activation on a local WordPress
- [ ] 4.2 Render loader and placement on product pages; verify the button on a mapped product
- [ ] 4.3 Forward orders (with the session id copied from the cookie into order meta) and refunds; verify both reach the core

## 5. Integration checks

- [ ] 5.1 For the pilot platform, run install → button → order → return end to end on a test shop; verify all records are linked in the core
- [ ] 5.2 Verify uninstall removes code, stops events and schedules deletion on every built adapter
