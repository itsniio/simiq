# Tasks

## 1. Tools and learning

- [x] 1.1 Install Blender and run a cloth simulation from a headless Python script on a sphere collider; verify the script runs without a UI and writes the deformed mesh to a file
- [x] 1.2 Reproduce Blender's pattern sewing on a two-panel tube around a cylinder; verify the panels pull together and settle without interpenetration, and save a screenshot
- [x] 1.3 Work through the Ten Minute Physics cloth tutorials and run the resulting JavaScript cloth in a browser; verify a hanging cloth with stretch constraints simulates stably (this starts the XPBD track)

## 2. Physical garment and fabric rig

- [ ] 2.1 Buy the primary jersey in all sizes (shared with the fit lab) plus one extra size M to cut; verify all are logged in the garment record
- [ ] 2.2 Flat-measure every size per the points-of-measure list; verify every size has all measurements and grading is monotonic
- [ ] 2.3 Build the strip rig (clamp, ruler, set of weights) and write the measurement procedure; verify two people measure the same strip and agree within 10 percent elongation at every load
- [ ] 2.4 Cut strips from the extra jersey for each distinct fabric and measure warp and weft elongation at three or more loads plus recovery; verify fabric library entries exist with method "strip" and monotonic curves

## 3. Fabric library and garment form

- [x] 3.1 Implement the fabric library (entries, curves, comfortable range, fidelity, versioning) per the fabric-library spec; verify tests for rejected non-monotonic curves, derived ranges, and version retention
- [x] 3.2 Implement the garment form (panels, seams, size run, fabric per panel with warp direction, intent, rest-state dimensions, provenance) per the garment-digital-twin spec; verify tests for grading rejection, missing fabric flag, and default intent flag
- [x] 3.3 Implement the parametric jersey template with set-in and raglan archetypes, with and without side panels, driven by points of measure; verify a test generates panels for every size of the bought jersey and the panel dimensions match the flat measurements within 1 cm
- [ ] 3.4 Digitise the bought jersey as tier C using 2.2 and 2.4; verify the garment is marked simulatable with provenance "physical"
- [x] 3.5 Implement a DXF pattern import proof that reads panel outlines from a sample DXF into the garment form; verify a test imports a hand-made two-panel DXF with the expected piece count

## 4. Blender dressing and strain

- [x] 4.1 Write the headless Blender script that takes a body mesh from the body contract, a garment size, and a pose, sews the panels on from an inflated start, and settles; verify it produces a draped mesh on the standing body without interpenetration beyond 2 mm
- [x] 4.2 Extract per-triangle stretch ratios in warp and weft against the rest-state panels and classify per vertex against the fabric's comfortable range; verify a test on a synthetic stretched quad returns the known ratio and class
- [x] 4.3 Calibrate solver stiffness per fabric by simulating a strip under the library's load points; verify each simulated elongation is within 10 percent of the measured curve and the fabric is marked calibrated
- [ ] 4.4 Run dressing in the riding pose and tune friction so the back lengthens; verify the back hem moves upward relative to the waist landmark compared with standing, and record the amount
- [x] 4.5 Mark non-converging or interpenetrating cases as failed with a reason; verify a test with a deliberately undersized garment produces a failed result, not a stored one
- [x] 4.6 Compute the zone summary (eight zones) and hem positions (back hem versus waist, sleeve hem versus elbow) in centimetres; verify a test on a known draped mesh reports the expected hem offsets

## 5. Size verdict

- [x] 5.1 Implement the size verdict across all sizes using zone classes and the shopper's fit preference, with per-zone reasons and an "equally acceptable" case; verify tests for a clear verdict and for a preference that changes it
- [x] 5.2 Implement the standing versus riding comparison per zone; verify a test lists zones whose class differs between poses

## 6. Precompute and serving

- [x] 6.1 Sample a small body grid (tens of bodies) in shape parameter space stratified to include tall-thin and short-broad; verify the sampled set includes bodies at the extremes of height and chest
- [x] 6.2 Build a batch runner (Rails job or script) that invokes Blender as a separate process per body, size, and pose and stores draped meshes and strain arrays with solver, garment, and fabric versions; verify a run over the grid reports counts of succeeded and failed cases
- [x] 6.3 Implement nearest-neighbour blending of strain arrays for a body not in the grid, with a confidence from neighbour distance and a low-confidence flag; verify a test that a grid body blended from its neighbours differs from its direct result by less than a set tolerance
- [x] 6.4 Serve a blended result through a small endpoint and display it in the three.js viewer with per-vertex colour, pose toggle, and size switch; verify a request completes in under 500 milliseconds server time and the viewer shows the colours
- [ ] 6.5 Hand the viewer to the designer for the result screen; verify the designer can switch bodies, sizes, and poses without developer help

## 7. Self-check before the lab

- [ ] 7.1 Draw the lab's 3 cm dot grid on one jersey in two sizes and photograph each flat with a scale reference; verify rest-state photos are stored
- [ ] 7.2 Photograph both founders in both sizes, standing and on a trainer, front, side, and back; verify every photo is labelled with person, size, pose, and view
- [ ] 7.3 Write the dot-grid stretch extraction script (dot spacing versus rest spacing per zone in camera-facing areas); verify it reproduces a known stretch on a photographed test grid stretched by a measured amount
- [ ] 7.4 Compare simulated stretch with dot-grid stretch per zone for the founders; verify a comparison table is saved and disagreements are logged as solver issues

## 8. Lab scoring

- [x] 8.1 Write the scoring script that reads the lab dataset export and reports zone agreement with feel charts, stretch versus dot grid, and size verdict accuracy against the chart baseline, per the fit-accuracy-evaluation spec; verify it runs on a synthetic dataset with known answers
- [ ] 8.2 After the lab, run the scoring on real data; verify the report is saved with rider count, exclusions, and the chart baseline side by side

## 9. XPBD track (time-boxed to end of January 2027)

- [x] 9.1 Implement an XPBD membrane solver with anisotropic stretch constraints, seam constraints, and body collision with friction in Python; verify it dresses the tier C jersey on the standing body without exploding
- [ ] 9.2 Run the solver through the strip calibration and the founders' dot-grid comparison; verify a table compares it with the Blender results zone by zone
- [x] 9.3 Record the time-box decision: XPBD replaces Blender behind the same inputs and outputs only if it matches the dot grid at least as well; verify the decision note is saved with the comparison table
