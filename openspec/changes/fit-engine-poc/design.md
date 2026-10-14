# Design: fit-engine-poc

## Context

- Greenfield repository, no code yet. Motivation: see proposal.md (Why).
- Research constraints (see `simiq-prehlad.md`, sections 2–3):
  - Cloth-simulation pressure did not correlate with measured pressure on cycling wear.
  - Laplace's law with measured fabric stretch curves predicted pressure well.
  - SMPL-family body models are non-commercial. Anny is Apache-2.0 code with CC0 assets.
- Team of 3–4 with about five weeks to demo day. Python for the engine (Anny runs on PyTorch), TypeScript for web.
- Pilot brand is Isadore (founder ruling 2026-10-14). Until their tech packs arrive, the first garments are Isadore pieces bought and measured by the team, so the contract must accept team-measured data as well as brand tech packs.
- Fresh build (founder ruling 2026-10-14): the early-October prototype is not carried over; nothing is copied from it.
- Inputs follow the Figma onboarding flow the team designed: sex, height, weight and a body silhouette; age, region silhouettes and girths are optional.
- The niio factory rules apply (`CLAUDE.md`): constants before settings, a derivation and a hand-computed test for every formula, `engine/` is `core` radius.

## Goals / Non-Goals

**Goals:**

- Deterministic, explainable per-zone fit for tight cycling garments in riding poses.
- Reproducible from the command line: body inputs + garment file → recommendation JSON.
- An evaluation harness that produces the demo-day accuracy number honestly (out of sample, with confidence intervals).

**Non-Goals:**

- Request latency and serving (the surrogate in `tryon-viewer-mvp`).
- Loose garments (MTB jerseys, jackets). The strain model assumes the garment touches the body.
- Absolute pressure in mmHg as a shopper-facing claim.

## Decisions

### D1. Monorepo layout

```
engine/         Python package simiq_fit: body, garment, fit, calibration, CLI
api/            Python FastAPI service (tryon-viewer-mvp)
web/            TypeScript workspace: viewer/, widget/, demo-shop/, portal/ (later)
adapters/       platform apps (platform-adapters)
data/           garments/, fabrics/, poses/, fit-ranges/ (versioned, non-personal)
data/private/   fit-study data (gitignored, also kept off shared drives without access control)
docs/           guides: measuring garments, fit-study protocol, integration
```

- Python is managed with uv. `api` imports `engine` as a path dependency.
- Rejected alternative: separate repositories per component. Too much overhead for 3–4 people with shared contracts.

### D2. Body: Anny with phenotype fitting by optimization

- Inputs map to Anny phenotype parameters (sex, age, height, weight, muscle, proportions) plus local shape parameters.
- The silhouette pick sets the starting point and a prior on the muscle and proportion parameters: `slim`, `regular` and `athletic` are three fixed parameter offsets, chosen so that at equal height and weight `athletic` has the larger chest and shoulders. Region silhouettes from the Figma flow add offsets on their region's local parameters.
- Without an age the body is built for 35 years (`DEFAULT_AGE`), a constant to revisit with study data.
- The parameters are fitted by gradient descent, since Anny is differentiable in PyTorch. Loss terms:
  - height: tolerance 0.5 cm;
  - mass, computed as mesh volume × `BODY_DENSITY_KG_PER_L` = 1.03. A constant; retuning it against study participants is its own PR with before/after numbers;
  - optional chest, waist and hip girths with tolerance 1.0 cm.
- Rejected alternative: a direct regression from inputs to sliders. It is faster but less faithful when girths are given. A regression of this kind is still used later as the serving surrogate.
- Anny's optional SMPL-X topology is not used, because it is non-commercial.

### D3. Poses as versioned data

- `data/poses/{standing,hoods,drops}.json` hold joint rotations on Anny's default 104-bone rig.
- Angles start from typical bike-fit ranges and are adjusted visually.
- Every result records the pose file's version, so it can be reproduced.
- Known risk: Anny documents no pose-corrective shapes, so plain linear blend skinning may distort the hip and crotch in deep flexion. Task group 2 is a go/no-go spike. Fallbacks if it fails:
  - (a) measure on the standing body and apply pose deltas measured on the team;
  - (b) add corrective vertex offsets for the hip region.

### D4. Measurements are defined once on the template topology

- **Landmarks** are vertex indices on the Anny template (armpit, waist, hip, C7, crotch, shoulder points, elbow, knee). Anny's topology is fixed, so the same indices work for every body shape.
- **Girths** are planar cross-sections at landmark-relative heights. The value is the perimeter of the cross-section's convex hull, which is what a tape measure reads because it bridges concavities.
- **Limb profiles**: upper-arm and thigh girths every 2 cm, perpendicular to the bone axis. The engine picks the level where the garment's sleeve or leg opening sits.
- **Lengths** are surface paths between landmarks:
  - back length: C7 down to the back hip line;
  - vertical trunk girth: a closed loop over the shoulder, down the front, through the crotch and up the back. This is the body counterpart of a bib's front rise + straps + back rise.
- Rejected alternative: a learned measurement predictor. It is harder to validate against tape measurements for the PoC.

### D5. Garment and fabric contract

Pydantic models are the source of truth. JSON Schema is exported for TypeScript components. Sketch of the shape (illustrative values):

```json
{
  "schema_version": 1,
  "id": "demo-jersey-01",
  "type": "jersey",
  "brand": "demo",
  "model": "Demo Race Jersey",
  "fit_block": "race",
  "source": "team_measured",
  "zones": [
    {"id": "chest", "kind": "girth", "pom": "chest_circumference",
     "body": "chest_girth", "fabric": "main", "direction": "course", "weight": 2},
    {"id": "back_length", "kind": "length", "pom": "center_back_length",
     "body": "back_length", "fabric": "main", "direction": "wale", "weight": 1}
  ],
  "sizes": [{"label": "M", "pom": {"chest_circumference": 86.0, "center_back_length": 62.0},
             "provenance": {"by": "...", "date": "2026-10-20", "method": "flat x2"}}],
  "size_chart": [{"label": "M", "chest": [88, 92], "waist": [76, 80]}],
  "fabrics": {"main": "fabric-demo-01"}
}
```

- A fabric record has an id, composition, g/m², specimen width, method (`strip_test_weights`, `supplier_datasheet` or `lab`) and force-vs-strain curves for `course` and `wale`.
- Default zones:
  - jersey: chest, waist, hem, sleeve_opening (girth zones), back_length (length zone);
  - bib shorts: hip and leg_opening (girth zones), vertical_loop (loop zone).

### D6. Fit computation

- **Girth and loop zones:** ε = C_body / C_garment − 1.
  - If ε ≤ 0, report ease = −ε · C_garment in cm.
  - If ε > 0, tension T = F(ε) / w. F comes from the fabric curve by linear interpolation and is not extrapolated: values beyond the curve are flagged `out_of_curve`. w is the specimen width.
  - Pressure P = T / r with r = C_body / 2π (Laplace's law). It is exposed only as a value relative to other sizes.
- **Length zones:** margin = L_garment · (1 + ε_allow) − L_body. ε_allow is the strain at which the wale curve reaches `COMFORT_TENSION_N_PER_M`, one constant set from the team's own try-ons (task 6.3). A negative margin means the garment rides up or is too short.
- Rejected alternative: per-vertex cloth simulation. It is slower, harder to validate, and the evidence says it does not track real pressure.

### D7. Fit ranges per brand and fit block

- `data/fit-ranges/<brand>.json` defines, per fit block and zone, the thresholds of the ok band and the outer bands (strain for girth and loop zones, margin for length zones). `default.json` is the fallback.
- Initial values are set by hand from the team's own try-ons of the purchased garments, then fitted from study ratings (D9).
- Ranges are per brand because brands design different intended compression.

### D8. Recommendation, confidence and explanation

- **Penalty per size:** Σ weight_zone × band cost. Costs: ok 0; loose, tight, short or long 1; too_* 3.
- **Recommendation:** the lowest penalty wins. Ties go to the size closest to the ok-band centers of its weighted zones.
- **Confidence:**
  - Sample K = 64 measurement vectors around the body. The standard deviations depend on which inputs were given (body-profile).
  - Deviations in standing girths propagate to pose measurements through a Jacobian computed once per body with autograd, so each sample does not need a new body fit.
  - Confidence = share of samples whose best size equals the recommendation.
  - Alternative = the next most frequent size when confidence < `CONFIDENCE_THRESHOLD` = 0.6.
- **Explanation:** the zones whose status differs between the recommended size and its neighbors, as structured data. Wording is localized in the viewer.

### D9. Calibration and evaluation

- **Study records** (spec fit-calibration) are imported from CSV under `data/private/` with a pseudonymous ID. Names live in a separate sheet that never touches the repo.
- **Range fitting:** per zone, thresholds are chosen to maximize ordinal agreement with the ratings. Evaluation is leave-one-out, so the reported accuracy is out of sample.
- **Report** (markdown + CSV, aggregate only):
  - N and hit rate with Wilson 95 % CI;
  - hit-or-alternative rate;
  - baseline hit rate of the brand chart, both from tape girths and from girths estimated from the required inputs;
  - per-zone agreement;
  - standing-girth error with and without girth inputs, and with and without the silhouette pick;
  - predicted versus measured strain where dot-grid data exists, otherwise "unverified".
- **Dot grid (optional):** only on a garment the team owns, because the marker stays on the fabric. The extra Isadore jersey bought for strip tests gets a 3 cm dot grid first; team members wear it standing and on a trainer in `hoods`; photos with a scale reference give local strain in camera-facing zones (chest, back, upper arm). Then the jersey is cut for strip tests. Borrowed garments are never marked.

### D10. Interfaces

- **Library:** used directly by `api/` and the precompute.
- **CLI `simiq-fit`:**
  - `measure`: inputs → measurements JSON;
  - `recommend`: inputs + garment → recommendation JSON;
  - `export-mesh`: body + pose → glTF;
  - `validate-data`: checks garment and fabric files;
  - `calibrate` and `evaluate`: run on study data.
- The recommendation JSON shape is the payload that `fit-api` returns, so the CLI and the API cannot drift apart.

## Program design

File placement, the types that cross module boundaries, and the constants. Only `body.py` imports Anny or PyTorch, so the serving path in `tryon-viewer-mvp` can run without them.

```
engine/
  pyproject.toml          package simiq_fit, console script simiq-fit
  src/simiq_fit/
    inputs.py             BodyInputs + validation ranges
    body.py               build_body(inputs) -> Body          (Anny, PyTorch)
    poses.py              load_pose(name) -> Pose; POSES = ("standing", "hoods", "drops")
    landmarks.py          vertex indices on the Anny template, loaded from data/landmarks.json
    tape.py               girth(), limb_profile(), surface_path()   (pure geometry, numpy)
    measure.py            measure(body, pose) -> Measurements; measurement_sds(inputs) -> dict
    garment.py            Garment, Size, Zone, Fabric, SizeChart + load, validate, JSON Schema export
    fabric.py             tension(fabric, direction, strain) -> N/m; comfort_strain(fabric, direction)
    fit.py                zone_fit(...) -> ZoneFit; size_fit(...) -> list[ZoneFit]
    recommend.py          recommend(...) -> Recommendation
    study.py              load_study(path) -> list[Participant]; delete_participant(path, pid)
    calibrate.py          fit_ranges(participants, garment) -> FitRanges
    evaluate.py           evaluate(participants, garments) -> Report
    cli.py                measure | recommend | export-mesh | validate-data | calibrate | evaluate
  tests/                  test_<module>.py; spec scenarios as hand-computed tests
  docs/                   formulas.md (derivations), measurements.md, anny-spike.md, licenses.md
data/
  poses/  landmarks.json  garments/  fabrics/  fit-ranges/      (versioned, non-personal)
  private/                                                       (gitignored study data)
```

```python
# inputs.py
Sex = Literal["female", "male"]
Silhouette = Literal["slim", "regular", "athletic"]
class BodyInputs(BaseModel):
    sex: Sex; height_cm: float; weight_kg: float; silhouette: Silhouette
    age: int | None = None; regions: dict[str, str] = {}
    chest_cm: float | None = None; waist_cm: float | None = None; hip_cm: float | None = None

# measure.py
class Measurements(BaseModel):
    pose: str
    girths_cm: dict[str, float]               # chest_girth, waist_girth, hip_girth
    profiles_cm: dict[str, list[float]]       # upper_arm_girth, thigh_girth; 2 cm steps
    lengths_cm: dict[str, float]              # back_length, vertical_trunk_girth

# fit.py
Status = Literal["too_loose", "loose", "ok", "tight", "too_tight", "too_short", "short", "long"]
class ZoneFit(BaseModel):
    zone: str; kind: Literal["girth", "loop", "length"]; status: Status
    strain: float | None; ease_cm: float | None; margin_cm: float | None
    relative_pressure: float | None; flags: list[str]  # out_of_curve, default_ranges

# recommend.py
class Recommendation(BaseModel):
    size: str; confidence: float; alternative: str | None; pose: str
    sizes: dict[str, list[ZoneFit]]; explanation: list[tuple[str, str, Status]]  # size, zone, status
    engine_version: str; data_version: str
```

Constants (one place each, changed only by a PR with before/after evaluation numbers):

| Constant | Value | Module |
|---|---|---|
| `BODY_DENSITY_KG_PER_L` | 1.03 | body.py |
| `DEFAULT_AGE` | 35 | body.py |
| `CONFIDENCE_THRESHOLD` | 0.6 | recommend.py |
| `SAMPLES` | 64 | recommend.py |
| `BAND_COST` | ok 0, loose/tight/short/long 1, too_* 3 | recommend.py |
| `COMFORT_TENSION_N_PER_M` | set in task 6.3 from team try-ons | fabric.py |
| `PROFILE_STEP_CM` | 2 | measure.py |

## Risks / Trade-offs

- [Anny skinning artifacts at hip flexion] → spike first (tasks group 2), with the fallbacks in D3.
- [Wrong density or weight mapping biases girths] → tune on study participants; report standing-girth error.
- [Team-measured garment dimensions differ from brand points of measure] → two people measure each size; source is recorded; compare when brand data arrives.
- [Noisy curves from the DIY stretch rig] → 3 specimens per direction, averaged; spread recorded; curve quality flagged.
- [Small study gives wide confidence intervals] → report N and CIs; call it pilot evidence, not proof.
- [Thresholds overfit to few riders] → leave-one-out evaluation; few parameters per zone.
- [Personal data committed by accident] → `.gitignore` plus a pre-commit hook blocking `data/private/`.

## Migration Plan

Greenfield; nothing to migrate. Data files carry `schema_version` so later changes can migrate them.

## Open Questions

- Exact joint angles of `hoods` and `drops`. These are data files and can change without touching the specs.
- The value of `BODY_DENSITY_KG_PER_L` after the first study round (a constant; the approach does not change).
- The exact region silhouettes in the Figma flow (task 3.1 pins them into the body-profile spec; the mechanism in D2 does not change).
- Whether an aero/time-trial pose is needed. That would only add a preset file.
