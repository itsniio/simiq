# Tasks

Target: groups 3–4 can start in T2 against fixtures; groups 1–2 in T3 (after fit-engine-poc groups 3–6); groups 5–7 in T3–T5. Production freeze 18 Nov 2026.

## 1. Surrogate and precompute (Python)

- [ ] 1.1 Implement a population sampler covering the supported input ranges (sex, age, height, BMI, girth deviations); verify with coverage plots saved in `engine/docs/surrogate.md`
- [ ] 1.2 Add a batch command that computes standing inputs and pose measurements for about 10k sampled bodies; verify the dataset file and its row count
- [ ] 1.3 Fit surrogate models per input set (base, +chest, +chest/waist/hip) and export them as numpy-only files; verify on held-out bodies that pose-measurement MAE ≤ 0.5 cm and recommendation agreement ≥ 95 %
- [ ] 1.4 Export the body mesh grid (594 cells) as `.glb` with pose clips, `_ZONE_JERSEY` and `_ZONE_BIB` attributes and meshopt compression; verify every file is ≤ 300 KB and loads in a Three.js test page
- [ ] 1.5 Build the garment bundle (garments, fabrics, fit ranges, version hash) and a publish script for bundle and meshes to the staging CDN; verify the URLs respond from a browser

## 2. Fit API

- [ ] 2.1 Create `api/` as a uv FastAPI project depending on `engine` without PyTorch at runtime, with `/healthz`; verify the container image builds and `/healthz` returns garment count and model version
- [ ] 2.2 Implement `POST /v1/recommendations` with the surrogate and fit computation; verify contract tests for 200, 404 `garment_not_found` and 422 `height_cm`
- [ ] 2.3 Implement `GET /v1/garments/{id}` returning public data only; verify a test that fabric curves and fit ranges are absent
- [ ] 2.4 Add version fields, the CORS allowlist and per-IP rate limiting; verify tests for the version fields, a disallowed origin and the 61st request returning 429
- [ ] 2.5 Add structured logging with a field allowlist and error-report scrubbing; verify a test that logs and error reports contain no body values
- [ ] 2.6 Run a load test (20 concurrent, 5 minutes); verify server-side p95 ≤ 300 ms and save the report in `api/docs/load-test.md`
- [ ] 2.7 Deploy the API to staging with health checks and an uptime monitor; publish the OpenAPI docs; verify `/healthz` from outside and that the monitor alerts on a stopped container

## 3. Viewer foundation (TypeScript)

- [ ] 3.1 Create the `web/` pnpm workspace and `web/viewer` (Vite, TypeScript, Preact, vitest, eslint); verify `pnpm build` and `pnpm test` pass
- [ ] 3.2 Add i18n with SK, CS and EN message files and language selection by parameter or browser; verify the `lang=sk` test and the English default
- [ ] 3.3 Add bundle budgets (80 KB initial, 250 KB 3D chunk) to the build check; verify that adding a large dependency makes the check fail

## 4. Form and consent

- [ ] 4.1 Build the body form with the same validation ranges as the API and how-to-measure help for girths; verify unit tests for required-only submit and inline errors
- [ ] 4.2 Add the privacy notice, policy link and consent checkbox; verify a test that no fetch with body data happens without consent
- [ ] 4.3 Add opt-in profile memory and "forget me", with storage access wrapped; verify tests for prefill, deletion and storage that throws

## 5. Results and 3D

- [ ] 5.1 Build the recommendation view (size label, plain-language confidence, zone explanations) against fixture responses; verify the high- and low-confidence fixtures render as specified
- [ ] 5.2 Build the Three.js scene: load the body mesh, play pose clips, orbit controls, camera presets; verify on a desktop browser and a phone
- [ ] 5.3 Color zones from statuses using the zone attributes, with legend and text labels; verify colors and labels match a fixture for every status
- [ ] 5.4 Add size and pose switching from already-loaded data; verify the update takes under 200 ms and makes no new API request
- [ ] 5.5 Implement degradation paths (no WebGL, mesh load failure, API error with retry and size-chart link); verify each by forcing the failure in a test

## 6. Modes and accessibility

- [ ] 6.1 Implement the standalone route `/fit?garment=…`; verify a shared link opens the right garment
- [ ] 6.2 Implement embedded mode with the v1 message envelope (`hello`, `ready`, `recommendation`, `select-size`, `close`) and origin checks against the allowlist; verify with a test parent page, including a disallowed origin
- [ ] 6.3 Run an accessibility pass (keyboard-only flow, labels, contrast); verify an automated axe check reports no violations and a manual keyboard run completes

## 7. Deployment and demo readiness

- [ ] 7.1 Deploy the viewer and assets to staging and production on the CDN with versioned paths; verify the flow from a phone on mobile data
- [ ] 7.2 Build the offline demo (both garments, three bodies, local assets) and record the demo video; verify the offline demo runs with the network disabled
- [ ] 7.3 Run the end-to-end check: standalone link → form → recommendation → 3D for both garments on iOS Safari and Android Chrome; verify and record results in `web/viewer/docs/e2e-check.md`
