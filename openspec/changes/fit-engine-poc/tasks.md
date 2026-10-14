# Tasks

Target: groups 1–2 in T1–T2, groups 3–5 by end of T2, groups 6–7 in T3, group 8 in T4–T5 (fit study rounds). See README.md for dates. Fresh build: nothing is copied from the early-October prototype. Every formula lands with its derivation in `engine/docs/formulas.md` and a test whose numbers were computed by hand.

## 1. Repository setup

- [x] 1.1 (#2) Initialize git, add root `.gitignore` (including `data/private/`, build outputs, `.venv/`) and push to the team's remote; verify `git status` is clean after the first commit
- [ ] 1.2 (#3) Create `engine/` as a uv project (Python 3.12) with pytest and ruff, package `simiq_fit`, and add an `engine` job to `.github/workflows/ci.yml` (pytest, ruff, pip-audit, product-code size report against the 6,000-line soft target); verify the job runs green on a PR
- [ ] 1.3 (#4) Add a pre-commit hook that blocks any staged file under `data/private/`; verify that staging a dummy private file makes the commit fail with an explanatory message

## 2. Anny spike (go/no-go)

- [ ] 2.1 (#5) Install Anny, build a body from phenotype parameters and export it as glTF; verify the file opens in a glTF viewer
- [ ] 2.2 (#6) Draft pose files `data/poses/standing.json`, `hoods.json`, `drops.json`; verify the posed meshes render for 5 different body shapes
- [ ] 2.3 (#7) Inspect hip, crotch and shoulder deformation in `hoods` and `drops` on those 5 shapes and write `engine/docs/anny-spike.md` with screenshots and an explicit go/no-go (or fallback from design D3); verify the team has signed off on the decision
- [ ] 2.4 (#8) Record the license of every Anny asset and dependency used in `engine/docs/licenses.md` and confirm no SMPL-derived topology is loaded; verify by a test that fails if the SMPL-X topology option is enabled

## 3. Body profile

- [ ] 3.1 (#9) Pin with the designer how each step-3 measurement is taken (the Figma "i" texts) and its range, into design D2 and `engine/docs/measurements.md`; verify `openspec validate --all --strict` passes and the designer confirms the definitions
- [ ] 3.2 (#10) Implement `BodyInputs` and validation ranges (height, weight, age, BMI, step-3 measurements, types); verify unit tests for every range edge, the height 150 / weight 150 case and the `stocky` case
- [ ] 3.3 (#11) Implement body type and arm, torso and leg type offsets as constants on the shape parameters, and `other` built as `male`; verify the body-type, region-type and sex-other scenarios
- [ ] 3.4 (#12) Implement phenotype fitting to height and mass with `BODY_DENSITY_KG_PER_L` and `DEFAULT_AGE`, and write the derivation in `engine/docs/formulas.md`; verify on 20 random valid inputs that height is within 0.5 cm and mass within 2 %
- [ ] 3.5 (#13) Add the step-3 measurements as optional targets of the fit, each measured on the mesh as defined in 3.1; verify every given measurement lands within 1.0 cm on test cases
- [ ] 3.6 (#14) Apply pose presets from `data/poses/`; verify that an unknown pose returns an error listing available poses
- [ ] 3.7 (#15) Add a determinism test; verify two runs of the same request give identical measurements within 0.1 mm

## 4. Measurements

- [ ] 4.1 (#16) Mark landmarks on the Anny template and store them in `data/landmarks.json`; verify by rendering landmark positions on 5 body shapes (screenshots in `engine/docs/measurements.md`)
- [ ] 4.2 (#17) Implement tape-style girths (convex hull perimeter of a planar section); verify against analytic cylinder and ellipse meshes within 1 mm
- [ ] 4.3 (#18) Implement upper-arm and thigh girth profiles in `PROFILE_STEP_CM` steps with interpolation; verify lookup and interpolation tests on a synthetic tapered limb
- [ ] 4.4 (#19) Implement back length and vertical trunk girth as surface paths; verify back length in `hoods` exceeds `standing` on 10 body shapes
- [ ] 4.5 (#20) Implement per-measurement standard deviations by input set as constants with their sources noted; verify chest SD is smaller when chest girth is given
- [ ] 4.6 (#21) Document every measurement definition with a figure in `engine/docs/measurements.md`; verify each body-profile measurement has an entry

## 5. Garment and fabric data

- [ ] 5.1 (#22) Implement garment and fabric models with validation and JSON Schema export (`simiq-fit validate-data`); verify example records pass and broken examples fail naming the field
- [ ] 5.2 (#23) Create jersey and bib-shorts templates with the default zones; verify the template-zone scenarios
- [ ] 5.3 (#24) Write `docs/garment-measuring.md` (lay flat, which points of measure, two measurers, doubling flat circumferences); verify a second team member can measure one size from it and lands within 0.5 cm of the first
- [ ] 5.4 (#25) Measure the purchased Isadore jersey and bib shorts in every size (two people) and add `data/garments/*.json`; verify `validate-data` passes and grading warnings are reviewed
- [ ] 5.5 (#26) Build the strip-test rig (weights or force gauge, 50 mm specimens) and measure course and wale curves with 3 specimens per direction from the extra owned jersey, after its dot-grid photos (8.5) if those are taken; add `data/fabrics/*.json` and curve plots in `docs/`; verify `validate-data` passes
- [ ] 5.6 (#27) Enter Isadore's published size chart for both garments; verify the chart-lookup scenarios

## 6. Fit computation

- [ ] 6.1 (#28) Implement strain and ease for girth and loop zones with their derivation in `formulas.md`; verify the 96/84 cm (14.3 %) and 80/84 cm (−4.8 %, 4.0 cm) scenarios
- [ ] 6.2 (#29) Implement tension from fabric curves and relative pressure (Laplace's law) with the `out_of_curve` flag and derivation; verify the M-vs-L pressure ordering and out-of-curve tests
- [ ] 6.3 (#30) Set `COMFORT_TENSION_N_PER_M` from the team's own try-ons (recorded in `formulas.md`) and implement length margin; verify the back-length scenario (+1.0 cm, `ok`)
- [ ] 6.4 (#31) Implement fit-range loading with fallback to `data/fit-ranges/default.json`, and set initial ranges by hand from the team's try-ons; verify status tests and the `default_ranges` flag
- [ ] 6.5 (#32) Add a performance test; verify 5 sizes from precomputed measurements take under 50 ms

## 7. Recommendation and CLI

- [ ] 7.1 (#33) Implement weighted penalty (`BAND_COST`), tie-break and explanation with derivation; verify the clear-case and explanation scenarios
- [ ] 7.2 (#34) Implement confidence by sampling (`SAMPLES`, `CONFIDENCE_THRESHOLD`) with a Jacobian from standing girths to pose measurements; verify the borderline (< 0.6 with alternative) and clear (≥ 0.8) scenarios
- [ ] 7.3 (#35) Implement the `simiq-fit` CLI commands `measure`, `recommend` and `export-mesh`; verify the examples in `engine/README.md` run as written
- [ ] 7.4 (#36) Run a team sanity check: predictions for every team member who tried the garments, compared with how they felt; record in `engine/docs/sanity-check.md`; verify obvious mismatches have an explanation or a fix

## 8. Calibration and evaluation

- [ ] 8.1 (#37) Implement study CSV import with consent check, self-reported inputs stored apart from tape measurements; verify the missing-consent rejection scenario
- [ ] 8.2 (#38) Implement deletion by pseudonymous id with regeneration of outputs; verify the P07 deletion scenario
- [ ] 8.3 (#39) Implement range calibration with versioned output including the dataset hash; verify the output file contents
- [ ] 8.4 (#40) Implement the evaluation report (hit rates, two baselines, per-zone agreement, girth error, silhouette ablation, strain comparison or "unverified", Wilson 95 % CIs, leave-one-out); verify on a synthetic study with a known answer
- [ ] 8.5 (#41) (Optional, owned jersey only) Draw a 3 cm dot grid on the extra Isadore jersey, photograph it flat and worn (standing, `hoods`) with a scale reference, and write the strain extraction script; verify the script reproduces a known stretch on a test grid stretched by a measured amount
- [ ] 8.6 (#42) Run calibration and evaluation after study round 1 and round 2; publish aggregate-only reports in `docs/results/`; verify N and CIs are present and no row-level data is included

## 9. Integration check

- [ ] 9.1 (#43) Add an end-to-end golden test: inputs → body → measurements → recommendation for both garments in `standing` and `hoods`; verify it passes in CI
