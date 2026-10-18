# Cloth-sim spike

Working notes and, at the end of the time box, the go/no-go report for `openspec/changes/cloth-sim-spike`.

## Reference data from CLO (tasks 1.1, 1.2), 16 Oct 2026

The RenderHub demo jersey draped by CLO on four Anny bodies in three poses and three sizes: 36 cases plus the starting drape (178/75 `standing` M, frame 0). Nothing of it is in git; it lives in `$SIMIQ_SPIKE_DIR` (default `~/Documents/SIMIQ/mens cycling jersey-green printed/simiq-anny/spike/`):

- `cases/garment-uv.obj`: the garment mesh with its UV layout (88,369 vertices, 149,894 faces), identical in all nine runs;
- `cases/<pose>-<size>.npz`: garment vertex positions in mm, CLO frame (Y up), one array per body;
- `cases/manifest.json`: per case the pose, body, size, source frame and how much the garment still moved over the 10 frames before it.

How they were made: the three CLO projects of the demo (`simiq-anny-{standing,body,drops}-sequence.zprj`) already hold the M animation of `standing` and `hoods`. For S and L, and for M in `drops`, `jersey-demo/scripts/clo_spike_export.py` scales every pattern piece's course (width) shrinkage by 68.5/72 or 75.5/72, the animation is recorded again, and the FBX export writes the mesh and a Maya cache of all frames; `engine/scripts/clo_cache_extract.py` keeps the mid-hold frame of each body. The drops project's own M animation (drops, then back to standing, 915 frames) put the garment 113–122 mm (mean per vertex) away from where the script's S recording has it, on every body, so drops M was recorded again by the script, to frame 465 like S and L; the new M lies 6–7 mm from S.

Found on the way:

- CLO's OBJ/GLB export ignores the animation frame (it always writes the garment's base state); only the FBX export with a cloth cache carries the frames. The OBJ it writes alongside is frame 0, in the same vertex order as the cache.
- Course shrinkage is 75 % on one piece and 72 % on the other fourteen, not 72 % everywhere. Sizes scale each piece's own value.
- On a tight jersey the sizes barely change the garment's shape: chest girths of S, M and L on the same body agree within 0.1 cm in most bands, because the fabric lies on the body. The size shows up in strain (same length, shorter rest length), so the comparison has to be made on strain, not on positions.
- Settling: the largest movement over 10 frames before a case is 5–11 mm for every M, standing and hoods run (one vertex; the share above 5 mm was not recorded for those). The first recording of drops S had not settled (up to 81 mm) and was recorded again: now the 99th percentile is 1–3 mm. The re-recorded drops M: largest movement 5–16 mm, 99th percentile 1.0–1.7 mm, at most 0.03 % of vertices above 5 mm. Drops L moves up to 31 mm at the collar and shoulders on 0.3–3 % of vertices, 99th percentile 3–10 mm; if group 5 shows it affects the shoulder zones, it is recorded again.
- CLO shows a trial-licence notice: the subscription renews on 29 Oct 2026.

## Garment rest state (tasks 2.1, 2.2), 16 Oct 2026

`simiq_fit/garment_mesh.py` reads CLO's OBJ, keeps the fabric pieces (material `FABRIC_13`; zipper, topstitch and trim blocks are left out), welds seams and gives every triangle its unstretched shape in the flat pattern.

- **UV is not mm.** CLO's UV layout is a non-square texture space: 1 unit of u is 538.01 mm and 1 unit of v is 763.79 mm for this export. Fitted per piece from the DXF (outline size across and along the grain line over the UV size): spread 0.016 % and 0.004 % over the 15 pieces. Stored in `cases/manifest.json` (`uv_mm_per_unit`) with how it was found; `scripts/cloth_spike.py calibrate-uv` recomputes it.
- **Grain along v.** CLO lays every piece out with its grain line along v, whatever the DXF orientation (six pieces are turned 90° in UV). So u is the course (where the 72 % width shrinkage acts) and v the wale.
- **Welding.** 80 % of the pieces' outline vertices lie within 0.01 mm of another piece's in CLO's drape; the rest are free edges (hem, cuffs, neckline, zipper). Pairs within 0.5 mm are joined nearest first, and never so that one seam vertex holds two vertices of the same piece: a binding folded over an edge would otherwise collapse onto itself (the first version did that to 113 vertices and left 35 degenerate triangles).
- **Check on the starting drape** (`scripts/cloth_spike.py mesh`): 15 pieces, 38,775 triangles, 20,664 vertices welded to 19,673, one connected garment, no degenerate triangle. The pieces' outlines measured on the UV rest shapes total 1694.5 cm against 1694.6 cm of DXF cut lines; 564 cm of seams are sewn.

## Strain and pressure fields (tasks 3.1–3.3), 16 Oct 2026

`simiq_fit/surface_strain.py` measures any draped garment with a pattern rest state the same way: per-triangle course and wale strain from the deformation gradient, the area-weighted zone mean, and pressure p = T_c·κ_c + T_w·κ_w with κ from the body under the garment (derivations and hand-computed tests in `formulas.md`). `scripts/cloth_spike.py zones | strain | pressure` run it on CLO's 36 cases; every case is welded on the starting drape so all share one mesh, one set of zone triangles and one rest state per size.

**Zones** (`zones`, written to `$SIMIQ_SPIKE_DIR/zones.npz`, outside git since they index the licensed mesh). The body vertex sets of `jersey-demo/scripts/heatmap.py` on 178/75 `standing` (chest and waist: ±25 mm about the fit engine's section planes, square to the torso; hem: ±25 mm about the hip ring's height; back length: a 6 cm strip down the spine from C7 to the back of the hip). A garment triangle is in a zone when the body vertex nearest its centre on the starting drape is in the set and lies within 30 mm. The sleeve opening is taken on the garment itself: the triangles of the pieces at the sleeve hems (the two free-edge loops farthest to the sides) within 50 mm of the hem, so cuffs, sleeve ends and the underarm inserts that reach the hem. Result: chest 2021 triangles (444 cm²), waist 2921 (647 cm²), hem 619 (150 cm²), sleeve opening 2589 (504 cm²), back length 2441 (537 cm²).

- The hem band sits at the jersey's lower edge and catches mostly the longer back (median z −166 mm, with the back at about −190 mm and the front at +80 mm): it is a back-hem zone, not a full girth.
- The sleeve band of `heatmap.py` (a shell 10–14 cm from each armpit) was tried first and dropped: 55 % of it lies above the armpit, on the shoulder cap, not at the sleeve's opening, which the fit engine's `sleeve_opening` measures.

**Alignment check.** The point caches that drove CLO give the posed body of every case (`anny-{standing,hoods-body,drops-standing}-sequence.pc2` at the frames of `clo_cache_extract.FRAMES`); the standing 178/75 frame equals the A-pose OBJ to 0.0 mm. Garment vertices sit 3.4 / 4.6 / 9.6 mm (p10 / median / p90) off the body along its normal on the starting drape, with no systematic offset (median offset vector under 1.2 mm): CLO's collision distance plus some loose fabric, as expected.

### Strain on CLO's drapes (task 3.2)

Zone mean course strain (wale for back length), size M; all 36 cases in the run log (`strain`, 5.7 s):

| pose | body | chest | waist | hem | sleeve opening | back length |
|---|---|---|---|---|---|---|
| standing | 178/75 | 8.6 % | 11.8 % | 26.0 % | 0.3 % | −0.8 % |
| standing | 180/64 | 6.2 % | 1.2 % | 20.6 % | 1.1 % | −0.1 % |
| standing | 176/88 | 13.8 % | 26.7 % | 31.8 % | −1.8 % | −0.6 % |
| standing | 192/82 | 11.8 % | 10.7 % | 29.6 % | 1.1 % | 2.1 % |
| hoods | 178/75 | 5.7 % | 15.6 % | 30.2 % | −0.1 % | 0.1 % |
| hoods | 180/64 | 4.6 % | 3.7 % | 23.9 % | 1.3 % | 0.6 % |
| hoods | 176/88 | 16.0 % | 29.7 % | 41.9 % | 5.0 % | 2.4 % |
| hoods | 192/82 | 9.0 % | 13.4 % | 32.3 % | 2.3 % | 3.3 % |
| drops | 178/75 | 6.9 % | 23.2 % | 18.9 % | 0.0 % | −1.5 % |
| drops | 180/64 | 5.1 % | 19.4 % | 12.1 % | −2.7 % | −1.2 % |
| drops | 176/88 | 9.4 % | 32.5 % | 31.2 % | 17.4 % | −2.1 % |
| drops | 192/82 | 9.4 % | 25.7 % | 17.8 % | −1.6 % | −1.5 % |

- **176/88 above 180/64:** holds in chest, waist and hem in every pose and size (27 of 27). It does not hold for the sleeve opening, with either band. With the shoulder shell it failed in hoods S, M, L and drops M, L (hoods M 1.1 % against 2.9 %; drops M was then still the old recording). At the sleeve hem it fails in standing S, M, L and hoods L, and the reason is plain: CLO leaves the sleeve opening essentially unstretched on every body, −2.7 to +5.0 % in all 36 cases bar three, so the difference between bodies is noise around zero, and on 176/88 standing the fabric is slightly compressed (−1.7 to −2.4 %). The three exceptions are drops 176/88 S, M and L (29.0, 17.4 and 26.5 %): the heavy arm pinches the underarm against the torso, 2–3.5 % of the zone's triangles are stretched past 50 % (up to 610 %) while the medians are −3 to −4 %, and the area weighting lets them dominate. **Decision** (the founder left it to the agent, 16 Oct): 3.2 is verified on the torso girth zones, where the claim is about the garment's fit; the sleeve opening is reported but not part of the claim, because on this jersey CLO does not stretch it. Task 3.2 ticked on that basis.
- **Sizes:** chest strain S > M > L on every body and pose (12 of 12), and so does the waist. The hem ranks M > L everywhere and S > M everywhere but hoods 178/75, 180/64 and 192/82 (S 1–2 points below M). With the demo's original drops-M recording, chest failed on drops 176/88 (S 11.5 %, M 17.0 %, L 7.2 %) and M had the highest hem strain of the three sizes on every body (178/75: S 23.5 %, M 38.8 %, L 12.9 %); recorded again by `clo_spike_export.py` like S and L, 178/75 drops reads chest 8.8 / 6.9 / 4.4 % and hem 23.5 / 18.9 / 12.9 %. The old recording was a different garment state, not a size effect; it is kept outside git as `cases/drops-M.orig.npz`.
- Back length strain is within ±3.3 %: the wale hardly stretches on this jersey, so the length zone is decided by how the garment rides, not by strain.

### Relative pressure (task 3.3)

**Fabric.** CLO's FABRIC_13 is unknown, so the tension comes from a published, measured knit: fabric LB of Teyeme et al., *Predicting Compression Pressure of Knitted Fabric Using a Modified Laplace's Law*, Materials 14 (2021) 4461, doi:10.3390/ma14164461 (CC BY 4.0): single-face tricot, 74 % nylon / 26 % elastane, 150 g/m², 0.29 mm, the lightest of their four and closest to a jersey. Their Table 3 gives engineering stress 46.0, 162.0, 263.1 kPa at 11.1, 24.9 and 42.9 % strain (EN 14704-1, 50 mm strips); tension is stress × thickness, 13.3, 47.0 and 76.3 N/m. Only one direction was published, so the wale repeats it (the wale barely stretches here, ±3 %). Three measured points are below the fit engine's five-point rule for a product fabric, so it lives as a constant in `cloth_spike.py` (`STAND_IN_FABRIC`), not in `data/`. No open source with full course and wale curves of a polyester/elastane jersey turned up (searched Europe PMC: swimwear and sportswear papers give breaking force and elongation only); the real curve comes from the Isadore fabric or our own strip test. The Pascals therefore mean nothing; only the ranking of sizes does.

**Result** (`pressure`, 2 min). Chest on 178/75 `standing`: S 89 Pa, **M 58 Pa > L 35 Pa** (relative 1.00 / 0.65 / 0.39). The chest ranks M above L on every body in every pose; in `standing` every girth zone of every body ranks S ≥ M ≥ L (sleeve opening of 178/75: M and L both 20 Pa). M does not press more than L in three places: the waist in drops on 176/88 (320 against 328 Pa, with 22 and 13 % of the zone beyond the curve) and the hem and sleeve opening in hoods on 176/88. With the old drops-M recording the drops waist failed on all four bodies and the drops sleeve opening on three; recorded again, drops 178/75 chest is S 88, M 64, L 47 Pa. Hoods 176/88's hem has 23 % of its triangles beyond the curve's 42.9 % on every size, and the mean is taken over the rest. Beyond the curve in general: chest up to 6 %, waist up to 36 % (drops 176/88 S), hem 0–23 %; the hem is the zone the curve does not cover.

The example knit (illustrative values, curve to 50 %) gave the same ranking in `standing` and, with the old drops-M recording, the same drops exceptions: 178/75 chest S 282, M 196, L 118 Pa.

Taking κ from the garment's own surface instead of the body (tried first) let CLO's folds flip the sign of the curvature: hoods L chest came out at −17 Pa and sizes did not rank in the poses. With the body's κ the ranking holds wherever the strain ranking does.

Run times on the Mac: `zones` 16 s, `strain` 6 s for 36 cases, `pressure` 2 min (nearest body triangle by brute force, 38,775 × 27,420 per case).

## Drape solver (tasks 4.1–4.4), 18 Oct 2026

`simiq_fit/drape.py`: XPBD on Warp (CPU), per substep a prediction, two passes of per-triangle course, wale and shear stretch from the fabric curve, one bending pass, one body-collision pass, then velocities with Coulomb friction. Derivations in `formulas.md`; spec tests in `tests/test_drape.py`. `scripts/cloth_spike.py drape | timing` run it on the jersey.

**4.1 Hanging strip.** The example knit's 50 mm strip with the curve's 20 % load settles at 20.2 % (500 substeps/s × 2 passes; 19.8 % at 1000 × 2), within the 1 point. It took two fixes to get there, both general:

- A heavy weight on a light strip (w ratio 10⁴) or a force on a 5 µg vertex does not converge in Gauss-Seidel passes (388 % instead of 20 %). Inertia is scaled by `MASS_SCALE` = 1000 while weight stays the fabric's own force: the settled state is unchanged, only the way to it.
- A piecewise curve is solved piece by piece, constraint C = ε − ε₀ with the piece's own slope, so the force is exactly A·T(ε) on every piece.

**4.2 Tube on a cylinder.** The spec's 84 cm tube on a 96 cm cylinder settles at 14.285 % (14.3 %), no vertex inside; also with a 2.2 mm thicker layer. Bending is a flat-rest hinge per interior edge (discrete-shell energy, weights from the rest triangles); its stiffness, 10⁻⁶ N·m, is a guess and matters little on the tight jersey (switched off, the chest's course strain after 0.2 s moved by 0.3 points).

**The real jersey needed three things the tube did not:**

- *The zipper.* `load_garment` kept only the FABRIC_13 pieces, so the jersey was open at the front: within 0.2 s the front panels lost 13.7 points of course strain and the chest went from 7.9 % to 0.6 %. The zipper tapes (`Fabric628555`, UV is a texture, not a pattern) are now `trims`: each triangle rests in its drape shape, they weld to the fronts and to each other, and they are 100 × the knit's stiffness (a guess for a woven tape). With them the chest holds at 6.5–7 % on the start body.
- *The collision distance.* CLO keeps the garment 4.6 mm off the avatar (start drape: p1 4.58, median 4.73 mm). With the design's 2 mm the garment first moved 2.6 mm inward with no contact and no friction; `COLLISION_MM` is now CLO's 4.6 mm.
- *The pockets.* Cloth does not collide with cloth here, so the back pockets (pieces 1, 12) fell through the back panel to the body (median 25 mm). First fix: keep them 2.2 mm further off the body (CLO: pocket p5 6.7–6.8 mm, back panel 4.6 mm). That held them up but let them lift off the back like a chord (median 8 → 14 mm off the body) and go slack (waist zone pocket triangles −0.6 % against CLO's 8.3 %). The cause was the weld: the pockets' bottom seam lies 0.5–1 mm off the back panel in CLO's drape, so at 0.5 mm it was never sewn (32 shared vertices; 125 at 1 mm, no degenerate triangle). `WELD_MM` is now 1 mm, and the pockets are a layer kept 2.2 mm off the back panel (the one place cloth meets cloth, formulas.md). Pocket triangles in the waist zone: 11.0 % against CLO's 8.6 %. The silicone hem gripper and the zipper teeth are still left out.

The sleeves still ride 7–13 mm up the arm on the start body and the pocket edge moves; whether that matters is for group 5's zone comparison.

**4.3 Body sequence.** 178/75 → 176/88 `hoods` through CLO's own point cache (`anny-m176-88-morph-hoods.pc2`: morph 40 frames, settle 15, pose 120, hold 30), size M, final solver (after group 5's changes below):

- *Determinism:* two runs agree to 0.0000 mm (colour-ordered Gauss-Seidel, no atomics).
- *Penetration* (winding-number inside test): 100.00 % of vertices outside at all 14 recorded frames; the deepest vertex is 0.87 mm off the skin (frame 120). The first solver of 18 Oct let one to five armpit vertices go 2–4.25 mm inside (frames 45–135), where the posed Anny's arm and torso meet. CLO's own M drapes are worse on the same check: hoods 176/88 99.04 % outside, 144 vertices below −2 mm, deepest −6.19 mm; every hoods and drops case has vertices below −2 mm, drops down to −14.15 mm. Founder ruling 7 (18 Oct) makes the depth limit CLO's drape of the same case, so 4.3 passes; group 5 checks it on all 36 cases (36 of 36).
- The angle-weighted normal's sign called one armpit vertex inside when it was 4.6 mm outside; inside is now confirmed by winding number before a vertex is pushed.

**4.4 Timing** (`timing`, Apple M3 Pro, Warp 1.18 on one CPU core, final solver): 39,045 triangles, 19,603 vertices, 6.80 s of sequence at 500 substeps/s × 2 passes: setup 1.9 s, simulation 54.7 s (8.0 s per simulated second), **56.6 s total**, under the 60 s budget with CLO's 10 mm mesh as it is, so the particle distance stays 10 mm. Per substep: triangles 3.2 ms per pass, bending 1.0 ms, collision 2.4 ms (15 ms with a BVH query per vertex; now the last nearest face is tried first and one vertex in four asks the BVH), body refit 2.8 ms while it moves. Nine sequences run side by side on the 11 cores (one process each) in 2.3–4.6 min.


## Comparison with CLO and recommendation (tasks 5.1, 5.2), 18 Oct 2026

**Recommendation: no-go for now.** Against the acceptance scenarios: sizes rank like CLO's in chest strain on all 12 body × pose pairs (pass), one garment on one body takes 56.6 s (pass), and no case goes deeper into the body than CLO's drape of it (36 of 36, ruling 7). But only **4 of 35** held-out cases have every zone within ±3 points of CLO, so the report recommends no-go (spec: "any of those conditions fails"). The failures have one main cause, found but not fixed: in the posed sequences the jersey creeps up the body (below). Standing on the first bodies of a sequence it agrees well.

**How it was run.** `simulate <pose> <size>` drives our drape through the very point cache that drove CLO's run of that pose (and, for `hoods` and `drops`, first through the 178/75 A-pose → hoods animation that brought CLO's garment there: those caches start in the pose, 672 mm from the starting drape's body) and saves our garment at CLO's case frames; nine runs side by side, 2.3–4.6 min each. `report` scores both with the same zone metric (group 3) and checks penetration with the winding-number test. Fabric: the stand-in tricot × the fitted scales.

**5.1 Fit.** Course and wale tension scales on a 5 × 5 grid (×0.25 … ×4), the case settling 3 s on 178/75 `standing` from CLO's starting drape: best course ×1, wale ×4, 1.00 points rms. Per zone, ours − CLO: chest +0.13, waist +1.28, hem +0.85, sleeve opening −1.55, back length +0.41 points. Waist and sleeve miss the 1 point, so 5.1 is not met. Only the course/wale ratio matters much (×1/×2: 1.02 rms); the chest ranges 3.2–11.7 % over the grid.

**5.2 All cases**, ours / CLO (ours − CLO) in % course strain (wale for back length), worst zone in points, and the deepest vertex (mm off the skin, negative inside) of ours and CLO's:

| pose | size | body | chest | waist | hem | sleeve_opening | back_length | worst | deepest ours / CLO mm |
|---|---|---|---|---|---|---|---|---|---|
| standing | S | 178-75 | 9.9 / 12.0 (-2.2) | 24.0 / 17.2 (+6.8) | 27.5 / 32.0 (-4.6) | -3.7 / 0.4 (-4.0) | -1.2 / -1.1 (-0.1) | 6.8 | 3.5 / 3.1 |
| standing | S | 180-64 | 8.9 / 9.3 (-0.4) | 5.8 / 3.9 (+1.9) | 23.7 / 26.8 (-3.1) | -0.6 / 1.3 (-1.9) | -0.5 / -0.2 (-0.2) | 3.1 | 4.6 / 3.9 |
| standing | S | 176-88 | 17.0 / 17.4 (-0.5) | 31.4 / 33.0 (-1.5) | 40.9 / 38.3 (+2.5) | -6.8 / -1.7 (-5.1) | -1.7 / -1.0 (-0.7) | 5.1 | 2.2 / -3.1 |
| standing | S | 192-82 | 13.5 / 15.3 (-1.7) | 15.4 / 15.7 (-0.3) | 32.4 / 35.8 (-3.4) | -1.6 / 1.7 (-3.3) | -0.3 / 1.9 (-2.3) | 3.4 | 4.5 / 4.0 |
| standing | M | 178-75 (fitted) | 6.8 / 8.6 (-1.8) | 26.7 / 11.9 (+14.8) | 20.1 / 26.0 (-5.9) | -3.3 / 0.3 (-3.6) | -0.1 / -0.7 (+0.6) | 14.8 | 3.7 / 3.6 |
| standing | M | 180-64 | 6.1 / 6.2 (-0.1) | 2.8 / 1.4 (+1.4) | 18.5 / 20.7 (-2.2) | -0.7 / 1.1 (-1.8) | -0.3 / -0.1 (-0.2) | 2.2 | 4.6 / 4.1 |
| standing | M | 176-88 | 13.4 / 13.8 (-0.4) | 25.7 / 26.9 (-1.1) | 34.9 / 31.8 (+3.0) | -5.4 / -1.8 (-3.6) | -1.7 / -0.5 (-1.2) | 3.6 | 2.4 / -0.4 |
| standing | M | 192-82 | 10.7 / 11.8 (-1.1) | 10.6 / 10.8 (-0.2) | 26.9 / 29.6 (-2.7) | -1.4 / 1.1 (-2.5) | -0.1 / 2.2 (-2.3) | 2.7 | 4.6 / 3.9 |
| standing | L | 178-75 | 4.0 / 5.4 (-1.3) | 16.8 / 7.1 (+9.7) | 13.7 / 20.8 (-7.1) | -2.7 / 0.1 (-2.8) | -4.1 / -0.6 (-3.4) | 9.7 | 3.8 / 3.4 |
| standing | L | 180-64 | 3.6 / 3.5 (+0.1) | 0.8 / 0.5 (+0.4) | 13.7 / 15.4 (-1.6) | -0.8 / 0.8 (-1.6) | -0.1 / -0.1 (-0.0) | 1.6 | 4.5 / 4.0 |
| standing | L | 176-88 | 10.4 / 9.6 (+0.7) | 23.6 / 21.2 (+2.4) | 28.1 / 26.8 (+1.3) | -5.1 / -2.4 (-2.6) | -1.3 / -0.7 (-0.6) | 2.6 | 2.4 / -2.9 |
| standing | L | 192-82 | 7.7 / 8.2 (-0.5) | 16.4 / 6.2 (+10.3) | 17.2 / 24.0 (-6.7) | -1.0 / 1.0 (-2.0) | -2.8 / 1.6 (-4.4) | 10.3 | 4.6 / 4.0 |
| hoods | S | 178-75 | 5.7 / 8.0 (-2.3) | 34.2 / 20.2 (+13.9) | 20.8 / 28.3 (-7.4) | -5.5 / -0.9 (-4.6) | -5.1 / -1.3 (-3.7) | 13.9 | 1.3 / -4.6 |
| hoods | S | 180-64 | 5.1 / 5.5 (-0.4) | 23.6 / 6.4 (+17.3) | 14.0 / 22.9 (-8.9) | -1.3 / 1.1 (-2.3) | -0.5 / -0.8 (+0.3) | 17.3 | 1.2 / -3.8 |
| hoods | S | 176-88 | 14.0 / 18.9 (-4.9) | 44.1 / 34.0 (+10.1) | 32.5 / 42.5 (-10.0) | -7.4 / 3.7 (-11.1) | -3.9 / -0.7 (-3.2) | 11.1 | 1.9 / -5.6 |
| hoods | S | 192-82 | 9.9 / 9.9 (-0.0) | 27.5 / 17.2 (+10.3) | 17.1 / 30.3 (-13.1) | -2.5 / 1.4 (-3.9) | -3.0 / -1.0 (-2.0) | 13.1 | 1.8 / -4.6 |
| hoods | M | 178-75 | 3.0 / 5.7 (-2.7) | 30.6 / 15.8 (+14.8) | 16.3 / 30.2 (-13.9) | -5.0 / -0.1 (-4.9) | -2.8 / 0.3 (-3.1) | 14.8 | 1.8 / -4.7 |
| hoods | M | 180-64 | 2.7 / 4.6 (-1.8) | 15.0 / 3.9 (+11.1) | 7.2 / 23.9 (-16.8) | -1.0 / 1.3 (-2.3) | -3.1 / 0.7 (-3.7) | 16.8 | 2.9 / -6.4 |
| hoods | M | 176-88 | 10.9 / 16.0 (-5.1) | 37.9 / 29.9 (+8.1) | 21.7 / 41.9 (-20.2) | -7.0 / 5.0 (-12.0) | -2.5 / 2.5 (-5.1) | 20.2 | 2.8 / -6.2 |
| hoods | M | 192-82 | 6.7 / 9.0 (-2.4) | 27.5 / 13.6 (+13.9) | 10.4 / 32.3 (-21.9) | -2.0 / 2.3 (-4.3) | -2.2 / 3.5 (-5.7) | 21.9 | 2.2 / -5.9 |
| hoods | L | 178-75 | 0.6 / 2.7 (-2.1) | 25.2 / 11.4 (+13.8) | 12.2 / 20.3 (-8.1) | -4.0 / -1.5 (-2.5) | -2.3 / -0.8 (-1.5) | 13.8 | 2.9 / -4.7 |
| hoods | L | 180-64 | 0.8 / 1.1 (-0.3) | 11.4 / 2.2 (+9.3) | 5.6 / 13.5 (-7.8) | -1.1 / 0.4 (-1.5) | 0.1 / -0.3 (+0.4) | 9.3 | 2.3 / -3.1 |
| hoods | L | 176-88 | 8.2 / 11.5 (-3.3) | 34.3 / 23.3 (+11.0) | 21.9 / 33.3 (-11.4) | -5.8 / -0.9 (-4.8) | -0.8 / -0.5 (-0.3) | 11.4 | 2.6 / -5.9 |
| hoods | L | 192-82 | 5.1 / 3.9 (+1.2) | 21.3 / 8.8 (+12.5) | 11.9 / 22.1 (-10.2) | -1.4 / 0.5 (-1.9) | 1.4 / -0.4 (+1.7) | 12.5 | 1.9 / -2.9 |
| drops | S | 178-75 | 5.2 / 8.8 (-3.5) | 39.7 / 29.7 (+10.0) | 20.1 / 23.5 (-3.5) | -5.9 / 1.8 (-7.7) | -2.9 / -1.9 (-1.0) | 10.0 | 0.7 / -11.7 |
| drops | S | 180-64 | 3.7 / 6.6 (-2.9) | 34.0 / 25.8 (+8.3) | 21.2 / 14.7 (+6.5) | -1.6 / -1.4 (-0.2) | -3.6 / -1.4 (-2.2) | 8.3 | 0.7 / -8.7 |
| drops | S | 176-88 | 12.7 / 11.5 (+1.2) | 49.7 / 39.5 (+10.2) | 34.1 / 35.2 (-1.1) | -8.1 / 29.0 (-37.1) | -5.9 / -2.5 (-3.4) | 37.1 | 1.2 / -14.7 |
| drops | S | 192-82 | 8.0 / 11.2 (-3.3) | 37.1 / 32.2 (+4.9) | 18.4 / 22.5 (-4.2) | -3.5 / -0.2 (-3.3) | -3.7 / -1.8 (-1.9) | 4.9 | 0.7 / -11.6 |
| drops | M | 178-75 | 3.0 / 6.9 (-3.9) | 33.1 / 23.4 (+9.7) | 16.5 / 18.9 (-2.4) | -5.1 / 0.0 (-5.2) | -4.2 / -1.5 (-2.7) | 9.7 | 0.2 / -12.3 |
| drops | M | 180-64 | 1.9 / 5.1 (-3.2) | 30.5 / 19.6 (+10.9) | 14.7 / 12.2 (+2.5) | -1.1 / -2.7 (+1.6) | -3.6 / -1.2 (-2.5) | 10.9 | 0.2 / -12.1 |
| drops | M | 176-88 | 9.8 / 9.4 (+0.4) | 46.1 / 32.7 (+13.5) | 27.1 / 31.2 (-4.1) | -7.3 / 17.4 (-24.8) | -3.9 / -2.2 (-1.7) | 24.8 | 1.4 / -11.6 |
| drops | M | 192-82 | 5.7 / 9.4 (-3.7) | 32.5 / 25.9 (+6.6) | 20.4 / 17.8 (+2.6) | -2.2 / -1.6 (-0.6) | -2.7 / -1.5 (-1.2) | 6.6 | 0.6 / -14.1 |
| drops | L | 178-75 | 1.0 / 4.4 (-3.3) | 30.2 / 20.3 (+9.9) | 20.5 / 13.0 (+7.5) | -4.4 / 0.9 (-5.3) | -3.1 / -1.4 (-1.7) | 9.9 | 1.1 / -14.4 |
| drops | L | 180-64 | 0.2 / 2.7 (-2.5) | 27.5 / 16.3 (+11.1) | 18.0 / 8.1 (+9.9) | -1.0 / -1.2 (+0.2) | -1.6 / -0.7 (-0.9) | 11.1 | 0.7 / -12.1 |
| drops | L | 176-88 | 7.8 / 7.2 (+0.6) | 36.5 / 29.1 (+7.3) | 29.3 / 23.1 (+6.2) | -6.3 / 26.5 (-32.8) | -2.4 / -2.1 (-0.3) | 32.8 | 1.7 / -13.8 |
| drops | L | 192-82 | 3.4 / 6.5 (-3.1) | 27.8 / 22.5 (+5.3) | 20.3 / 13.0 (+7.3) | -2.0 / -0.2 (-1.8) | -4.3 / -0.1 (-4.2) | 7.3 | 0.8 / -17.9 |

Summary: held-out cases within ±3 points in every zone 4 of 35 (standing M 180/64, 192/82; standing L 180/64, 176/88). Chest size ranking as CLO's 12 of 12. Deepest vertex no deeper than CLO's 36 of 36: ours stays 0.2–4.6 mm off the skin everywhere, CLO's goes up to 17.9 mm inside in `drops`.

Renders (course strain, CLO above, ours below; blue −30 %, white 0, red +30 %): [standing M 192/82](cloth-sim-spike/standing-M-192-82.png) (agrees), [hoods M 176/88](cloth-sim-spike/hoods-M-176-88.png) and [drops M 180/64](cloth-sim-spike/drops-M-180-64.png) (do not).

### Why the posed cases fail

- **The jersey creeps up in the posed sequences.** The hem edge ends 80–140 mm above CLO's in every `hoods` case (p90 up to 289 mm) and 107 mm on standing 178/75 after the other three bodies; on standing 180/64, the first body of its sequence, 6 mm. Traced through hoods M: during the lead-in pose the hem rises 87 mm relative to the hip ring, then keeps rising with every body change while the pose stays (78 → 163 mm over the four bodies). Nothing pulls it back down: with inertia scaled × 1000 the cloth falls at g/1000, and friction only acts on vertices the collision pushed in that substep, so fabric hovering just off the skin slides freely. In `hoods` the waist zone then reads +8 to +17 points and the hem −7 to −22. Fixes to try next, in order: static friction that persists while a vertex stays within a fraction of a millimetre of the skin; gravity at full strength with the iteration count that converges without inertia scaling (8 passes at 1000 substeps/s ≈ 4× the time); and the silicone gripper as part of the cloth instead of a friction coefficient.
- **Sleeves and shoulders.** Ours compresses the upper sleeve and shoulder (sleeve opening −0.6 to −8.1 % in every case, where CLO has −2.7 to +5 % outside the pinched drops 176/88); our bending and shear are guesses, and CLO's sleeve opening is near zero strain, so a few points of difference fail the ±3. In drops 176/88 CLO's sleeve zone reads +17 to +29 % from a pinched underarm (group 3); ours does not pinch.
- **Pockets.** One back pocket can still lift off and go slack (white patch in the standing render).

### Solver changes made in group 5 (all in `drape.py` / `garment_mesh.py`, with tests)

1. **Lead-in to the pose.** CLO's `hoods` and `drops` runs start from a garment already posed; the first comparison started ours from the A-pose drape inside a posed body, and the garment fell through it (waist strain 300 %, vertices 96 mm inside).
2. **Weld at 1 mm** (spec scenario changed from 0.5 mm): the back pockets' bottom seam lies 0.5–1 mm off the back panel in CLO's drape and was never sewn, so the pocket lifted off like a chord. Pocket triangles in the waist went from −0.6 % to 11.0 % (CLO 8.6 %).
3. **Pockets as a layer** on the back panel (2.2 mm), replacing the extra body distance.
4. **Inelastic contact:** a collision push no longer becomes a velocity off the surface.
5. **Inertia scaling is a parameter**, and **the body carries the cloth on it** (`carry`): with natural mass, 500 × 2 passes did not converge (every stiffness gave the same drape, 3.46 points rms); with inertia × 1000 the cloth could not follow a body that got shorter (hem 156 mm high on standing 178/75). Carrying cut that to 67 mm (107 mm again with the gripper friction below) but not the creep in the poses.
6. **Friction per vertex** and 1.5 under the silicone hem gripper: it changed the posed cases by less than their scatter, which is how the creep was traced to vertices out of contact rather than to sliding under load.

Results before these changes, for the record: first comparison (no lead-in) 4 of 35, ranking 4 of 12; with lead-in, pocket layer and 1 mm weld 5 of 35, ranking 12 of 12; with the body carrying the cloth 4 of 35, ranking 12 of 12; final (gripper friction) 4 of 35, 12 of 12.
