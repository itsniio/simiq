# Tasks

Phase 2 (after the first pilot, when brand number two arrives). Depends on platform-adapters group 1 (Postgres) and pilot-analytics (aggregates for the dashboard).

## 1. Data model and auth

- [ ] 1.1 Add migrations for brands, users, memberships, shops, garments, intake submissions and manifests; verify migrations apply and roll back
- [ ] 1.2 Implement magic-link sign-in (15-minute single-use links, secure session cookie) with a transactional email provider; verify expired and reused links are refused
- [ ] 1.3 Implement roles and brand isolation in all portal endpoints; verify cross-brand access tests return 403

## 2. Garment intake

- [ ] 2.1 Generate XLSX/CSV intake templates from the garment-model contract per garment type; verify templates contain every point of measure used by default zones
- [ ] 2.2 Implement sheet parsing and validation with row/column errors; verify the "eighty" scenario and the missing-fabric scenario
- [ ] 2.3 Implement private file uploads with expiring links; verify another brand's user is denied
- [ ] 2.4 Implement the status workflow with transition rules, logging and the `in_review` validation gate; verify the workflow scenarios
- [ ] 2.5 Implement turnaround targets and overdue flags in the staff queue; verify with a backdated submission

## 3. Staff tools and preview

- [ ] 3.1 Build the staff queue (submissions, overdue, assignee) and a command to turn an intake into a garment record using the engine; verify a submitted sample becomes a valid garment record
- [ ] 3.2 Implement preview bundles and signed preview links to the standalone viewer; verify a link expires and shows the unpublished garment

## 4. Catalog sync and manifests

- [ ] 4.1 Implement catalog import from adapters, Google Merchant feed (daily) and CSV; verify the feed scenario with a sample feed
- [ ] 4.2 Implement product–garment and size-label mapping with normalized suggestions and flagged new labels; verify the suggestion and XXL scenarios
- [ ] 4.3 Implement manifest generation, schema validation, versioned upload, pointer switch and rollback; verify the go-live (≤ 5 minutes), invalid-manifest and rollback scenarios
- [ ] 4.4 Import existing hand-written manifests and garments and compare generated manifests with them; verify no differences before switching pointers

## 5. Portal UI

- [ ] 5.1 Create `web/portal` (Vite, TypeScript, Preact) with sign-in and brand switcher; verify build and sign-in flow end to end
- [ ] 5.2 Build shop settings, product overview with filters, intake upload and status views; verify the theme-change and filter scenarios
- [ ] 5.3 Build preview, approve and request-changes flows; verify the request-changes scenario
- [ ] 5.4 Build installation instructions per platform and the results dashboard; verify the custom-shop and active-pilot scenarios
- [ ] 5.5 Run an accessibility pass on the portal; verify an axe check reports no violations

## 6. Integration check

- [ ] 6.1 Run a full onboarding with a test brand: sign up → intake → digitization → preview → approve → manifest → button on the demo shop; verify every step without manual database edits
