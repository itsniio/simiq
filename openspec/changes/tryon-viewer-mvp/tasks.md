# Tasks

Target: groups 3–5 can start in T2 against fixtures; groups 1–2 in T3 (after fit-engine-poc groups 3–6); groups 5–7 in T3–T5. Production freeze 18 Nov 2026. UI tasks build from the Figma frames listed in design D4b, read through the Figma MCP.

## 1. Surrogate and precompute (Python)

- [ ] 1.1 (#44) Implement a population sampler covering the supported input ranges (sex, body and region types, height, BMI, measurement deviations); verify with coverage plots saved in `engine/docs/surrogate.md`
- [ ] 1.2 (#45) Add a batch command that computes standing inputs and pose measurements for about 10k sampled bodies; verify the dataset file and its row count
- [ ] 1.3 (#46) Fit surrogate models per input set and export them as numpy-only files; verify on held-out bodies that pose-measurement MAE ≤ 0.5 cm and recommendation agreement ≥ 95 %
- [ ] 1.4 (#47) Export the body mesh grid (594 cells) as `.glb` with pose clips, `_ZONE_JERSEY` and `_ZONE_BIB` attributes and meshopt compression; verify every file is ≤ 300 KB and loads in a Three.js test page
- [ ] 1.5 (#48) Build the garment bundle (garments with display data, fabrics, fit ranges, version hash) and a publish script for bundle and meshes to the staging CDN; verify the URLs respond from a browser

## 2. Fit API

- [ ] 2.1 (#49) Create `api/` as a uv FastAPI project depending on `engine` without PyTorch at runtime, with `/healthz`; verify the container image builds and `/healthz` returns garment count and model version
- [ ] 2.2 (#50) Implement `POST /v1/recommendations` with the surrogate and fit computation; verify contract tests for 200, 404 `garment_not_found` and 422 `height_cm`
- [ ] 2.3 (#51) Implement `GET /v1/garments` and `GET /v1/garments/{id}` with display data and public data only; verify tests that fabric curves, fit ranges and prices are absent and the list holds every published garment once
- [ ] 2.4 (#52) Add version fields, the CORS allowlist and per-IP rate limiting; verify tests for the version fields, a disallowed origin and the 61st request returning 429
- [ ] 2.5 (#53) Add structured logging with a field allowlist and error-report scrubbing; verify a test that logs and error reports contain no body values
- [ ] 2.6 (#54) Run a load test (20 concurrent, 5 minutes); verify server-side p95 ≤ 300 ms and save the report in `api/docs/load-test.md`
- [ ] 2.7 (#55) Deploy the API to staging with health checks and an uptime monitor; publish the OpenAPI docs; verify `/healthz` from outside and that the monitor alerts on a stopped container

## 3. Viewer foundation (TypeScript)

- [ ] 3.1 (#56) Create the `web/` pnpm workspace and `web/viewer` (Vite, TypeScript, Preact, vitest, eslint) and add a `web` job to `.github/workflows/ci.yml` (test, lint, budgets, `pnpm audit`); verify the job runs green on a PR
- [ ] 3.2 (#57) Add i18n with SK (the Figma copy), CS and EN message files and language selection by parameter or browser, plus a test that fails on any user-facing string outside the message files; verify the `lang=sk` test, the English default and that a hardcoded string makes the test fail
- [ ] 3.3 (#58) Add bundle budgets (80 KB initial, 250 KB 3D chunk) to the build check; verify that adding a large dependency makes the check fail
- [ ] 3.4 (#59) Create `tokens.css` from the Figma variables and a lint rule forbidding raw hex outside it; verify a raw hex in a component fails lint
- [ ] 3.5 (#60) Generate `api-types.ts` from the API's OpenAPI document; verify a changed response field breaks the type check

## 4. Studio and onboarding

- [ ] 4.1 (#61) Build the three-area layout from frame `473:3` with folding side panels and the interim stacking on narrow screens; verify designer sign-off on a 1440 px comparison screenshot and a 390 px stacking test
- [ ] 4.2 (#62) Build onboarding step 1 from frame `478:1203` (sex, weight, height, body type) with the API's validation ranges; verify the required-step and invalid-value scenarios
- [ ] 4.3 (#63) Build steps 2 and 3 from frames `478:1202` and `478:1201` (arm, torso and leg types; upper and lower body measurements), both skippable; verify the skip scenario and designer sign-off on each step's screenshot
- [ ] 4.4 (#64) Add the privacy notice, policy link and consent checkbox; verify a test that no request with body data happens without consent
- [ ] 4.5 (#65) Add opt-in profile memory and "forget me", with storage access wrapped; verify tests for prefill, deletion and storage that throws

## 5. Products, results and 3D

- [ ] 5.1 (#66) Build the product list from frame `483:645` (search, category filters, cards with image, name, color count and the manifest's price when a shop is known); verify the filter scenario
- [ ] 5.2 (#67) Build the product detail from frame `483:644` (name, subtitle, price, image, colors, sizes, "Try on", key features with material properties); verify it renders a fixture garment completely
- [ ] 5.3 (#68) Mark the recommended size with plain-language confidence and zone explanations; verify the high- and low-confidence fixtures
- [ ] 5.4 (#69) Build the Three.js scene from frame `485:751`: body mesh, standing by default, bike control to `hoods`, rotate, reset view and fullscreen; verify on a desktop browser and a phone
- [ ] 5.5 (#70) Color zones from statuses using the zone attributes, with legend and text labels; verify colors and labels match a fixture for every status
- [ ] 5.6 (#71) Highlight the body part and show measuring instructions when a step-3 info icon or field is clicked; verify the chest-help scenario
- [ ] 5.7 (#72) Add size and pose switching from already-loaded data; verify the update takes under 200 ms and makes no new API request
- [ ] 5.8 (#73) Implement "Buy the fit" (embedded: `select-size` messages; standalone: product links when a shop is known); verify the embedded scenario with a test parent page
- [ ] 5.9 (#74) Implement degradation paths (no WebGL, mesh load failure, API error with retry and size-chart link); verify each by forcing the failure in a test

## 6. Modes and accessibility

- [ ] 6.1 (#75) Implement the standalone routes `/fit` and `/fit?garment=…`; verify a shared link opens the studio with the right garment selected
- [ ] 6.2 (#76) Implement embedded mode with the v1 message envelope (`hello`, `ready`, `recommendation`, `select-size`, `close`), origin checks and the shop's product already tried on; verify with a test parent page, including a disallowed origin
- [ ] 6.3 (#77) Run an accessibility pass (keyboard-only flow, labels, contrast); verify an automated axe check reports no violations and a manual keyboard run completes

## 7. Deployment and demo readiness

- [ ] 7.1 (#78) Deploy the viewer and assets to staging and production on the CDN with versioned paths; verify the flow from a phone on mobile data
- [ ] 7.2 (#79) Build the offline demo (both garments, three bodies, local assets) and record the demo video; verify the offline demo runs with the network disabled
- [ ] 7.3 (#80) Run the end-to-end check: standalone link → onboarding → try on → recommendation → 3D standing and on the bike for both garments on iOS Safari and Android Chrome; verify and record results in `web/viewer/docs/e2e-check.md`
