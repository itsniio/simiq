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
