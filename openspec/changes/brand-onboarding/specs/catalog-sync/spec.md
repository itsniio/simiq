# Spec Delta: catalog-sync

## Purpose

Keeps simiq's view of each shop's products and variants in sync with the shop, maps them to digitized garments and sizes, and publishes the shop manifest that tells the loader where to show the button.

## ADDED Requirements

### Requirement: Catalog sources
The system SHALL import products and variants from platform adapters, from a Google Merchant feed URL polled at least daily, and from CSV upload.

#### Scenario: Merchant feed
- **WHEN** a shop configures a Google Merchant feed URL
- **THEN** its products and variants are imported within 24 hours, grouped by `item_group_id`

### Requirement: Variant identifiers
Each variant SHALL store its platform id, SKU, GTIN when available, size label, title and product URL.

#### Scenario: Variant without GTIN
- **WHEN** a variant has no GTIN
- **THEN** it is stored and can still be mapped by SKU or platform id

### Requirement: Mapping to garments and sizes
Brand users SHALL be able to map a product to a garment and each shop size label to a garment size. The system SHALL suggest size mappings from normalized labels.

#### Scenario: Suggested mapping
- **WHEN** a product has labels "Small", "Medium", "Large" and the garment has sizes S, M, L
- **THEN** the system suggests Small→S, Medium→M, Large→L for confirmation

### Requirement: Unmapped changes are held back
New or changed size labels SHALL be flagged for mapping and SHALL NOT appear in the manifest until mapped.

#### Scenario: New size
- **WHEN** the shop adds size label "XXL" to a mapped product
- **THEN** XXL is flagged and the manifest maps only the existing labels

### Requirement: Manifest publishing
The system SHALL publish a shop's manifest within 5 minutes of any change to mapping, garment status or shop settings. A manifest SHALL include only products whose garment is `live`, and SHALL validate against the shop-embed manifest schema.

#### Scenario: Garment goes live
- **WHEN** a mapped garment becomes `live`
- **THEN** within 5 minutes the shop manifest includes its products

#### Scenario: Invalid manifest
- **WHEN** a generated manifest fails schema validation
- **THEN** it is not published and staff are alerted

### Requirement: Manifest versions and rollback
Published manifests SHALL be versioned. The last 10 versions SHALL be kept, and staff SHALL be able to roll back to any of them.

#### Scenario: Rollback
- **WHEN** staff roll back a shop to the previous manifest version
- **THEN** the loader receives that version within 5 minutes
