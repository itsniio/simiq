# Design: tryon-viewer-mvp

## Context

- Builds on `fit-engine-poc`, the Python library with the body-profile, garment-model and fit-engine capabilities.
- Fitting an Anny body takes seconds and needs PyTorch, which is too slow and too heavy for a request path.
- Demo day (20 Nov 2026) needs a live demo on phones and laptops, and a fallback if the venue network fails.
- The first-brand decision (D2C e-shop or team-kit maker) is not made yet, so the viewer must serve both a shareable link and an e-shop modal.

## Goals / Non-Goals

**Goals:**

- API p95 ≤ 300 ms server-side. The API container does not include PyTorch.
- Viewer usable on a mid-range phone over 4G.
- One viewer codebase for standalone and embedded use.

**Non-Goals:**

- Accounts or any server-side storage of body profiles.
- Cloth-simulated garment visuals. Zones are painted on the body, which fits tight cycling wear.
- Photo input and a fit-preference toggle.
- Analytics events (`pilot-analytics`).

## Decisions

### D1. Surrogate measurement model instead of running Anny online

**Offline:**
- Sample about 10k Anny bodies covering the supported input ranges.
- For each body, compute its standing inputs (height, mass, chest, waist and hip girths) and all pose measurements.
- Fit a regression per input set: base, base + chest, base + chest + waist + hip. Missing girths in other combinations are filled in by the base model.
- Start with ridge regression on polynomial features. Move to a small MLP only if the acceptance threshold fails.
- The residual spread of the base model, floored by the body-profile default SDs, feeds the confidence sampling.

**Online:** load the model files (numpy only), predict pose measurements, and run the fit-engine computation (pure Python/numpy).

**Acceptance:**
- pose-measurement MAE ≤ 0.5 cm against the direct pipeline;
- recommendation agreement ≥ 95 % on held-out bodies.

**Rejected alternatives:**
- Run Anny per request with caching: seconds of latency and a large container.
- Precomputed lookup grid of measurements: combinatorial explosion once optional girths are included.

### D2. Body mesh grid for visuals

- **Grid:** sex (2) × age band (3) × height 150–200 cm in 5 cm steps × BMI 18–34 in steps of 2. That is 594 cells.
- **File per cell:** one `.glb` with:
  - a skinned mesh;
  - animation clips `standing`, `hoods` and `drops`;
  - per-vertex zone attributes `_ZONE_JERSEY` and `_ZONE_BIB` mapping vertices to fit zones;
  - meshopt compression, target ≤ 300 KB.
- **Publishing:** files go to `cdn/bodies/v<n>/<cell>.glb`. The API returns the nearest cell's URL, and the viewer scales the mesh to the exact height.
- The mesh is illustrative. The numbers come from the API.
- **Rejected alternatives:**
  - per-user mesh generation: latency and cost;
  - one file with morph targets: larger first download, revisit later.

### D3. API shape

- **Framework:** FastAPI, stateless.
- **Endpoints:** `POST /v1/recommendations`, `GET /v1/garments/{id}`, `GET /healthz`.
- **Garment bundle:** garments, fabrics and fit ranges are built from `data/` into a bundle with a version hash. The API loads it at startup and hot-reloads it on a version change.
- **Request:**
  `{garment_id, body: {sex, height_cm, weight_kg, silhouette, age?, regions?, chest_cm?, waist_cm?, hip_cm?}, pose?, lang?}`
  — the body object is `BodyInputs` from `fit-engine-poc`, exported as JSON Schema for the viewer.
- **Response:** the CLI recommendation JSON plus `body_mesh_url`, `engine_version`, `model_version` and `bundle_version`.
- **Logging:** structured, with an allowlist of fields; body values are never in the allowlist. Error reporting strips request bodies.
- **Access:** CORS allowlist of viewer origins. Rate limit is a token bucket per IP, 60/min (`RATE_LIMIT_PER_MIN`), behind the CDN or proxy.

### D4. Viewer stack

- **Build and UI:** Vite + TypeScript with Preact for the form and results. The initial bundle stays small.
- **3D:** Three.js in a code-split chunk that loads only after the form is submitted.
- **Layout and onboarding:** the Figma frames in D4b, read through the Figma MCP (never redrawn by eye).
- **Colors:** design tokens in `web/viewer/src/tokens.css`, taken from the Figma variables; a lint fails on raw hex anywhere else. Fit statuses use a diverging scale (blue = loose, neutral = ok, red = tight), and every status also gets a text label and pattern, so color is never the only cue.
- **Languages:** SK, CS and EN via JSON message files; a test fails on any user-facing string outside them. Wording for explanations is generated from zone + status + language templates.

### D4b. The Figma design is the UI contract

File NIIO (`nmFcu26FyE2mqlIGnJJ9Vh`), page `simik` (node `211:1083`). Read each frame through the Figma MCP when building its component; never redraw by eye.

| Part | Node | Variants |
|---|---|---|
| Desktop layout | `473:3` | left sidebar, middle, right sidebar |
| Left sidebar (onboarding) | `478:1204` | step 1 `478:1203`, step 2 `478:1202`, step 3 `478:1201`, folded `478:1200` |
| Middle (3D) | `485:751` | standing `485:750`, bike `485:749` |
| Right sidebar (products) | `483:646` | list `483:645`, detail `483:644`, folded `483:643` |
| Components | | sex bar `473:175`, type pick box `478:965`, measurement lists `474:591`, `474:641`, button `473:244`, tag `483:401`, step bullet `473:126`, check box `473:152` |

Copy is Slovak in the frames; English and Czech strings are translations of it. Older wireframes on the same page (frames `385:51`, `386:59`, `389:136`, `390:456`, `390:689`) are superseded by the frames above.

Not designed yet, and decided here until the designer delivers frames: narrow screens stack left panel, 3D and products; the embedded modal shows the same studio with the shop's product already tried on (the page notes an embed frame "do budúcna").

Catalog data: garments and their display data come from `GET /v1/garments`; price, currency and product link come from the shop manifest (`shop-embed`), so standalone without a shop shows no prices.

### D5. Modes and messaging

- **Standalone:** `/fit?garment=<id>&lang=<xx>` opens the studio with that garment selected (the shareable link); `/fit` opens it on the catalog.
- **Embedded:** `/fit?embed=1&shop=<key>&garment=<id>`.
  - The viewer reads the shop manifest (from `shop-embed`) for allowed parent origins and size labels.
  - It accepts a `hello` only from an allowed origin.
- **Message envelope:** `{source: "simiq", v: 1, type, payload}`.
  - Viewer → parent: `ready`, `recommendation`, `select-size`, `close`.
  - Parent → viewer: `hello`.
- Until `shop-embed-mvp` lands, a configured allowlist stands in for the manifest.

### D6. Profile on the device only

- The profile is stored in `localStorage` only after opt-in, and every access is wrapped in try/catch.
- Inside an iframe the storage is partitioned per shop. That is acceptable and matches the GDPR stance of one profile per shop and device.
- A "forget me" control clears the profile.

### D7. Hosting

- **Static assets** (viewer, meshes, garment bundle): object storage + CDN, with versioned paths and long cache. HTML uses a short cache.
- **API:** one container on a small VM or PaaS, with health checks and an uptime monitor.
- **Environments:** `staging` and `production`. Production is the demo-day environment and is frozen on 18 Nov.

### D8. Demo-day fallback

- An offline build of the viewer with the two garments and three bundled bodies, served from a laptop.
- A recorded demo video.

## Program design

```
engine/src/simiq_fit/
  surrogate.py        sample_population(n) -> bodies; fit_surrogate(dataset) -> files;
                      predict(inputs) -> Measurements + sds       (numpy only, no PyTorch)
  meshgrid.py         export_grid(out_dir) -> 594 .glb files      (offline, uses body.py)
  bundle.py           build_bundle(data_dir) -> bundle.json + version hash
api/
  pyproject.toml      depends on engine without the anny/torch extra
  src/simiq_api/
    app.py            FastAPI app: /healthz, /v1/recommendations, /v1/garments/{id};
                      CORS allowlist, rate limit, logging allowlist
  tests/              contract tests per spec scenario; load test script in api/docs/
web/
  package.json        pnpm workspace
  viewer/src/
    main.tsx          route: /fit (standalone or ?embed=1); the three-area layout of 473:3
    onboarding/       one component per Figma step (478:1203, 478:1202, 478:1201);
                      validation shared with the API's ranges
    products/         list (483:645) with search and category filters; detail (483:644)
    result/           recommended size, confidence, zone list, size and pose switch
    scene/            Three.js scene, bike control, part highlight; a separate chunk
    embed.ts          postMessage v1: hello, ready, recommendation, select-size, close
    api.ts            postRecommendation(), getGarment()
    i18n.ts + locales/{sk,cs,en}.json
    tokens.css
```

Types shared across the boundary come from one source: the API's OpenAPI document generates `web/viewer/src/api-types.ts`, so the viewer never hand-writes the response shape.

Constants: `RATE_LIMIT_PER_MIN = 60`, `GRID` (sex × 3 age bands × height 150–200 / 5 × BMI 18–34 / 2), budgets 80 KB / 250 KB / 300 KB.

## Risks / Trade-offs

- [Surrogate error near the edges of the input ranges] → held-out tests per region; inputs outside the training coverage are rejected by validation.
- [Nearest-cell mesh looks different from the shopper] → scale to exact height, label it "illustrative body", keep the numbers authoritative.
- [WebGL missing or low-end phone] → text-only result path; capped pixel ratio; meshopt.
- [API outage on demo day] → offline fallback (D8) and the production freeze.
- [Color-only communication excludes color-blind users] → labels and patterns (spec requirement).

## Migration Plan

Greenfield deploy. Releases are rolled back by redeploying the previous container tag and repointing the static `latest` path; versioned asset paths are never overwritten.

## Open Questions

- API host provider (any container host works; the choice changes neither specs nor tasks).
- Exact color palette values.
