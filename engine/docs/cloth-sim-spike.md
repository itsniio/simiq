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
- *Penetration* (winding-number inside test): 99.99–100 % of vertices outside at all 14 recorded frames; the deepest vertex is 0.62 mm inside (one vertex, frame 150), against CLO's −6.19 mm on the same case. The first solver of 18 Oct let one to five armpit vertices go 2–4.25 mm inside (frames 45–135), where the posed Anny's arm and torso meet. CLO's own M drapes are worse on the same check: hoods 176/88 99.04 % outside, 144 vertices below −2 mm, deepest −6.19 mm; every hoods and drops case has vertices below −2 mm, drops down to −14.15 mm. Founder ruling 7 (18 Oct) makes the depth limit CLO's drape of the same case, so 4.3 passes; group 5 checks it on all 36 cases (36 of 36).
- The angle-weighted normal's sign called one armpit vertex inside when it was 4.6 mm outside; inside is now confirmed by winding number before a vertex is pushed.

**4.4 Timing** (`timing`, Apple M3 Pro, Warp 1.18 on one CPU core, final solver): 39,045 triangles, 19,603 vertices, 6.80 s of sequence at 500 substeps/s × 2 passes: setup 2.0 s, simulation 53.2–53.4 s (7.8–7.9 s per simulated second), **55.2–55.4 s total** (19 Oct, final solver with friction 1.0 and shear 40 N/m), 4.6 s inside the 60 s budget. On the CPU each colour of triangles or hinges was its own launch, 52 a substep; a CPU launch runs its threads one after another, so one launch over all colours in order computes exactly the same (the 4.3 sequence came out identical to 0.0 mm) and saved 3 s (58.2–58.4 s before; up to 64.5 s while macOS's media analysis took two cores). The colours stay for a GPU. The particle distance stays 10 mm (CLO's mesh as it is); a 15 mm mesh would need a new CLO export. Per substep: triangles 3.2 ms per pass, bending 1.0 ms, collision 2.4 ms (15 ms with a BVH query per vertex; now the last nearest face is tried first and one vertex in four asks the BVH), body refit 2.8 ms while it moves. Nine sequences run side by side on the 11 cores (one process each) in 2.4–4.5 min.


## Comparison with CLO and recommendation (tasks 5.1, 5.2), 18–19 Oct 2026

**Recommendation: no-go as specified; standing passes, the poses wait for two measured numbers.** Against the acceptance scenarios: sizes rank like CLO's in chest strain on all 12 body × pose pairs (pass); no case goes deeper into the body than CLO's drape of it (36 of 36, ruling 7, pass); one garment on one body takes 55.2–55.4 s (pass); every zone within ±3 points of CLO on only **11 of 33** held-out cases (fail). In `standing` all 11 held-out cases are within 3.3 points (10 within 3). The poses fail mainly in the hem zone (+5 to +30 points, size S worst) and on 176/88's underarm. They depend sharply on fabric-on-skin friction and in-plane shear, which are not measured; the last proposal below says how to measure them in a day, after which one honest run decides.

**How it was run.** `simulate <pose> <size>` drives our drape through the very point cache that drove CLO's run of that pose (and, for `hoods` and `drops`, first through the 178/75 A-pose → hoods animation that brought CLO's garment there: those caches start in the pose, 672 mm from the starting drape's body) and saves our garment at CLO's case frames; nine runs side by side, 2.4–4.5 min each. `report` scores both with the same zone metric (group 3) and checks penetration with the winding-number test. Fabric: the stand-in tricot × the fitted scales; friction and shear as calibrated below.

**5.1 Fit.** Course and wale tension scales on a 5 × 5 grid (×0.25 … ×4), the case settling 3 s on 178/75 `standing` from CLO's starting drape: best course ×2, wale ×4, 1.35 points rms. Per zone, ours − CLO: chest −1.34, waist +1.52, hem −1.81, sleeve opening −1.22, back length +0.41 points. Four zones miss the 1 point, so 5.1 is not met. Mostly the course/wale ratio matters (×1/×4: 1.37 rms). Through its whole sequence the same case ends within 1.6 points in every zone.

**Calibration of friction and shear (my proposal, not in the spec; founders to approve).** The fit case cannot see either number (shear 5–160 N/m moves it by 0.07 points rms), so they were calibrated on the fitted body and size in the two poses, 178/75 M `hoods` and `drops`, which are therefore no longer held out (33 remain). `calibrate` over friction 0.5, 0.7, 1.0, 1.4 × shear 20, 40, 80 N/m, rms over the ten zones of the two cases:

| friction \ shear | 20 N/m | 40 N/m | 80 N/m |
|---|---|---|---|
| 0.5 | 6.39 | 6.52 | 7.20 |
| 0.7 | 5.90 | 6.18 | 6.21 |
| **1.0** | 2.61 | **2.48** | 3.03 |
| 1.4 | 9.81 | 9.18 | 7.87 |

Friction 1.0 is a sharp optimum on both poses and shear a weak one; 1.0 and 40 N/m are now `KNIT_FRICTION` and `KNIT_SHEAR_N_PER_M`. Neither is a measured value.

**5.2 All cases**, ours / CLO (ours − CLO) in % course strain (wale for back length), worst zone in points, and the deepest vertex (mm off the skin, negative inside) of ours and CLO's; "(fitted)" marks the stiffness fit case and the two calibration cases:

| pose | size | body | chest | waist | hem | sleeve_opening | back_length | worst | deepest ours / CLO mm |
|---|---|---|---|---|---|---|---|---|---|
| standing | S | 178-75 | 11.1 / 12.0 (-0.9) | 18.3 / 17.2 (+1.2) | 30.1 / 32.0 (-1.9) | -1.5 / 0.4 (-1.9) | -0.9 / -1.1 (+0.2) | 1.9 | 4.6 / 3.1 |
| standing | S | 180-64 | 8.9 / 9.3 (-0.4) | 5.7 / 3.9 (+1.8) | 26.7 / 26.8 (-0.2) | 0.0 / 1.3 (-1.3) | -0.3 / -0.2 (-0.0) | 1.8 | 4.6 / 3.9 |
| standing | S | 176-88 | 16.0 / 17.4 (-1.5) | 33.2 / 33.0 (+0.2) | 35.0 / 38.3 (-3.3) | -2.8 / -1.7 (-1.1) | -0.7 / -1.0 (+0.3) | 3.3 | 1.1 / -3.1 |
| standing | S | 192-82 | 14.6 / 15.3 (-0.6) | 17.1 / 15.7 (+1.4) | 34.5 / 35.8 (-1.3) | 0.2 / 1.7 (-1.5) | 2.7 / 1.9 (+0.8) | 1.5 | 4.6 / 4.0 |
| standing | M | 178-75 (fitted) | 8.1 / 8.6 (-0.5) | 13.0 / 11.9 (+1.1) | 24.5 / 26.0 (-1.6) | -1.4 / 0.3 (-1.7) | -0.8 / -0.7 (-0.0) | 1.7 | 4.5 / 3.6 |
| standing | M | 180-64 | 5.7 / 6.2 (-0.5) | 2.3 / 1.4 (+1.0) | 20.4 / 20.7 (-0.2) | -0.3 / 1.1 (-1.4) | -0.3 / -0.1 (-0.2) | 1.4 | 4.6 / 4.1 |
| standing | M | 176-88 | 12.5 / 13.8 (-1.3) | 26.8 / 26.9 (-0.0) | 29.1 / 31.8 (-2.7) | -2.9 / -1.8 (-1.1) | -0.8 / -0.5 (-0.2) | 2.7 | 0.7 / -0.4 |
| standing | M | 192-82 | 11.4 / 11.8 (-0.3) | 12.2 / 10.8 (+1.3) | 28.6 / 29.6 (-1.0) | -0.2 / 1.1 (-1.3) | 2.2 / 2.2 (+0.1) | 1.3 | 4.6 / 3.9 |
| standing | L | 178-75 | 5.6 / 5.4 (+0.2) | 8.4 / 7.1 (+1.3) | 19.5 / 20.8 (-1.3) | -1.4 / 0.1 (-1.5) | -0.6 / -0.6 (+0.1) | 1.5 | 4.4 / 3.4 |
| standing | L | 180-64 | 3.4 / 3.5 (-0.1) | 1.0 / 0.5 (+0.5) | 14.6 / 15.4 (-0.8) | -0.5 / 0.8 (-1.3) | -0.2 / -0.1 (-0.1) | 1.3 | 4.6 / 4.0 |
| standing | L | 176-88 | 9.5 / 9.6 (-0.1) | 21.1 / 21.2 (-0.0) | 24.2 / 26.8 (-2.5) | -2.8 / -2.4 (-0.4) | -0.7 / -0.7 (-0.0) | 2.5 | 1.5 / -2.9 |
| standing | L | 192-82 | 8.8 / 8.2 (+0.6) | 8.0 / 6.2 (+1.9) | 23.3 / 24.0 (-0.7) | -0.5 / 1.0 (-1.4) | 1.7 / 1.6 (+0.1) | 1.9 | 4.6 / 4.0 |
| hoods | S | 178-75 | 7.6 / 8.0 (-0.4) | 18.7 / 20.2 (-1.5) | 39.2 / 28.3 (+10.9) | -3.3 / -0.9 (-2.3) | 1.3 / -1.3 (+2.6) | 10.9 | 1.5 / -4.6 |
| hoods | S | 180-64 | 7.7 / 5.5 (+2.2) | 6.3 / 6.4 (-0.1) | 32.2 / 22.9 (+9.3) | 0.6 / 1.1 (-0.5) | 1.4 / -0.8 (+2.2) | 9.3 | 0.0 / -3.8 |
| hoods | S | 176-88 | 11.8 / 18.9 (-7.1) | 33.0 / 34.0 (-1.0) | 48.2 / 42.5 (+5.7) | -4.8 / 3.7 (-8.5) | 3.4 / -0.7 (+4.1) | 8.5 | 0.1 / -5.6 |
| hoods | S | 192-82 | 11.8 / 9.9 (+1.8) | 17.4 / 17.2 (+0.1) | 43.6 / 30.3 (+13.3) | 1.0 / 1.4 (-0.4) | 4.6 / -1.0 (+5.5) | 13.3 | -0.1 / -4.6 |
| hoods | M | 178-75 (fitted) | 4.9 / 5.7 (-0.8) | 14.0 / 15.8 (-1.7) | 32.4 / 30.2 (+2.2) | -3.6 / -0.1 (-3.5) | 0.1 / 0.3 (-0.1) | 3.5 | 0.6 / -4.7 |
| hoods | M | 180-64 | 5.1 / 4.6 (+0.5) | 3.2 / 3.9 (-0.7) | 25.9 / 23.9 (+2.0) | 0.5 / 1.3 (-0.7) | 0.5 / 0.7 (-0.2) | 2.0 | 0.4 / -6.4 |
| hoods | M | 176-88 | 9.1 / 16.0 (-6.9) | 27.4 / 29.9 (-2.5) | 43.2 / 41.9 (+1.3) | -4.3 / 5.0 (-9.2) | 2.3 / 2.5 (-0.3) | 9.2 | 0.9 / -6.2 |
| hoods | M | 192-82 | 8.9 / 9.0 (-0.1) | 12.3 / 13.6 (-1.2) | 35.6 / 32.3 (+3.3) | 0.8 / 2.3 (-1.5) | 3.1 / 3.5 (-0.3) | 3.3 | 0.7 / -5.9 |
| hoods | L | 178-75 | 2.3 / 2.7 (-0.3) | 9.9 / 11.4 (-1.5) | 27.2 / 20.3 (+6.8) | -3.3 / -1.5 (-1.8) | -0.8 / -0.8 (+0.1) | 6.8 | 2.0 / -4.7 |
| hoods | L | 180-64 | 2.1 / 1.1 (+1.0) | 1.6 / 2.2 (-0.6) | 21.7 / 13.5 (+8.2) | 0.4 / 0.4 (+0.0) | -0.3 / -0.3 (+0.0) | 8.2 | 0.7 / -3.1 |
| hoods | L | 176-88 | 6.3 / 11.5 (-5.1) | 21.9 / 23.3 (-1.4) | 38.6 / 33.3 (+5.3) | -4.9 / -0.9 (-4.0) | 0.7 / -0.5 (+1.1) | 5.3 | 1.2 / -5.9 |
| hoods | L | 192-82 | 6.0 / 3.9 (+2.1) | 7.8 / 8.8 (-1.0) | 30.5 / 22.1 (+8.5) | 0.9 / 0.5 (+0.3) | 1.6 / -0.4 (+1.9) | 8.5 | 1.4 / -2.9 |
| drops | S | 178-75 | 7.0 / 8.8 (-1.8) | 26.8 / 29.7 (-2.9) | 32.3 / 23.5 (+8.8) | -3.7 / 1.8 (-5.5) | -2.8 / -1.9 (-0.8) | 8.8 | 0.3 / -11.7 |
| drops | S | 180-64 | 7.1 / 6.6 (+0.5) | 15.9 / 25.8 (-9.9) | 44.8 / 14.7 (+30.2) | 0.5 / -1.4 (+1.9) | 0.1 / -1.4 (+1.5) | 30.2 | -1.0 / -8.7 |
| drops | S | 176-88 | 11.4 / 11.5 (-0.1) | 39.0 / 39.5 (-0.5) | 54.8 / 35.2 (+19.6) | -4.9 / 29.0 (-33.9) | -6.3 / -2.5 (-3.8) | 33.9 | 0.1 / -14.7 |
| drops | S | 192-82 | 11.2 / 11.2 (-0.0) | 26.9 / 32.2 (-5.3) | 39.5 / 22.5 (+17.0) | 0.9 / -0.2 (+1.1) | -2.6 / -1.8 (-0.8) | 17.0 | -0.1 / -11.6 |
| drops | M | 178-75 (fitted) | 4.2 / 6.9 (-2.7) | 23.1 / 23.4 (-0.3) | 21.6 / 18.9 (+2.7) | -3.4 / 0.0 (-3.4) | -5.3 / -1.5 (-3.7) | 3.7 | 0.9 / -12.3 |
| drops | M | 180-64 | 4.5 / 5.1 (-0.5) | 19.4 / 19.6 (-0.2) | 36.5 / 12.2 (+24.3) | 0.5 / -2.7 (+3.2) | -0.7 / -1.2 (+0.5) | 24.3 | -1.1 / -12.1 |
| drops | M | 176-88 | 8.6 / 9.4 (-0.7) | 36.1 / 32.7 (+3.4) | 39.0 / 31.2 (+7.8) | -4.6 / 17.4 (-22.0) | -7.6 / -2.2 (-5.4) | 22.0 | 0.4 / -11.6 |
| drops | M | 192-82 | 8.2 / 9.4 (-1.2) | 24.2 / 25.9 (-1.7) | 26.2 / 17.8 (+8.4) | 0.9 / -1.6 (+2.5) | -3.3 / -1.5 (-1.8) | 8.4 | 0.4 / -14.1 |
| drops | L | 178-75 | 1.8 / 4.4 (-2.5) | 18.1 / 20.3 (-2.2) | 18.0 / 13.0 (+5.1) | -2.6 / 0.9 (-3.5) | -5.7 / -1.4 (-4.4) | 5.1 | -0.2 / -14.4 |
| drops | L | 180-64 | 1.7 / 2.7 (-1.1) | 14.6 / 16.3 (-1.7) | 20.4 / 8.1 (+12.3) | 0.4 / -1.2 (+1.6) | -1.9 / -0.7 (-1.2) | 12.3 | -0.7 / -12.1 |
| drops | L | 176-88 | 6.2 / 7.2 (-1.0) | 31.8 / 29.1 (+2.6) | 33.2 / 23.1 (+10.1) | -5.1 / 26.5 (-31.5) | -6.0 / -2.1 (-3.9) | 31.5 | 1.1 / -13.8 |
| drops | L | 192-82 | 5.5 / 6.5 (-1.0) | 19.7 / 22.5 (-2.8) | 21.1 / 13.0 (+8.1) | 1.2 / -0.2 (+1.3) | -3.9 / -0.1 (-3.8) | 8.1 | -0.2 / -17.9 |

Summary: held-out cases within ±3 points in every zone 11 of 33: all of `standing` but S 176/88 (hem −3.3), and `hoods` M 180/64. Chest size ranking as CLO's 12 of 12. Deepest vertex no deeper than CLO's 36 of 36: ours stays off the skin everywhere, CLO's goes up to 17.9 mm inside in `drops`. Hem edge height, ours − CLO, on M: within 4 mm on average in `standing` and `hoods`, 18–57 mm lower in `drops`.

Renders (course strain, CLO above, ours below; blue −30 %, white 0, red +30 %): [standing M 192/82](cloth-sim-spike/standing-M-192-82.png) (agrees), [hoods M 176/88](cloth-sim-spike/hoods-M-176-88.png), [hoods S 192/82](cloth-sim-spike/hoods-S-192-82.png) and [drops M 180/64](cloth-sim-spike/drops-M-180-64.png) (do not).

### What still fails

- **The hem zone in the poses**: +3 to +13 points in `hoods` (9 of 12 cases, S worst) and +5 to +30 in `drops` (11 of 12), although in `hoods` the hem edge sits at CLO's height. Over the flexed hips our fabric stretches with the skin under it, where CLO's slides; whether the fabric holds or slides there is set by friction, the parameter the poses are most sensitive to. In `drops` our hem edge also ends 18–57 mm lower than CLO's: CLO's jersey rides further up the back.
- **176/88's underarm**: chest −5 to −7 and sleeve opening −4 to −9 points in `hoods`; in `drops` CLO pinches the heavy underarm (sleeve opening +17 to +29 %, group 3) and ours does not, 22–34 points.
- **Back length in `drops`**: ours −3.7 to −5.4 points (wale) in six of 12 cases.

### Experiments before the calibration (19 Oct)

Before the calibration, the posed errors were chased with four experiments, each a full or partial rerun against CLO (worst zone, points; M unless noted):

| Change | hoods M 178/75 · 180/64 · 176/88 · 192/82 | drops M 178/75 · 180/64 · 176/88 · 192/82 | All 36 |
|---|---|---|---|
| μ 1.0, shear 20 N/m (before calibration) | 3.8 · 3.4 · 9.4 · 5.8 | 3.5 · 24.5 · 22.3 · 3.1 | 10 of 35 |
| μ 0.7 | 15.1 · 2.5 · 10.7 · 13.1 | 4.5 · 2.8 · 22.9 · 3.1 | 13 of 35 |
| μ 0.5 | 16.7 · 18.7 · 14.6 · 17.6 | 4.7 · 3.6 · 24.1 · 3.9 | — |
| Shear 80 N/m (μ 1.0) | 2.3 · 1.0 · 9.5 · 2.0 | 7.6 · 23.3 · 22.1 · 12.8 | 13 of 35 |
| The legs do not carry cloth | — | hem 70–115 mm below CLO's on every body | — |

- **Friction is a threshold.** CLO's jersey stays at the hips in `hoods` and rides some 170 mm up the back in `drops` (measured as the A-pose height of the skin under the hem). At μ 1.0 ours does the first and not the second, at 0.5–0.7 the other way round, and at 0.7 the `hoods` hem rides up on two bodies and not on the other two. The +25 points of drops 180/64 are the hem staying on the buttocks where CLO's has gone up.
- **Shear matters as much and cannot be fitted on the standing case:** across 5–160 N/m the fitted case moves by 0.07 points rms (1.28–1.35), while `hoods` M improves at 80 and `drops` gets worse.
- **Not carrying cloth on the legs** made `drops` worse: the thighs were holding the hem up, not dragging it down. Dropped.
- None of these was adopted on its own: each was chosen by looking at held-out cases. That is what led to the calibration above, on the fitted body and size only.

### Measuring friction and shear (proposal)

The two numbers the poses hang on can be measured in a day with the strip-test rig and kitchen tools; the measured values then go into `KNIT_FRICTION`, `GRIPPER_FRICTION` and `KNIT_SHEAR_N_PER_M` with no fitting, and the 36 cases are run once. That is the honest test of the solver.

**Fabric on skin, μ** (static, as the solver's friction holds until it slips):

1. Cut a 50 × 50 mm patch of the jersey fabric and glue or tape it round a flat block of known mass (100 g and 300 g; a block of wood with washers works). Mark the course direction.
2. Lay it fabric-down on the inner forearm of three people (dry skin, room temperature, arm resting on a table). Pull it level along the arm with a digital force gauge or luggage scale (0.01 N resolution) at about 10 mm/s.
3. Read the peak force when it starts to slide (static) and the steady force while it slides (kinetic). μ = F / (m · 9.81). Five pulls per person, per load, with the course along the pull and across it.
4. The same with a strip of the silicone hem gripper for `GRIPPER_FRICTION`.
5. Without a gauge: a sheet of skin-like silicone (e.g. Ecoflex 00-30, 2 mm, matte) on a board, the block on it, the board tilted slowly until the block slips; μ = tan θ, θ from a phone inclinometer. Less like skin, but repeatable.

Report the mean static μ (the solver's value), the kinetic μ and the spread over people and loads; skin friction varies with load and moisture, so the spread says how much the poses can be trusted.

**Shear modulus G** (formulas.md, "Shear modulus from a bias strip"):

1. On the strip-test rig (50 mm strips, 100 mm gauge length, weights), take the course and wale curves at small strain (0–10 %, at least five points) if they are not already measured: their slopes are E_c and E_w in N/m.
2. While pulling the course strip, mark two lines across it and measure how much narrower it gets: ν_cw = width strain / length strain.
3. Cut three strips at 45° to the course and pull them the same way: E₄₅ is the slope in N/m at small strain.
4. G = 1 / (4/E₄₅ − 1/E_c − 1/E_w + 2ν_cw/E_c). A textile lab with a KES-FB1 shear tester gives it directly (gf/cm/deg × 56.19 = N/m).

The measured course and wale curves would also replace the stand-in tricot and its fitted scales, leaving nothing fitted at all.

### Solver changes made in group 5 (all in `drape.py` / `garment_mesh.py`, with tests)

1. **Lead-in to the pose.** CLO's `hoods` and `drops` runs start from a garment already posed; the first comparison started ours from the A-pose drape inside a posed body, and the garment fell through it (waist strain 300 %, vertices 96 mm inside).
2. **Weld at 1 mm** (spec scenario changed from 0.5 mm): the back pockets' bottom seam lies 0.5–1 mm off the back panel in CLO's drape and was never sewn, so the pocket lifted off like a chord. Pocket triangles in the waist went from −0.6 % to 11.0 % (CLO 8.6 %).
3. **Pockets as a layer** on the back panel (2.2 mm), replacing the extra body distance.
4. **Inelastic contact:** a collision push no longer becomes a velocity off the surface.
5. **Inertia scaling is a parameter**, and **the body carries the cloth on it** (`carry`): with natural mass, 500 × 2 passes did not converge (every stiffness gave the same drape, 3.46 points rms); with inertia × 1000 the cloth could not follow a body that got shorter (hem 156 mm high on standing 178/75).
6. **Friction on the position, μ = 1.0.** Velocity-level friction leaked each substep's slide (a sheet held by half its friction crept 2.9 mm/s); it now acts in the collision pass and holds exactly to μ (test). That alone did not stop the creep (hem +95 mm relative to the hips at the end of the hoods lead-in); the coefficient did: 0.3 → 87–95 mm, 0.6 → 57 mm, 1.0 → 13 mm. **1.0 was chosen by looking at a held-out pose** (the 178/75 lead-in to `hoods`, before any case frame, but the same motion as the held-out runs). It is not a measured value; a fair test would fit it, or measure it, before looking. A remembered contact force for vertices hovering at the skin was tried and dropped (87 against 95 mm). Per-vertex friction 1.5 under the silicone hem gripper stays.
7. **Shear modulus as a parameter** of `cloth()` (`shear_n_per_m`, tested: a 100 × 10 mm strip under 2 N/m shear moves τ/G · h), so it can be calibrated and later measured.

Full gravity with natural mass was not run: the creep is a balance of forces that friction loses, and the settled balance does not depend on inertia, which the friction sweep above confirms.

Results along the way (all held-out counts): first comparison (no lead-in) 4 of 35, ranking 4 of 12; with lead-in, pocket layer and 1 mm weld 5 of 35, ranking 12 of 12; with the body carrying the cloth 4 of 35; with gripper friction 4 of 35; with friction on the position at 1.0 **10 of 35**, ranking 12 of 12.; with shear as a parameter of `cloth()` and friction and shear calibrated on 178/75 M posed (1.0, 40 N/m) **11 of 33**, ranking 12 of 12.
