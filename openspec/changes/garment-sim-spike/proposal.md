# Proposal

## Why

The product's picture is a jersey on the shopper's body, coloured where it pulls and where it bags, standing and in the riding position. Producing that picture needs a digital garment with per-panel fabric behaviour, a way to dress a body with it, and a solver that reports stretch. The team has none of these yet and cannot fund a simulation specialist, so the winter of 2026/27 is spent building the simplest credible version on Blender's scriptable cloth simulator, with the home-built solver as a later upgrade, and scoring the result against the fit lab's feel charts and dot-grid photos in spring 2027 (see `fit-lab-protocol`).

## What Changes

- Digitise one bought race-fit jersey: flat measurements per size, panel layout as a parametric template, and fabric stretch measured on a hanging-weight strip rig.
- Dress the body produced by `body-model-spike` with that jersey in Blender, headless, in the standing and riding poses, and read per-vertex stretch relative to the fabric's comfortable range.
- Define the garment representation that accepts a pattern file (CLO or DXF), a spec sheet, or a physical garment, all converging on the same template plus measurements plus fabric form.
- Start a fabric library: measured warp and weft stretch curves for the fabrics encountered, keyed by mill and fabric name where known.
- Prove the precompute shape: batch bodies x sizes x poses, store strain arrays, blend nearest neighbours for a new body, display in a three.js viewer in milliseconds.
- Self-check before the lab: dot grid drawn on the bought jersey, worn by the founders, photographed standing and on a trainer, compared with the simulated stretch.
- Time-box a home-built XPBD solver as a parallel learning track; it replaces Blender only when it matches the dot grid at least as well.

Out of scope: the shopper widget, shop integration, textured rendering of prints and colours, loose or draping garments, and photo-based body capture.

## Capabilities

### New Capabilities

- `garment-digital-twin`: representing a garment as panels with seams, sizes with per-size measurements, and a fabric per panel, created from a pattern file, a spec sheet, or a measured physical garment, all resolving to the same internal form.
- `fabric-library`: storing measured stretch behaviour of fabrics (elongation under load in warp and weft, comfortable stretch range, recovery), keyed so that a fabric measured once serves every garment that uses it.
- `fit-simulation`: computing, for a body in a pose and a garment size, where the garment is tighter or looser than the designer intended, and serving that for an arbitrary shopper body in milliseconds by blending precomputed results across a sampled grid of bodies.

### Modified Capabilities

None.

## Impact

- New dependencies: Blender (headless, run as a separate process from any Rails code to stay clear of its GPL licence), a physical stretch rig built from a clamp, weights and a ruler, and one jersey bought in all sizes (the same one the fit lab uses).
- Depends on the body contract from `body-model-spike`; can start on a hand-exported body before that pipeline is complete.
- Scored by `fit-accuracy-evaluation` from `fit-lab-protocol`: per-zone agreement with rider feel charts, stretch versus dot-grid photos, and size verdict accuracy against the brand size chart.
- Team learning: Blender cloth and sewing, headless Blender scripting, position-based dynamics, fabric mechanics basics.
