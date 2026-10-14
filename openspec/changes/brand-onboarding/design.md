# Design: brand-onboarding

## Context

- After the pilot, garments are created by staff with the engine CLI, and shop manifests are hand-written JSON files (`shop-embed-mvp`).
- Postgres exists (`platform-adapters`, `pilot-analytics`). Analytics aggregates exist.
- Digitization remains a service: DXF has no seam information and fabric curves need a swatch, so a person is in the loop.

## Goals / Non-Goals

**Goals:**

- A brand can go from sign-up to a live product without email ping-pong.
- Manifests are generated from catalog data and garment status, never edited by hand.
- Staff see one queue of work.

**Non-Goals:**

- Fully automatic digitization.
- Self-serve billing. Invoicing stays manual.
- Brand-editable fit ranges.

## Decisions

### D1. Data model

Postgres tables:
- `brands`, `users`, `memberships` (role `owner` or `member`); `staff` flag on users;
- `shops` (shop key, platform, allowed origins, settings);
- `products`, `variants` (platform id, SKU, GTIN, size label);
- `garments` (garment-model JSON, status, version);
- `intake_submissions` (sheet data, file references, status history);
- `manifests` (shop, version, JSON, published_at).

### D2. Authentication

- Passwordless magic links sent by a transactional email provider; a session cookie that is httpOnly, Secure and SameSite=Lax.
- Rejected alternative: passwords. Reset flows and storage risk for no benefit at this stage.

### D3. Intake templates generated from the garment model

- XLSX and CSV templates per garment type are generated from the garment-model points of measure and zones, so the template and the contract cannot drift.
- Uploads are parsed server-side, with row- and cell-level errors.
- Files (tech packs, DXF, datasheets, photos) go to private object storage and are downloaded through signed URLs.

### D4. Status workflow

```
draft --> submitted --> in_digitization --> in_review --> live --> archived
              ^                                  |
              +-------- changes_requested <------+
```

- `in_digitization` and `in_review` are set by staff.
- `live` requires the brand to approve the preview.
- Each transition is logged with user and time.
- The SLA target (working days from `submitted` to `in_review`) is configurable; overdue submissions are flagged.

### D5. Preview

- Staff publish an unpublished garment to a preview bundle.
- The brand gets a signed, expiring preview link to the standalone viewer for that garment.

### D6. Catalog sync

- **Sources:**
  - adapter pushes (`platform-adapters` contract);
  - a Google Merchant feed URL polled daily (fields `g:id`, `g:item_group_id`, `g:gtin`, `g:size`, `link`);
  - CSV upload.
- Variants are grouped into products by platform product id or `item_group_id`.
- Size labels are normalized for suggestions, e.g. "Medium" maps to M.
- New or unknown size labels are flagged and left out of the manifest until mapped.

### D7. Manifest publishing

- Triggered by any change to mapping, garment status or shop settings.
- Steps: build the manifest from live garments only, validate it against the `shop-embed` schema, upload a versioned file, then switch the shop's pointer.
- The manifest is published within 5 minutes of the change.
- The last 10 versions are kept; rollback is one action.

### D8. Portal application

- `web/portal`: Vite + TypeScript + Preact, the same stack as the viewer, so the preview component is reused.
- Talks to `api/` under `/v1/portal/*`.

## Risks / Trade-offs

- [Brands upload inconsistent sheets] → strict template validation with clear errors; staff can edit and resubmit on the brand's behalf (logged).
- [A wrong mapping shows the button on the wrong product] → only live garments are published; mapping changes show a diff before publishing.
- [Magic-link email is delayed or lands in spam] → a reputable provider, SPF/DKIM set up, and a resend option.
- [Scope creep into a full PIM] → the catalog only stores identifiers needed for mapping.

## Migration Plan

Import the existing hand-written manifests and garments as initial data. Compare generated manifests with the hand-written ones before switching pointers. Keep the hand-written files as the first manifest versions for rollback.

## Open Questions

- SLA target value (working days) to promise brands. It is a configuration value, decided with pricing.
