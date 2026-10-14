# Tasks

Phase 2 (after 20 Nov 2026), before the Isadore pilot goes live. Depends on shop-embed-mvp. Isadore runs a custom shop, so orders and returns come by CSV export (group 3); no platform adapter is needed.

## 1. Event pipeline

- [ ] 1.1 Add Postgres to `api/` with migrations for events, orders, order lines and returns; verify migrations apply and roll back on a fresh database
- [ ] 1.2 Add `POST /v1/events` with the field allowlist; verify a test that `height_cm` is dropped and valid events are stored
- [ ] 1.3 Add batched `sendBeacon` event sending to the loader and the viewer; verify the widget size check still passes and events arrive from the demo shop

## 2. Experiment assignment and consent

- [ ] 2.1 Extend the manifest schema with `experiment` and implement deterministic assignment in the loader; verify stable assignment across reloads and the control-visitor scenario
- [ ] 2.2 Implement `simiq.setConsent()` and the no-consent path (button shown, no ids, no events); verify the consent-declined scenario

## 3. Orders and returns

- [ ] 3.1 Implement CSV import for orders and returns with reason mapping tables per platform; verify the CSV import scenario with a sample file
- [ ] 3.2 Link orders to sessions via session id and compute the linkage rate; verify with fixture data containing linked and unlinked orders

## 4. Report

- [ ] 4.1 Compute conversion, bracketing and size-return rates per variant with Newcombe–Wilson intervals; verify against a hand-calculated fixture
- [ ] 4.2 Add the sample-size estimate and generate the weekly HTML/CSV report per shop; verify the report contains all required sections and no visitor-level rows

## 5. Retention and checks

- [ ] 5.1 Implement the 13-month retention job and deletion by shop and by linked customer; verify with backdated fixtures
- [ ] 5.2 Run a full dry run on the demo shop with a 50 % holdout and fake orders; verify the report shows both variants and plausible numbers
