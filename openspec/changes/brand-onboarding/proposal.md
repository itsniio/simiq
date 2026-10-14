# Proposal: brand-onboarding

> Phase 2 (after the first pilot). Needed when brand number two arrives.

## Why

During the pilot every brand is handled by email and spreadsheets, and shop manifests are written by hand. That does not scale past one or two brands. Brands need one place to hand over product data, follow digitization, approve garments before they go live and see results, and product mapping must come from their catalog instead of hand-edited files. Digitization itself stays a service performed by simiq.

## What Changes

- Garment intake: templates for points of measure and fabric data, uploads (tech packs, DXF, datasheets, photos), validation with row-level errors, and a status workflow up to "live".
- Catalog sync: products and variants from platform adapters, a Google Merchant feed or CSV; mapping to garments and sizes; automatic, versioned publishing of shop manifests to the CDN.
- Brand portal: passwordless sign-in, brand workspace and roles, shop settings, product list and status, preview and approval, installation instructions and results dashboard.
- Internal staff views for the digitization queue.

## Capabilities

### New Capabilities

- `garment-intake`: what a brand hands over per garment, how it is validated, and how digitization status is tracked until it goes live.
- `catalog-sync`: keeping simiq's view of a shop's products and variants in sync and publishing the shop manifest the loader uses.
- `brand-portal`: the brand's self-service workspace: access, settings, products, approval and results.

### Modified Capabilities

None.

## Impact

- New code: `web/portal/` (TypeScript); auth, brands, shops, products, intake and manifest endpoints in `api/`.
- New infrastructure: Postgres (shared with `pilot-analytics`), private object storage for uploads, transactional email for sign-in.
- Reuses the `garment-model` contract and the manifest format from `shop-embed`; replaces hand-written manifests.
