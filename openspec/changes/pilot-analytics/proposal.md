# Proposal: pilot-analytics

> Phase 2 (pilot, after demo day 20 Nov 2026).

## Why

Return-reduction claims in this market mostly come from vendors comparing users with non-users, which is biased. Zalando's own published study found that personalized size recommendations raised conversion by 2.1 % but did not significantly reduce size-related returns. To sell to brands, simiq must measure conversion, multi-size ordering and size-related returns in the pilot against a holdout group that never sees the button.

## What Changes

- Event collection from loader and viewer (eligibility, view, open, recommendation, size selection) without body data.
- Visitor and session identifiers that link product-page activity to orders and returns.
- Deterministic A/B holdout in the loader, configured per shop.
- Order and return ingestion from platform adapters and from CSV for shops without an adapter.
- Pilot report: treatment vs control for conversion, multi-size ordering and size-related return rate, with confidence intervals; CSV export.
- Consent handling, retention limits and deletion.

## Capabilities

### New Capabilities

- `analytics`: measuring simiq's effect on shopper behavior against a holdout, from event collection to the pilot report.

### Modified Capabilities

None.

## Impact

- Changes in `web/widget/` (assignment, events) and `web/viewer/` (events); new ingestion and reporting in `api/`.
- New infrastructure: managed Postgres.
- Depends on `shop-embed-mvp`; uses `platform-adapters` or CSV import for orders and returns.
