# Design: pilot-analytics

## Context

- The loader and viewer exist (`shop-embed`, `tryon-viewer`). Orders and returns arrive through `platform-adapters` or CSV.
- Published evidence: a size recommender can raise conversion while barely moving size returns. It can also change multi-size ordering ("bracketing"). The pilot must measure all three against a holdout, not users against non-users.
- Body data may count as health data by inference, so no body values ever enter analytics.

## Goals / Non-Goals

**Goals:**

- An unbiased treatment-versus-control comparison per shop.
- Honest uncertainty: confidence intervals and the sample size needed.
- Minimal personal data.

**Non-Goals:**

- A general product-analytics platform.
- Cross-shop visitor tracking.
- Real-time dashboards. Daily is enough for a pilot.

## Decisions

### D1. Identifiers

- **`visitor_id`:** random, stored in the shop's first-party storage by the loader, and only when analytics consent is given. It drives experiment assignment.
- **`session_id`:** per visit. It is passed to the viewer iframe as a parameter and to orders through the adapter (cart attribute or cookie).
- Rejected alternative: assignment per session. The same visitor would land in different groups across visits.

### D2. Deterministic holdout in the loader

- **Assignment:** bucket = hash(visitor_id + experiment_id) mod 100. The visitor is in control if bucket < `holdout_pct`.
- **Configuration:** the shop manifest holds `experiment: {id, holdout_pct, start, end}`.
- **Control visitors:** no button. The loader still records an `eligible` event with variant `control`.
- **No analytics consent:** no events, no `visitor_id`, and the visitor sees the button but is excluded from analysis.

### D3. Events and transport

- **Events:** `eligible`, `button_view` (in viewport), `open`, `form_submit` (no values), `recommendation_shown` (size label and confidence only), `size_selected`, `error`.
- **Common fields:** shop key, product identifier, garment id, visitor and session id, variant, versions, timestamp.
- **Transport:** batched and sent with `sendBeacon` to `POST /v1/events`, stored in Postgres.
- **Schema:** allowlisted. Unknown fields are dropped server-side.

### D4. Orders and returns

- **Sources:** CSV upload with columns: order id, line, variant, size label, session id (optional), timestamp, return reason; later, adapters (from `platform-adapters`).
- **Isadore (the pilot):** a custom PHP (Nette) shop, so the CSV is their weekly order and return export. Their developers add `simiq.getSessionId()` to the order record at checkout; until they do, the linkage rate is reported as zero rather than guessed.
- **Reason mapping:** platform reasons map to `size_too_small`, `size_too_large`, `other_fit`, `not_fit_related` and `unknown`, using one table per platform.

### D5. Metrics and statistics

- **Per variant:**
  - **Conversion:** eligible visitors who ordered the eligible product ÷ eligible visitors.
  - **Bracketing rate:** orders with two or more sizes of the same product ÷ orders containing the product.
  - **Size-return rate:** returned lines with size reasons ÷ sold lines.
- **Statistics:**
  - differences between variants with Newcombe–Wilson 95 % intervals;
  - the linkage rate (orders with a session id);
  - a sample-size estimate for detecting a chosen effect, so the brand knows how long the pilot must run.

### D6. Reporting

- A generated weekly report per shop (HTML + CSV) during the pilot.
- The same aggregates feed the brand-portal dashboard later.

### D7. Consent and retention

- **Consent sources:**
  - the shop's consent tool through `simiq.setConsent({analytics})`;
  - on Shopify, the Customer Privacy API in the adapter.
- **Retention:** raw events 13 months; aggregates are kept.
- **Deletion:** by shop and, where linked, by customer, triggered by adapter privacy webhooks.

## Risks / Trade-offs

- [Low traffic gives inconclusive results] → the report includes a sample-size estimate; set pilot duration upfront with the brand.
- [Low linkage between sessions and orders] → report the linkage rate; prefer adapters over CSV.
- [Consent declines bias the analysed sample] → report the share of eligible traffic with consent; treatment and control are equally affected.
- [The holdout costs the brand some benefit] → keep `holdout_pct` small (e.g. 20–50 %) and time-boxed. Agree on it in the pilot contract.

## Migration Plan

The loader change ships as a minor version. Shops without an `experiment` in the manifest behave as before (all treatment, no events unless enabled).

## Open Questions

- Default `holdout_pct` per pilot (a contractual choice; the mechanism is the same).
