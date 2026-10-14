# Design: platform-adapters

## Context

- The core already works on any page through the snippet (`shop-embed`). Adapters only make installation and data flow native per platform.
- Platform facts as of Oct 2026 (see `simiq-prehlad.md`, section 7):
  - **Shopify:**
    - Theme app extensions are mandatory for App Store apps that touch themes.
    - Billing goes through the Billing API.
    - Three privacy webhooks are mandatory.
    - Reading orders needs Protected Customer Data approval.
    - Thank-you-page scripts stopped working on 26 Aug 2026.
    - `ReturnReason` includes `SIZE_TOO_SMALL` and `SIZE_TOO_LARGE`.
  - **Shoptet:**
    - Partner approval via api@shoptet.cz.
    - OAuth per installation; API tokens are valid for 30 minutes.
    - `/template-include` for code injection; webhooks such as `order:create`.
  - **WooCommerce:** a WordPress plugin; webhooks signed with HMAC-SHA256; refunds via the REST API.
- The pilot brand's platform decides which adapter is built first. The others follow when a customer needs them.

## Goals / Non-Goals

**Goals:**

- Install without editing theme code.
- One shared ingestion contract, so the core has no platform branches.
- Pass platform review on the first or second attempt.

**Non-Goals:**

- Fit logic or UI inside adapters.
- Shopware and Magento. Use the snippet until a customer requires them.
- Headless storefronts. Use the snippet or `simiq.mount()`.

## Decisions

### D1. Shared ingestion contract in the core API

- **Endpoints:**
  - `POST /v1/shops/{shop_key}/catalog`: products and variants with platform ids, SKU, GTIN, size label, title, URL and image.
  - `POST /v1/shops/{shop_key}/orders`: order id, lines with variant and size, simiq session id if present, timestamp.
  - `POST /v1/shops/{shop_key}/returns`: order id, line, quantity, reason code, raw platform reason, timestamp.
- **Authentication:** a per-shop secret issued at install, sent as an HMAC signature of the body.
- **Idempotency:** platform event ids are used as idempotency keys.
- Rejected alternative: each adapter writes to the database directly. That couples adapters to the schema and duplicates validation.

### D2. Linking the session to the order

- The loader exposes `simiq.getSessionId()`.
- **Shopify:** the loader adds the session id as cart attribute `_simiq_sid` when the shopper interacts. The adapter reads it from the order's note attributes.
- **WooCommerce:** the loader writes a first-party cookie, which the plugin copies into order meta at checkout.
- **Shoptet:** the mechanism has to be confirmed with Shoptet's partner documentation (see Open Questions). Fallback: a hidden order note.

### D3. Shopify app

- **Base:** Shopify CLI app template (TypeScript).
- **Theme app extension:**
  - an app embed that loads `loader.js`;
  - an app block "simiq fit button" for product templates, with a product identifier setting that defaults to the variant SKU.
- **Other pieces:**
  - **Billing:** the Billing API, with plans defined when pricing is set.
  - **Privacy webhooks:** forwarded to core deletion.
  - **Orders:** `orders/create` webhook.
  - **Returns:** `returns/request` and `refunds/create` webhooks.
  - **Web Pixel:** `checkout_completed` as a secondary signal if webhook access is delayed.

### D4. Shoptet addon

- Partner registration and an addon listing.
- The OAuth install stores the token, then calls template-include to inject the loader and placement.
- Webhooks: `order:create` and others available for status changes.
- Products are read through the API for catalog sync.

### D5. WooCommerce plugin

- A PHP plugin with a settings page for the shop key.
- On product pages it adds the loader script and renders the placement through a WooCommerce product-summary hook.
- An identifier setting chooses between SKU and GTIN.
- On order creation and refunds it calls the core through `wp_remote_post` with the HMAC signature.

### D6. Uninstall

- Every adapter removes injected code on uninstall.
- It notifies the core, which stops ingestion and schedules shop data deletion after 30 days unless the contract says otherwise.

## Risks / Trade-offs

- [Shopify review and Protected Customer Data approval take weeks] → submit early in the pilot; run the pilot on the snippet meanwhile.
- [Theme differences on Shoptet] → test the placement on the 3 most common templates; document manual placement.
- [Session id missing on orders (consent declined, other device)] → treat as unlinked; pilot-analytics reports the linkage rate.
- [Webhook delivery failures] → idempotent ingestion, retries on the platform side, a daily reconciliation job via platform APIs.

## Migration Plan

Shops already on the snippet switch to the app. The adapter detects an existing snippet and tells the merchant to remove it, to avoid double loading. The loader is idempotent if it is included twice.

## Open Questions

- Shoptet: how to carry a custom attribute from cart to order, and whether returns or refunds have webhooks. Confirm during partner onboarding; it affects only the Shoptet task details.
