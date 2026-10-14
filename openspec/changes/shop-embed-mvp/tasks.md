# Tasks

Target: T4 (2–8 Nov 2026), after tryon-viewer-mvp group 6.2 (embedded mode). Demo-shop polish in T5.

## 1. Setup

- [ ] 1.1 Create `web/widget` (TypeScript, library build to a single `loader.js`, vitest, Playwright) with a 10 KB compressed size check wired into the `web` CI job; verify `pnpm build` and that the size check fails above 10 KB

## 2. Manifest

- [ ] 2.1 Define the manifest JSON Schema and write the demo shop manifest; verify the example validates and that a size label pointing to a non-existent garment size fails a check script
- [ ] 2.2 Add a publish script for manifests to the CDN (5-minute cache); verify the manifest is fetchable from a browser on the demo origin

## 3. Loader and button

- [ ] 3.1 Implement placement scanning, `simiq.mount()`, `allowed_origins` check and `MutationObserver` re-mounting; verify Playwright tests for mapped, unmapped, disallowed-origin and re-rendered placements
- [ ] 3.2 Implement `<simiq-fit>` with Shadow DOM, theming variables and `::part(button)`; verify the hostile-CSS and theming tests
- [ ] 3.3 Implement the 3-second manifest timeout, global error isolation and the fallback link; verify tests with a blocked CDN show no uncaught errors
- [ ] 3.4 Add `?simiq_debug=1` console diagnostics; verify nothing is logged without the flag

## 4. Modal and messaging

- [ ] 4.1 Implement the `<dialog>` modal with a lazily created viewer iframe, scroll lock and focus return; verify the Escape/focus test and that no viewer request happens before the click
- [ ] 4.2 Implement v1 message handling with origin and version checks, and the viewer-not-ready error state; verify the forged-message test and the not-ready test
- [ ] 4.3 Dispatch `simiq:recommendation` and `simiq:select-size` events and call `onSelectSize`; verify the demo shop preselects the chosen size
- [ ] 4.4 Add `preconnect` hints on button hover/focus; verify in the network log that they appear only after intent

## 5. Release and documentation

- [ ] 5.1 Publish releases to `/v1/loader.js` and `/v<x.y.z>/loader.js` with SRI hashes in release notes; verify a pinned include with the hash loads and a tampered copy is refused
- [ ] 5.2 Write `docs/integration.md` (snippet, placeholder CSS, identifiers, events, CSP entries, troubleshooting); verify by following it on a blank HTML page

## 6. Demo shop

- [ ] 6.1 Build `web/demo-shop` (cycling product page, size selector, fake cart) with the snippet and placeholder CSS; verify the Lighthouse run shows no simiq layout shift and record the performance score with and without the loader
- [ ] 6.2 (Stretch) Paste the snippet into a Shopify development store theme; verify the button works on a product page
- [ ] 6.3 Write the demo-day click path and backup plan in `docs/demo-script.md`; verify it in a full rehearsal on the production environment
- [ ] 6.4 Agree placement, product identifier (SKU or product id) and CSP entries with Isadore's developers and write their shop manifest; verify the button appears on an Isadore product page in their test environment (or a saved copy of the page if they have none)
