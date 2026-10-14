# Spec Delta: platform-adapters

## Purpose

Thin per-platform integrations that install simiq without code changes, keep product identifiers in sync and forward order and return events, so that all platforms share one core.

## ADDED Requirements

### Requirement: Shared ingestion contract
Every adapter SHALL send catalog data, orders and returns to the core in the same documented format, with a per-shop signature. Adapters SHALL contain no fit logic.

#### Scenario: Signed catalog push
- **WHEN** an adapter sends a catalog update with a valid shop signature
- **THEN** the core accepts it and stores the products and variants

#### Scenario: Bad signature
- **WHEN** a request arrives with an invalid signature
- **THEN** the core rejects it with 401 and stores nothing

#### Scenario: Duplicate event
- **WHEN** the same platform order event is delivered twice
- **THEN** the core stores the order once

### Requirement: Shopify installation without theme edits
The Shopify app SHALL install via OAuth, SHALL load simiq through an app embed and SHALL place the button through an app block on product templates, without the merchant editing theme code.

#### Scenario: Merchant enables the app
- **WHEN** a merchant installs the app, enables the embed and adds the block to the product template
- **THEN** the fit button appears on mapped products

### Requirement: Shopify compliance
The Shopify app SHALL implement the mandatory privacy webhooks, SHALL charge through the Billing API and SHALL reduce the store's Lighthouse score by no more than 10 points.

#### Scenario: Customer redaction
- **WHEN** Shopify sends `customers/redact` for a customer
- **THEN** simiq deletes that customer's linked analytics data within 30 days and confirms

#### Scenario: Performance review
- **WHEN** Lighthouse runs on a test store with and without the app
- **THEN** the weighted score difference is at most 10 points

### Requirement: Shopify order and return capture
The Shopify app SHALL forward created orders and return or refund events, including return reasons, with the simiq session id when the order carries one.

#### Scenario: Size return
- **WHEN** a customer returns a line with reason `SIZE_TOO_SMALL`
- **THEN** the core receives a return event for that order line with reason code `size_too_small`

### Requirement: Shoptet installation
The Shoptet addon SHALL install from the Shoptet addon marketplace, inject the loader and placement through template include, and forward created orders.

#### Scenario: Shoptet install
- **WHEN** a Shoptet merchant installs the addon
- **THEN** the loader is present on product pages without manual template edits and new orders reach the core

### Requirement: WooCommerce installation
The WooCommerce plugin SHALL add the loader and placement to product pages after the merchant enters a shop key, and SHALL forward orders and refunds.

#### Scenario: Woo install
- **WHEN** a merchant activates the plugin and saves a valid shop key
- **THEN** mapped product pages show the button and new orders reach the core

### Requirement: Catalog identifier sync
Adapters SHALL send product and variant identifiers (platform id, SKU, GTIN, size label) on install and whenever products change.

#### Scenario: New variant
- **WHEN** a merchant adds size XXL to a product
- **THEN** the core receives the new variant within 15 minutes

### Requirement: Uninstall cleanup
Uninstalling SHALL remove injected code and stop data forwarding. Shop data SHALL be deleted within 30 days unless the contract requires otherwise.

#### Scenario: Uninstall
- **WHEN** a merchant uninstalls the adapter
- **THEN** the button no longer appears, no further events are sent and the shop is scheduled for deletion
