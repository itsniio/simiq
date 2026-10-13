# Design

## Context

See proposal.md for motivation. Constraints:

- Two Rails developers learning simulation from scratch, evenings and weekends, no budget for a specialist. Outside eyes come from a thesis student with a supervisor and, if found, an advisor for equity.
- Tight race-fit garments only. The fabric is under tension everywhere and follows the body, so stretch (membrane strain) is the quantity of interest; drape, wrinkles and bending are not.
- Brands may supply CLO or DXF patterns, a spec sheet of points of measure, or nothing. The product must work from any of the three.
- All physics runs offline in batch jobs. The browser only ever loads a small mesh with per-vertex classes. The body mesh has fixed topology (see `body-model-spike`), which makes blending across bodies trivial.
- The fit lab in spring 2027 is the only external ground truth; before it, the founders' own dot-grid photos are the only check.

## Goals / Non-Goals

**Goals:**

- A coloured jersey on a posed body by the end of January 2027, in Blender, from a bought and measured garment.
- A garment form that accepts all three brand input tiers and resolves to template plus measurements plus fabric.
- A fabric stretch number that comes from a physical measurement, not a guess.
- A working precompute-and-blend path with a viewer, so the designer can build the result screen on real data before the lab.
- A scoring script against the lab's feel charts and dot grid, shared with `fit-accuracy-evaluation`.

**Non-Goals:**

- Physical accuracy beyond what the lab can measure. If the picture agrees with riders, it is good enough for v1.
- Simulating loose fit well. Below-intended tension is reported as loose; how the fabric actually drapes there is not modelled.
- Prints, colours, textured rendering. Blender can render them for the sales deck but it is not part of the spike's output.
- A production-quality home-built solver. It is a learning track with a time box.

## Decisions

### Blender headless is the v1 solver; a home-built XPBD solver is a time-boxed upgrade track

Blender has cloth with stretch stiffness, sewing springs that pull flat panels onto a body, collision with a collider mesh, and a Python API that runs without a UI. That covers dressing, which is the hardest practical step, and it is learnable by web developers. It is not calibrated to real fabric mechanics; stiffness is hand-tuned until a strip in the simulator elongates like the strip on the rig. It runs only inside batch jobs, invoked as a separate process so Rails never links to it.

The XPBD track (position-based dynamics with compliance, following Müller and Macklin) is written in parallel as a learning exercise, starting from the Ten Minute Physics cloth tutorials. It replaces Blender in the pipeline only when it matches the founders' dot-grid photos at least as well as Blender does. If that has not happened by the end of January, Blender carries the lab and the XPBD track continues without deadline pressure.

Alternative considered: writing the XPBD solver first. Rejected; dressing and collision tuning without a reference implementation is where beginners lose months, and Blender provides that reference for free.

Alternative considered: a commercial simulation API. None exists at consumer scale for this; CLO and Browzwear are designer desktop tools.

### One garment form, three input tiers

```
  tier A  pattern file (CLO export / DXF-AAMA) + bill of materials
          -> exact panels and seams; fabric per panel from the BOM
  tier B  spec sheet (points of measure per size) + fabric names
          -> template jersey panels resized to match the spec
  tier C  physical garment only
          -> flat-measure it like a spec sheet; cut a strip for the rig;
             then as tier B
```

The template is a parametric short-sleeve jersey: front panel, back panel, two side panels, two sleeves, collar, with a few archetype variants (raglan versus set-in sleeve, with or without side panels). Its dimensions are driven by the same points of measure a spec sheet lists (chest half width, body length front and back, sleeve length, sleeve opening, hem width). Tier A bypasses the template; tiers B and C are the same code path. The spike implements tier C end to end on the bought jersey and tier A as a DXF import proof only.

Alternative considered: requiring patterns from brands. Rejected; it would make the pilot depend on brand cooperation and would exclude every brand that designs on paper.

### Fabric stretch comes from a hanging-weight strip rig

A fabric strip of known width and gauge length clamped at the top, weights hung at the bottom in steps, elongation read against a ruler, in warp and in weft, with recovery noted after unloading. The result is an elongation-versus-load curve per direction. The fabric library stores the curve, the fabric's comfortable range (the elongation at which the garment is designed to sit, read from the curve's knee and from the brand's intent where known), and the mill and fabric name where identifiable. Solver stiffness is tuned so a simulated strip follows the measured curve.

Alternative considered: a commercial fabric test kit. Deferred; the rig costs almost nothing and the kit becomes worthwhile only once a brand supplies fabrics in volume.

### Strain is reported per vertex as a class relative to designer intent

For each triangle, the stretch ratio versus the flat rest shape in the panel's warp and weft directions. Per vertex, averaged, then classified against the fabric's comfortable range into tight, as designed, loose, with the numeric ratio kept for hover tooltips. "As designed" rather than "zero strain" is the reference, because a race jersey is meant to be stretched; the result screen must never read a correctly tight race fit as a defect.

### Precompute grid and blending

Bodies are sampled in the body model's shape parameter space, stratified to cover tall-thin and short-broad, not uniformly. For each body x garment size x pose the solver stores the draped garment mesh and the per-vertex strain class and ratio, compressed. For a new shopper body, the k nearest sampled bodies by parameter distance are blended by inverse distance, which is valid because every garment mesh instance shares topology. The spike proves this with a small grid (tens of bodies) and a three.js page; the lab's riders, each simulated directly and also blended from neighbours, tell how dense the grid must be.

Alternative considered: simulating on demand per shopper. Rejected; seconds of GPU per request on a product page is neither fast nor cheap, and the grid makes the result deterministic and cacheable.

### Self-check before the lab

The bought jersey gets the lab's dot grid. The founders wear it, photographed standing and on a trainer with a scale reference, in two sizes each. Local stretch from dot spacing is compared with the simulated stretch in the same zones. This is the only truth available before spring and is run every time the solver or the calibration changes.

### Deliverables of the spike

1. Garment form and a tier C digitisation of the bought jersey, all sizes.
2. Fabric library with the jersey's fabrics measured on the rig.
3. Headless Blender script: body mesh + garment + pose in, draped mesh + strain out.
4. Precompute runner over a small body grid; blended result served to a three.js viewer.
5. Dot-grid comparison script and the founders' own comparison results.
6. Scoring script for the lab data: per-zone agreement with feel charts, stretch versus grid, size verdict versus chart and versus rider choice.
7. XPBD learning track with its own dot-grid comparison, status recorded at the January time box.

## Risks / Trade-offs

- [Blender's cloth is not physically calibrated and may be wrong in a way that still looks plausible] → the strip-in-simulator versus strip-on-rig calibration, the founders' dot-grid check, and the lab's feel charts are three independent checks; any disagreement is treated as a solver problem, not a data problem.
- [Dressing fails or explodes for some body and size combinations in batch] → sewing-spring dressing from an inflated start is the robust path; failed cases are logged per body id and excluded from blending rather than silently stored.
- [Riding pose makes the fabric slide unrealistically because friction is untuned] → friction is tuned against the back-lengthening visible in the on-bike dot-grid photos; if Blender cannot reproduce it, that is the strongest argument for the XPBD track.
- [The template cannot represent a brand's panel layout] → add archetypes as encountered; a brand with an unusual layout is a tier A candidate.
- [Fabric strips cannot be cut from a garment the brand lends] → measure stretch in place with a clamp on the whole panel, lower fidelity, recorded as such in the library.
- [The team spends the winter on the XPBD solver instead of the pipeline] → the time box is explicit and the Blender path must be whole first; the solver is a swap-in behind the same inputs and outputs.
- [Blending across neighbours smears a tight zone that only exists for one body shape] → the lab riders simulated both directly and by blending quantify this; grid density or a smarter interpolation is the response.

## Open Questions

- Whether side panels in the bought jersey use a different fabric from the front; determines whether the first fabric library has one entry or two. Known on unboxing.
- How the tooltip number should be expressed to shoppers, as a percentage of stretch or as a plain "tight here". A result screen decision for the designer, not a solver decision.
- Whether the thesis topic is pitched as the solver, the calibration, or the evaluation. Any of the three helps.
