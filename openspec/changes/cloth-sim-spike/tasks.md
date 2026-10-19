# Tasks

Time box: Fri 16 – Fri 23 Oct 2026, then go/no-go. Builds on the engine on branch `rp-anny`. Every formula lands with its derivation in `engine/docs/formulas.md` and a test with hand-computed numbers. Issue numbers are added when the issues are created.

## 1. Reference data from CLO

- [x] 1.1 Export from CLO, by script, the jersey draped on all 4 bodies × 3 poses × 3 sizes (course shrinkage scaled by 68.5 / 72 / 75.5 % of 72 %), plus the starting drape on 178/75 `standing`, outside the repository: the garment mesh with UVs once and every case's vertex positions (CLO writes frames only into the FBX cloth cache); verify 37 cases with one mesh and a manifest listing body, pose, size, frame and settling for each
- [x] 1.2 Add `.gitignore` guards for the spike's garment meshes, CLO projects and point caches; verify `git status` shows none of the exported files

## 2. Garment rest state

- [x] 2.1 Implement `garment_mesh.py`: load an OBJ with UVs, split pattern pieces, weld coinciding vertices of different pieces (≤ 0.5 mm, nearest first, never two of one piece), build per-triangle rest frames from UV × the export's mm per UV unit × shrinkage; verify the rest-length, seam and missing-UV scenarios with hand-made meshes
- [x] 2.2 Load the CLO starting drape; verify the welded mesh is one connected garment and print piece count, vertex count, seam length and the pieces' outline length against the DXF

## 3. Strain and pressure fields

- [x] 3.1 Implement per-triangle course and wale strain from the deformation gradient, with the derivation in `formulas.md`; verify the undeformed and uniform-stretch scenarios by hand-computed triangles
- [x] 3.2 Implement zone means on the landmark bands and score the CLO exports from 1.1; verify that on CLO's drapes 176/88 has a higher strain than 180/64 in every girth zone in every pose, as the CLO videos show
  - Verified on the torso girth zones (chest, waist, hem: 27 of 27). The sleeve opening is reported, not claimed: CLO leaves it unstretched (−2.4 to +5.0 %) on every body; decision and numbers in `engine/docs/cloth-sim-spike.md` (16 Oct).
- [x] 3.3 Implement relative pressure from tension and curvature (D4); verify the cylinder scenario (P = T / r) and that M presses more than L on 178/75 `standing`

## 4. Drape solver

- [x] 4.1 Implement XPBD stretch (course, wale, shear) with compliance from the fabric curve, and gravity; verify the hanging-strip scenario at 20 % strain within 1 percentage point
- [x] 4.2 Add bending and body collision with thickness and friction; verify a garment tube on a cylinder settles at 14.3 % course strain with no vertex inside the surface
- [x] 4.3 Drive the body through the point-cache sequence (shared with `jersey-demo/scripts/clo_*.py`); verify the no-penetration and determinism scenarios on 178/75 → 176/88 `hoods`
  - Run 18 Oct: two runs agree to 0.0000 mm; 99.96–100 % of vertices outside at every recorded frame; but up to 4.25 mm inside at the armpit crease, where the posed Anny's arm and torso meet. CLO's own drape of the same case fails the 2 mm limit worse (144 vertices, down to 6.19 mm; drops to 14 mm). Founder ruling 7 (18 Oct): the depth limit is CLO's drape of the same case; ours at the settled frame 204 has no vertex inside (deepest +1.78 mm against CLO's −6.19 mm), so the scenario passes; see `engine/docs/cloth-sim-spike.md`.
- [x] 4.4 Time one garment on one body on the Mac and choose the particle distance (design open question); verify and record the timing in the report

## 5. Comparison and decision

- [ ] 5.1 Fit the course and wale stiffness scales on 178/75 `standing` M against CLO; verify the fitted case agrees within 1 percentage point per zone
  - Run 19 Oct (final solver): course ×2, wale ×4 of the stand-in tricot, 1.35 points rms; chest, waist, hem and sleeve opening miss the 1 point (up to 1.81), so not met; through its full sequence the case ends within 1.6 points. See `engine/docs/cloth-sim-spike.md`.
- [x] 5.2 Run all 35 held-out cases with `engine/scripts/cloth_spike.py` and write `engine/docs/cloth-sim-spike.md` (per-zone table, size ranking, timing, renders side by side); verify the report states pass or fail per the acceptance scenarios
  - Report 19 Oct (final): no-go as specified. Friction 1.0 and shear 40 N/m calibrated on 178/75 M `hoods` and `drops` (a protocol change proposed for the founders: those two cases are no longer held out). Zones within ±3 points on 11 of 33 held-out cases (fail; all of `standing` within 3.3); chest size ranking 12 of 12, no case deeper than CLO's, 58.2–58.4 s per garment (pass). The poses fail in the hem zone; the report proposes measuring fabric-skin friction and shear.
- [ ] 5.3 Founders read the report and sign go or no-go in it; on go, open the follow-up change that revises R1

## Workflow follow-up

- Create GitHub issues for these tasks (text 1:1) and add their numbers here; label `part:7`, `spike`.
- One PR per group (1–5); group 3 can merge before group 4.
