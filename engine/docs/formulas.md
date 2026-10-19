# Formulas

Every formula in `engine/` with its derivation and the test that checks it with hand-computed numbers (CLAUDE.md, "Understanding is the bar").

## Body fit (task 3.4, `body.py`)

### Standing height

Anny works in metres with z up. In the rest pose the body stands upright, so its height is the vertical extent of the mesh:

    height_cm = (max z − min z) × 100

The top of the head is the highest vertex and the sole the lowest; the A-pose arms stay below the head.

Test: a unit cube is 1 m tall → 100 cm (`test_height_is_the_vertical_extent_in_cm`).

### Mass from volume

For a closed triangle mesh, the divergence theorem turns the volume integral into a sum over faces. Each face (a, b, c) and the origin span a tetrahedron with signed volume

    V_face = a · (b × c) / 6

Faces pointing away from the origin add volume, faces pointing towards it subtract, so the sum is the enclosed volume whatever the origin. The sign depends on whether the faces are wound outward or inward, so we take the absolute value. Then

    mass_kg = |Σ V_face| [m³] × 1000 [L/m³] × BODY_DENSITY_KG_PER_L

`BODY_DENSITY_KG_PER_L` = 1.03, the starting value of design D2; it is retuned against study participants only by its own PR with before/after numbers.

Tests: a unit cube is 1 m³ = 1000 L → 1000 × 1.03 = 1030 kg, with either face winding (`test_mass_is_volume_times_density`, `test_mass_does_not_depend_on_face_orientation`).

Anny's eyes are closed meshes inside the head and are counted too; they add about 15 mL, under 0.03 % of an adult's volume.

### Age

Anny's age parameter is not linear in years. Anny ships its own calibration (`anny/data/shape_calibration/boys.pth` and `girls.pth`, the same anchors in both):

| Years | 0 | 1 | 4 | 11 | 16 | 18 | 64 | 110 |
|---|---|---|---|---|---|---|---|---|
| Anny age | 0 | 0.05 | 0.215 | 0.415 | 0.67 | 0.77 | 0.83 | 1 |

`anny_age(years)` interpolates linearly between the anchors. Without an age the body is built for `DEFAULT_AGE` = 35:

    anny_age(35) = 0.77 + (35 − 18) / (64 − 18) × (0.83 − 0.77) = 0.79217

Tests: the anchors 16, 18 and 64, and 35 and 90 by the formula above (`test_anny_age_interpolates_annys_calibration`).

### Fitting height, weight and muscle

Sex, age and proportions are fixed by the inputs (proportions at 0.5 until task 3.3 maps the body types). Three Anny parameters are fitted, all in [0, 1]: `height` h, `weight` w and `muscle` m, against the given height H and weight M and a prior on muscle, m₀ = `DEFAULT_MUSCLE` (task 3.3 will set m₀ per body type). The residuals, each divided by the size that counts as "close enough":

    r₁ = (height_cm(mesh) − H) / FIT_STOP_HEIGHT_CM
    r₂ = (mass_kg(mesh) − M) / (FIT_STOP_MASS_SHARE · M)
    r₃ = (m − m₀) / FIT_MUSCLE_PRIOR_SD

**How weight and muscle interact in Anny.** Anny blends MakeHuman targets defined at muscle 0, 0.5 and 1 and weight 0, 0.5 and 1, linearly between those anchors, so mass has kinks at the anchors. `scripts/body_ranges.py` (run 2026-10-14) shows that muscle changes how far the weight parameter reaches, not just "strength":

| Body (height parameter) | weight 0 → 1 at muscle 0 | at muscle 0.25 | at muscle 0.5 |
|---|---|---|---|
| Woman, 21, 165 cm | 37 → 96 kg (BMI 13.5–35.0) | 42 → 78 kg (15.4–28.5) | 48 → 62 kg (17.5–22.7) |
| Man, 35, 190 cm | 58 → 154 kg (BMI 16.1–42.7) | 68 → 121 kg (18.8–33.5) | 78 → 93 kg (21.8–25.8) |

(proportions 0.5). At low weight more muscle adds mass; at high weight it removes mass. Hence:

- **m₀ = 0.25**, between the min and average anchors and away from their kinks. There the weight parameter alone covers roughly BMI 15–34. A first version with m₀ = 0.5 failed for common bodies (a 173.8 cm, 59.3 kg man; a 165.3 cm, 72.7 kg woman), because at m = 0.5 Anny's weight range is only about 5 BMI points wide.
- **Muscle is fitted too**, with the prior keeping it at m₀ whenever weight alone can match the mass (then all three residuals can be zero, the least-squares minimum). Only when w is at a bound does the mass residual pull m away; with `FIT_MUSCLE_PRIOR_SD` = 0.25 against a mass scale of 0.2 % of M, the mass wins by orders of magnitude.

**Steps.** The fit starts from h = 0.5, m = m₀ and the w in `FIT_START_WEIGHTS` = (0, 0.25, 0.5, 0.75, 1) with the smallest Σ r². PyTorch gives the 3 × 3 Jacobian J = ∂r/∂(h, w, m); each step solves J Δ = r in the least-squares sense, freezes a parameter that sits at a bound and is pushed outward (the least-squares problem is re-solved over the remaining columns only; solving with a zeroed column instead made `lstsq` return Δ = 0 now and then, which stalled about one fit in four at the weight bound), and limits each change to `FIT_MAX_PARAMETER_STEP` = 0.25:

    (h, w, m) ← clamp((h, w, m) − Δ, low, high),  low = (0, −0.1, 0),  high = (1, 1.25, 1)

A step is accepted only if it lowers Σ r²; otherwise it is halved, up to `FIT_MAX_HALVINGS` = 8 times (backtracking line search), which keeps a step from overshooting across a kink. The clamp keeps height and muscle where Anny interpolates; only weight may extrapolate, within `FIT_WEIGHT_RANGE` = (−0.1, 1.25) (see the coverage limit below). The fit stops when |r₁| < 1 and |r₂| < 1, that is height within 0.05 cm and mass within 0.2 %, ten times tighter than the spec's 0.5 cm and 2 %. If no halving helps or `FIT_MAX_STEPS` = 30 steps pass, no Anny body in range reaches the inputs and the fit raises an error with the closest height, mass and parameters.

**Coverage limit.** Within [0, 1] Anny reaches about BMI 16–43 for men and 13–37 for women (at muscle 0, proportions 0.5, the tables above). The spec accepts BMI 15–45, so a very heavy woman or a very light man is refused with the error above. Either the spec range narrows, or Anny's extrapolation beyond the anchors is allowed for weight, at the risk of unnatural shapes.

`scripts/thin_bodies.py` (run 2026-10-14) tried that extrapolation below weight 0 for a 25-year-old man at 190 cm and woman at 175 cm (renders `measurements/thin-male.png`, `thin-female.png`). At weight 0 and muscle 0 the man is 58 kg (BMI 16.1) and the woman 43 kg (BMI 13.9), both still human-shaped. Already at weight −0.25 (man 44 kg, BMI 12.3) the pelvis bones stand out of the hips and the waist pinches in, and by −0.5 the body is a skeleton. Extrapolating weight downwards is therefore not usable; the thinnest body Anny models well is about BMI 16 for a man and 14 for a woman.

**Ruling (founders, 2026-10-14):** supported BMI is 14–40 for women and 16–40 for men and `other` (`BMI_RANGES` in `inputs.py`). The upper edge of 40 lies above what the weight parameter reaches for women (about 35–37 at muscle 0); there the fit must lower muscle further or fail. `test_bmi_range_edges_are_matched` fits all four edges at 160 and 190 cm and is the check.

Within [0, 1] three edges are out of reach (run 2026-10-14, age 35): a 160 cm woman at BMI 40 needs 102.4 kg and Anny gives at most 89.7 kg; a 190 cm woman at BMI 14 needs 50.5 kg against a minimum of 52.5 kg; a 190 cm man at BMI 16 needs 57.8 kg against 58.3 kg. Hence `FIT_WEIGHT_RANGE` = (−0.1, 1.25), Anny built with `extrapolate_phenotypes=True` (identical inside [0, 1]; the fit clamps height and muscle there):

- **Up to 1.25:** `scripts/thin_bodies.py heavy` renders a 175 cm woman at weight 1.25 (128 kg, BMI 42) still human-shaped, with a slight crease at the belly; from 1.5 (BMI 49.5) the belly and thighs fold into each other. At 1.25 a woman gains about 20 % mass over weight 1, enough for BMI 40 at 160 and 190 cm.
- **Down to −0.1:** at −0.25 the pelvis bones stand out (above); −0.1 is under half of that, and about 9 % lighter than weight 0 for the 175 cm woman, enough for the two thin edges. The renders at −0.05 and −0.1 are the check.

Tests (`test_body_fit.py`): 172 cm and 68 kg land within 171.5–172.5 cm and 66.64–69.36 kg; 20 seeded random inputs with BMI 18–32 land within 0.5 cm and 2 %; muscle stays at m₀ for 180 cm, 75 kg; the two cases that failed with m₀ = 0.5 are matched.

## Tape measurements (tasks 4.2, 4.3, `tape.py`)

### Girth

A tape measure laid around a body part in a plane reads the length of the shortest closed loop that encloses the cross-section, which is the perimeter of the cross-section's **convex hull**: the tape spans concavities instead of following them (between the shoulder blades, under the buttocks).

1. **Plane section.** For a plane through point p with unit normal n, each vertex gets s = (v − p) · n. A mesh edge with s of opposite signs at its ends crosses the plane at v_a + t (v_b − v_a), with t = s_a / (s_a − s_b). A triangle with mixed signs has exactly two crossed edges and contributes one segment between them; segments that share a crossed edge chain into closed loops.
2. **The loop around the point.** A plane at chest height in the A-pose also cuts the arms. The loops are projected onto two unit vectors spanning the plane; the loop containing p (even-odd rule) is the one measured. If several contain p, the outermost (largest hull) is taken; if none does, the loop nearest to p.
3. **Convex hull perimeter** by Andrew's monotone chain.

Tests (`test_tape.py`), all within 1 mm:

| Shape | Hand-computed girth |
|---|---|
| Cylinder r = 0.15 m | 2π · 0.15 = 0.94248 m |
| Elliptic cylinder a = 0.15, b = 0.10 m | Ramanujan: π[3(a+b) − √((3a+b)(a+3b))] = π[0.75 − √0.2475] = 0.79327 m |
| 0.2 m square with a 0.05 × 0.05 m notch | outline 0.9 m; tape reads the square, 0.8 m |
| Cylinder r = 0.15 cut by a plane tilted 30° | ellipse with semi-axes 0.15 and 0.15 / cos 30° = 0.17321: 1.01669 m |
| Torso r = 0.15 between two arms r = 0.05, one plane | 0.94248 m around the torso point, 2π · 0.05 = 0.31416 m around an arm point |

**One body part's section** (`hull_girth`). A body measurement cuts only one part's faces (measurements.md, "Which faces are cut"), and such a section is open where a neighbouring part was attached. `hull_girth` takes the convex hull of all section points of those faces, which spans the gap as the tape does. Open chains are walked from an end (an edge with one neighbour), so each comes out whole. Test: the r = 0.15 m cylinder with one of its 512 sides removed still reads 2π · 0.15 = 0.94248 m: the hull closes the 1.8 mm gap (2 · 0.15 · sin(π/512)) with the same straight side the polygon had.

**A ring of skin points** (`ring_girth`). The hip girth is taken on a fixed ring of vertices (measurements.md, `hip_girth`). The ring is not planar once posed, so it is centred, its best-fit plane found as the span of its two principal directions (the first two right singular vectors of the centred points), and the tape reads the convex hull perimeter of the ring projected onto that plane. Tests: 256 points on an r = 0.15 m circle tilted 40° and shifted read 2π · 0.15 = 0.94248 m (the 256-gon is 0.024 mm short); a 0.2 m square ring with one point pushed 0.05 m in reads the square's 0.8 m.

A 512-sided polygon underestimates a circle's perimeter by 2πr (π/512)² / 6 ≈ 0.006 mm at r = 0.15 m, far inside the 1 mm tolerance.

### Surface paths

Lengths follow the skin, like a tape laid along it (`surface_arc`, `surface_path`). A path from `start` to `end` lies in a plane through `start` with a given normal; `via`, a third point on the same section, says which way round the section loop to go.

1. Cut the mesh with the plane (as for girths) and take the loop nearest `start`. `start`, `end` and `via` must each lie within `SECTION_SNAP` = 5 mm of that loop, or the path is an error.
2. With i, j, k the loop indices nearest `start`, `end`, `via` and n the loop's length: if (k − i) mod n ≤ (j − i) mod n, `via` lies on the forward arc i → j; otherwise the path walks backward from i to j.
3. The length is the polyline length start → loop[i] → … → loop[j] → end.

Unlike a girth, a path does not bridge concavities: a garment lying on the back or over the shoulder follows the skin there.

Tests (`test_tape.py`), within 1 mm:

| Shape | Path | Hand-computed length |
|---|---|---|
| 0.3 × 0.1 m rectangle | right-side middle to top middle, via the top-right corner | 0.05 + 0.15 = 0.2 m |
| same | same ends, via the bottom | 0.05 + 0.3 + 0.1 + 0.15 = 0.6 m |
| 0.2 m square with a 0.05 m notch | corner to corner along the notched side | 0.2 + 2 × 0.05 = 0.3 m |
| r = 0.15 cylinder, plane tilted 30° | one end of the ellipse's long axis to the other | half of 1.01669 = 0.508345 m |

### Limb profile

Upper-arm and thigh girths are measured on planes perpendicular to the bone axis from `start` to `end`, every `step` (`PROFILE_STEP_CM` = 2 cm in `measure.py`, task 4.3). A girth between two levels is linearly interpolated (`profile_at`); a distance outside the profile is an error rather than an extrapolation.

Test: a truncated cone whose radius falls linearly from 0.079 m by 0.1 m per metre of depth gives 2π(0.079 − 0.1 d) at each level d = 0, 0.02, …, 0.38 m; the profile 0.50, 0.48, 0.46 at 0.02 m steps gives 0.475 at 0.025 m (a quarter of the way from 0.48 to 0.46).

## Uncertainty (task 4.5, `uncertainty.py`)

### Combining two estimates

A measurement predicted from height and weight (SD a) and the shopper's own tape measurement (SD b) are two independent estimates of the same quantity. Weighting each by its inverse variance gives the estimate with the smallest variance, and

    1 / σ² = 1 / a² + 1 / b²,   σ = (1/a² + 1/b²)^(−1/2)

σ is below both a and b, so entering a measurement always narrows the SD. The SDs themselves and their sources are in [measurements.md](measurements.md), "Uncertainty".

Tests (`test_uncertainty.py`): a = 3, b = 4 gives 1/√(25/144) = 12/5 = 2.4; a 100 cm chest gives b = 5 cm and σ = (1/p² + 1/25)^(−1/2) with p the predicted chest SD; the other measurements keep their predicted SDs.

## Fit of a girth or loop zone (tasks 6.1, 6.2, `fit.py`, `fabric.py`)

### Strain and ease

A garment of relaxed circumference C_garment worn on a body of girth C_body (the same zone, in the pose) is stretched by

    ε = C_body / C_garment − 1

ε > 0: the fabric is stretched. ε ≤ 0: the garment is loose, with **ease** = −ε · C_garment = C_garment − C_body cm of spare fabric round the body.

Tests (`test_fit.py`), the spec scenarios: 96 / 84 − 1 = 0.142857 → 14.3 %; 80 / 84 − 1 = −0.047619 → −4.8 %, ease 0.047619 · 84 = 4.0 cm.

### Tension

A strip test pulls a specimen of width w and records force F against strain (`Curve`). The fabric's tension, force per unit width, at strain ε is

    T(ε) = F(ε) / w      [N/m]

with F linearly interpolated between the measured points. Beyond the curve's last point there is no measurement, so nothing is extrapolated: the zone is flagged `out_of_curve` and has no tension or pressure.

Test: the example knit's course curve has 2.0 N at 10 % and 4.5 N at 20 %; at 15 %, F = 3.25 N and on a 50 mm strip T = 3.25 / 0.05 = 65 N/m.

### Pressure (Laplace's law)

A stretched tube of tension T around a cylinder of radius r presses on it with

    P = T / r,   r = C_body / 2π

(the hoop-stress form of Laplace's law; design "Context" and `simiq-prehlad.md` cite the study, https://pmc.ncbi.nlm.nih.gov/articles/PMC8401858/, where this with measured stretch curves predicted pressure on test cylinders mostly within 5 %). The body is not a cylinder, so P is only compared between sizes of the same garment on the same body, where the shape error is the same for all: **relative pressure** = P / the largest P among the sizes (`relative_pressures`). It is never shown as an absolute value.

Tests: at 15 % on a 96 cm girth, r = 0.96 / 2π = 0.152789 m and P = 65 / 0.152789 = 425.42 Pa. Sizes M (84 cm) and L (88 cm) on a 96 cm chest: strains 14.29 % and 9.09 %; F = 2.0 + 0.4286 · 2.5 = 3.0714 N and 0.9091 · 2.0 = 1.8182 N, so T = 61.43 and 36.36 N/m; the radius is the same, so relative pressure is 1.0 for M and 36.36 / 61.43 = 0.592 for L. A strain of 120 / 75 − 1 = 60 % lies beyond the curve's 50 % and is flagged.

### Length margin (task 6.3)

A length zone (back length) does not press on the body; it rides up when too short. The garment can stretch along the measurement until its fabric reaches a comfortable tension, `COMFORT_TENSION_N_PER_M` (one constant, set from the team's try-ons in task 6.3). The strain where the wale curve reaches it, ε_allow, is read off the curve backwards (`comfort_strain`: tension is interpolated as a function of strain, so its inverse is interpolated the same way between the measured points):

    margin = L_garment · (1 + ε_allow) − L_body      [cm]

A negative margin means the garment is short in that pose. If the curve never reaches the comfort tension, ε_allow is the curve's last strain and the zone is flagged `out_of_curve`.

Tests: the spec's back length, 60 · 1.05 − 62 = +1.0 cm. On the example's 50 mm course curve (tensions 0, 40, 90, 150, 220, 300 N/m at 0–50 %) 65 N/m lies halfway between 40 and 90, at 15 %; 400 N/m is never reached.

### Status bands (task 6.4)

Each zone of a brand's fit block has band edges in `data/fit-ranges/<brand>.json` (`default.json` when the brand or fit block has none; the result is then flagged `default_ranges`):

| Zone kind | Edges | Bands |
|---|---|---|
| girth, loop (strain) | a < b < c < d | < a `too_loose`, [a, b) `loose`, [b, c] `ok`, (c, d] `tight`, > d `too_tight` |
| length (margin, cm) | a < b < c | < a `too_short`, [a, b) `short`, [b, c] `ok`, > c `long` |

An edge value itself belongs to the band nearer `ok`. The edges are data with their source (`provenance`), set first from the team's try-ons and then fitted from the study (design D7, D9); the tests use made-up edges.

Test of a whole garment (`test_every_zone_of_every_size`): the example jersey on a body with chest 92 cm. S's chest strain 92/80 − 1 = 15 % lies in (10 %, 20 %] and is `tight`; its back margin with ε_allow = 10.714 % (65 N/m on the wale curve's 60 → 130 N/m between 10 and 20 %) is 60 · 1.10714 − 63 = +3.43 cm, `ok`. Chest tensions 65, 38.10 and 18.18 N/m for S, M and L give relative pressures 1, 0.586 and 0.280.

### Speed (task 6.5)

Five sizes of a jersey from precomputed measurements take well under the spec's 50 ms (`test_five_sizes_take_under_50_ms`, the mean of 10 runs); the work is a few interpolations per zone and size. Measured 2026-10-14 on the Linux VM: 0.05 ms for the example's three sizes, the mean of 100 calls.

## Size recommendation (task 7.1, `recommend.py`)

**Penalty.** Each size's zones carry a status; `BAND_COST` prices it (ok 0; loose, tight, short, long 1; too_loose, too_tight, too_short 3) and the zone's weight from the garment record scales it:

    penalty(size) = Σ_zones weight_zone × BAND_COST[status_zone]

The size with the lowest penalty is recommended.

**Tie-break.** Among sizes with the same penalty, the one whose zones sit nearest the middle of their ok bands wins: Σ weight × |value − (b + c)/2| / (c − b), where [b, c] is the zone's ok band (strain, or margin in cm) and dividing by its width makes strains and centimetres comparable.

**Explanation.** For the sizes next to the recommended one (one smaller, one larger), every zone whose status differs from the recommended size's is listed as (size, zone, status). The viewer turns these into sentences in each language.

Tests (`test_recommend.py`): the spec's clear case, S with a tight chest (weight 2: penalty 2), M all ok (0), L with a loose chest (2): M, explained by (S, chest, tight) and (L, chest, loose). A too_tight chest and a short back: 2 × 3 + 1 × 1 = 7. Tie: M's chest at 9 % is 4 % from the 5 % centre of a 10 %-wide band, 0.4 widths, × 2 = 0.8; L's back at 3.8 cm is 1.8 cm from the 2 cm centre of a 4 cm band, 0.45; L wins.

### Confidence and alternative (task 7.2)

The body's measurements are uncertain (`uncertainty.py`: an SD per measurement for the inputs given). `recommend` draws `SAMPLES` = 64 measurement vectors, each measurement moved by a normal deviation with its SD (a limb profile moved as a whole), recommends a size for each draw, and reports

    confidence = (draws whose size equals the recommendation) / 64

When confidence < `CONFIDENCE_THRESHOLD` = 0.6 the most frequent other size is named as the alternative. The draws use a fixed seed (`SAMPLE_SEED`), so the same request always gives the same confidence.

**Simplification until task 3.5.** Design D8 propagates deviations of the standing girths into the pose through a Jacobian computed with autograd. That needs the step-3 measurements as targets of the body fit (task 3.5). Until then the deviation of a pose measurement is taken equal to the standing one (Jacobian = identity).

Tests (`test_recommend.py`, the example jersey reduced to its chest zone, sizes 80/84/88 cm, ok band 2–6 % strain, SD 0.5 cm): a 87.36 cm chest (M at 4 %, S tight at 9.2 %, L loose at −0.7 %) gives M with confidence 1.0 and no alternative. A 89.4 cm chest falls between M's ok band (up to 84 · 1.06 = 89.04 cm) and L's (from 88 · 1.02 = 89.76 cm): M tight, L loose, equal penalties, and the tie-break prefers L by 0.602 against 0.607 band widths. The draws split: L with confidence 0.53, alternative M.

## Strain and pressure over a draped garment (cloth-sim-spike 3.1–3.3, `surface_strain.py`)

### Course and wale strain (task 3.1)

Each triangle has a rest shape in the flat pattern, corners r₀, r₁, r₂ in (course, wale) mm (`garment_mesh.py`: UV × mm per UV unit × shrinkage), and a draped shape, corners x₀, x₁, x₂ in 3D. Inside a triangle the map from pattern to drape is affine, so its derivative, the **deformation gradient** F (3 × 2), is constant and fixed by the two edges:

    Dm = [r₁ − r₀, r₂ − r₀]   (2 × 2, the rest edges)
    Ds = [x₁ − x₀, x₂ − x₀]   (3 × 2, the draped edges)
    F · Dm = Ds   →   F = Ds · Dm⁻¹

A fabric line of rest length 1 along the course (pattern axis u = (1, 0)) becomes the 3D vector F·u, the first column of F; along the wale, F·v, the second column. Their stretch ratios give

    course strain = |F·u| − 1,   wale strain = |F·v| − 1

the same strain as the fit engine's C_body / C_garment − 1, measured on one triangle. Rigid motion leaves |F·u| and |F·v| unchanged; shear does change the length of the line that slides (it is part of what the stretch measures, not a separate quantity here).

Tests (`test_surface_strain.py`), rest triangle (0, 0), (10, 0), (0, 10) mm: laid in 3D unchanged and turned → 0, 0. Course edge to 12 mm, wale edge to 11 mm → 12/10 − 1 = 0.2 and 11/10 − 1 = 0.1. The wale corner slid 5 mm along the course → F·v = (0.5, 0, 1), |F·v| = √1.25 = 1.118034, wale 11.8 %, course 0. A rest triangle off the axes, (2, 1), (6, 4), (1, 7), with every edge doubled → 100 % both ways.

### Zone means (task 3.2)

A zone is a set of garment triangles (cloth-sim D3). Its value is the area-weighted mean over its triangles i of a per-triangle value sᵢ, with A the triangle's area in the drape (½ |(x₁ − x₀) × (x₂ − x₀)|):

    s̄ = Σ Aᵢ sᵢ / Σ Aᵢ

Triangles without a value (pressure beyond the fabric curve) are left out of both sums. Tests: areas 50 and 150 mm² at 10 % and 30 % → (5 + 45) / 200 = 25 %; a triangle 12 × 11 mm → 66 mm²; a NaN triangle beside a 50 mm² one at 10 % → 10 %.

### Relative pressure from tension and curvature (task 3.3)

Laplace's law for a membrane: a surface under tensions T_c, T_w (N/m) along two perpendicular directions, curved with normal curvatures κ_c, κ_w (1/m) along them, presses on what it lies on with

    p = T_c · κ_c + T_w · κ_w      [Pa]

On a cylinder of radius r with the course round it, κ_c = 1/r and κ_w = 0, so p = T_c / r: the fit engine's hoop formula above. Tension per direction comes from the fabric curve at the triangle's strain (`tension_n_per_m`; zero at or below 0, none beyond the curve, then the triangle has no pressure). The directions are the triangle's own course and wale lines in the drape, F·u and F·v; they are perpendicular only where the fabric is not sheared, and the spike takes them as they are. **κ is the body's** (design D4): taken on the body triangle nearest to the garment triangle, so the garment's own folds do not flip its sign.

**Normal curvature on a triangle mesh.** Each vertex gets a unit normal, the mean of its triangles' normals weighted by the triangle's angle at that vertex (angle weighting keeps it radial on a cylinder however the quads are split; area weighting does not, 1.2° off on the test tube). Across a triangle the normal changes linearly, and the shape operator S (2 × 2, in an orthonormal frame of the triangle's plane) is the map from a step in the plane to the change of the normal it causes:

    S · [x₁ − x₀, x₂ − x₀] = [n₁ − n₀, n₂ − n₀]   (both projected onto the plane)
    S = P_n · P_x⁻¹, then symmetrised (S + Sᵀ)/2

The normal curvature along a unit direction d in the plane is κ(d) = dᵀ S d; a direction off the plane is projected onto it first and normalised. With outward normals, convex surfaces have κ > 0. On a cylinder with vertex normals exactly radial, a step along a chord of angle θ moves the normal by the same chord of the unit circle, 2 sin(θ/2), over a step of 2r sin(θ/2): κ = 1/r exactly; along the axis the normal does not change, κ = 0.

Tests: a tube of 48 chords of 20 mm has r = 20 / (2 sin(π/48)) = 10 / 0.0654031 = 152.8979 mm, and κ = 1/152.8979 round it, 0 along it. The spec's tube of 84 cm on a cylinder of 96 cm: 48 chords of 17.5 mm stretched to 20 mm, strain 20/17.5 − 1 = 0.142857; course tension on the example knit 2.0 + 0.42857 · 2.5 = 3.07143 N over 50 mm = 61.4286 N/m; p = 61.4286 / 0.1528979 = 401.76 Pa (402.04 Pa on the round cylinder of r = 0.96 / 2π, the 0.07 % being the polygon). The same tube on a body meshed with 96 chords of 10 mm: r = 5 / sin(π/96) = 5 / 0.0327191 = 152.8160 mm, p = 401.98 Pa. A tube stretched 20/12 − 1 = 66.7 %, beyond the curve's 50 %, has no pressure anywhere.

As in the fit engine, p is only ever reported relative to the highest among the sizes of the same garment on the same body and pose (`relative_pressures`).

## Drape solver (cloth-sim-spike 4.1–4.3, `drape.py`)

### XPBD step

Extended position-based dynamics (Macklin, Müller, Chentanez 2016). Per substep of length Δt each free vertex is predicted from its velocity and force, x̃ = x + Δt v + Δt² w f (w = 1/m), and then moved to satisfy constraints Cⱼ(x) = 0, each with an energy ½ kⱼ Cⱼ². For one constraint with gradients ∇ᵢC on its vertices and compliance α̃ = 1 / (k Δt²), one update is

    Δλ = (−C − α̃ λ) / (Σᵢ wᵢ |∇ᵢC|² + α̃),   xᵢ ← xᵢ + wᵢ ∇ᵢC Δλ,   λ ← λ + Δλ

with λ starting at 0 each substep and carried over its `ITERATIONS` passes. When the passes converge, C = −α̃ λ, so the constraint pushes with force λ ∇C / Δt² = −k C ∇C, the gradient of its energy: the settled state is the energy minimum whatever Δt is. Velocities are (x − x_before) / Δt, damped by e^(−`DAMPING_PER_S` Δt). Constraints are solved colour by colour (no two in one colour share a vertex), so a run is deterministic.

### Stretch from the fabric curve

A triangle's course strain is |F·u| − 1 (formula above). The fabric curve gives tension T(ε) in N/m, piecewise linear: on the piece holding ε, T = s (ε − ε₀) with slope s and zero-tension strain ε₀ = εᵢ − Tᵢ / s. The triangle's energy for that piece is A_rest ∫ T dε = ½ A_rest s (ε − ε₀)², so the constraint is

    C = |F·u| − 1 − ε₀,   k = A_rest · s,   ∇C on corners 1, 2 = aₖ · (F·u)/|F·u|, corner 0 the negative sum

where (a₁, a₂) is the first column of Dm⁻¹ (F·u = a₁(x₁ − x₀) + a₂(x₂ − x₀)). The force on the cloth is then A_rest · T(ε) exactly, on every piece. Check: a row of a strip of width w and row height h has area w·h and strain ΔL / h, so dE/dΔL = w·T, the strip test's force. Below 0 strain the knit buckles instead of pushing back: compression gets `COMPRESSION_SCALE` × the first slope. The wale likewise; shear C = (F·u)·(F·v), zero while course and wale lines stay square, with k = A_rest · `SHEAR_N_PER_M` (not measured, a guess). A per-triangle multiplier scales k (a zipper tape is `ZIPPER_STIFFNESS` × the knit).

Tests (`test_drape.py`): the example knit's 50 mm strip with 4.5 N on its free edge (90 N/m, the curve at 20 %) settles at 20 % ± 1 point (measured 19.84 % after 4 s). Twice as stiff, 90 N/m is the curve's 45 N/m, between 40 N/m at 10 % and 90 N/m at 20 %: 10 % + 5/50 · 10 % = 11 %.

**Inertia scaling.** XPBD's Gauss-Seidel passes move a heavy vertex by w_heavy / Σw of the error, so a 0.46 kg weight on a 1 g strip (w ratio 10⁴) needs ~10⁴ passes, and a 4.5 N force on a 5 µg vertex predicts metres of motion per substep. `cloth(..., inertia_scale=S)` makes the inertia S × the fabric's mass while the weight stays the fabric's own (a force, not an acceleration). The settled state does not depend on inertia (equilibrium: Σ forces = 0); only how it gets there does. Without it the strip settled at 388 % instead of 20 %, and on the jersey 500 substeps × 2 passes did not converge: all 25 stiffness scales of the fit gave the same drape (3.46 points rms); with S = 1000 the chest ranges from 3.2 to 11.7 % across them. The price is that free cloth falls S times slower (g/S): with S = 1000 the jersey stayed up when the body under it got 14 cm shorter (hem 156 mm above CLO's). Hence `carry`, below. Test: with S = 1, a free sheet falls 46.92 mm in 0.1 s (50 substeps, v ← (v + g dt)·a, a = e^(−k dt): x = g dt² [N + a/(1−a)(N − (1−a^N)/(1−a))]; 45.94 mm continuous).

### Bending

Each interior edge with its two opposite vertices is a hinge, flat at rest (the pattern is flat). With the edge from vertex 0 to 1, opposite vertex 2 at fraction s₂ along it and height h₂ off it (in its own rest triangle), vertex 3 at s₃, h₃ on the other side:

    K₂ = 1/h₂,  K₃ = 1/h₃,  K₁ = −(K₂ s₂ + K₃ s₃),  K₀ = −(K₂ + K₃) − K₁

These are the weights with Σ Kᵢ = 0 and Σ Kᵢ pᵢ = 0 for the flat rest positions pᵢ (the moment along the edge and across it), so L = Σ Kᵢ xᵢ vanishes for any rigid or flat placement, and for a small fold, with the opposite vertices lifted d₂, d₃ off the plane, |L| = d₂/h₂ + d₃/h₃ = θ, the fold angle. Constraint C = |L|, gradient Kᵢ L/|L|, stiffness k = `BENDING_N_M` · 6 |e|² / (A₀ + A₁): the discrete-shell energy 3 k_b |e|² θ² / (A₀ + A₁) of Grinspun et al. 2003 written as ½ k θ².

### Body collision and friction

The body is a closed triangle mesh, normals outward. Once per substep, after the stretch passes and one bending pass, every vertex closer to the body surface than its collision distance d (or inside it) is moved to the closest surface point p plus d along the outward direction. Inside is decided by the sign of the angle-weighted normal and, when that says inside, by the winding number: in the armpit crease the normal's sign called a vertex 4.6 mm outside the body inside it. The closest point is first sought on the body face found nearest last time (the vertex's projection onto that face's plane, if it falls inside the face, is the closest point on it, and the face normal gives the side); otherwise, and for one vertex in 4 each substep, the body's BVH is queried. That cut a collision pass from 15 to 2.4 ms on the jersey. d = `COLLISION_MM` = 4.6 mm, the distance CLO keeps the garment off the avatar (start drape: p1 4.58, median 4.73 mm).

**One layer on another.** Cloth meets cloth in one place, the back pockets on the back panel. The under layer's triangles form a second mesh over the cloth's own positions, refitted each substep; each upper-layer vertex not sewn to the under layer keeps 2.2 mm off it (CLO: pocket p5 6.7–6.8 mm off the body, back panel 4.6 mm), on the side it starts on (the panel's winding is not trusted). Test: a free sheet 0.5 mm above a pinned one settles 2.2 mm above it.

A push is a change of position, and v = (x − x_before)/Δt would turn it into a velocity off the surface: a vertex pushed 1.7 mm flew 366 mm away in the layer test. Contact is therefore inelastic: for a pushed vertex the velocity component away from the surface is removed.

**Friction** acts on the position, in the collision pass (as in position-based dynamics, Macklin et al. 2014): with push d (how far the vertex was moved out) and the substep's slide s_t over the skin (its move since the start of the substep, tangential part), the slide is undone while |s_t| ≤ μ d (static) and shortened by μ d otherwise (kinetic): s_t ← s_t · max(0, 1 − μ d / |s_t|). The first version acted on the velocity instead and leaked the slide each substep had already made, dt² a per substep: a sheet held by half its friction crept 2.9 mm/s, which is a/500 = 0.5 · 0.3 · 9.81 / 500 m per second, and the jersey crept up the body. μ per vertex: `FRICTION` = 1.0 for the knit and 1.5 where a silicone hem gripper lies on the fabric. **1.0 was chosen after the posed cases:** at 0.3 the hem rose 87–95 mm relative to the hips in the 178/75 lead-in to `hoods`, at 0.6 57 mm, at 1.0 13 mm (0.6 measured with a contact memory that was tried and dropped: it changed 95 to 87 mm). That uses information from held-out cases (see the report), and 1.0 is not a measured value for this knit on skin.

Tests: a 40 × 40 mm sheet lying on a box under its weight W = 190 g/m² · (0.04 m)² · 9.81 = 2.98 mN holds under a sideways pull of 0.5 μW and slides under 2 μW (measured: holds to 0.9 μW, slides at 1.1 μW). The spec's tube presses on its cylinder with P = T/r = 402 Pa over 0.96 m × 40 mm, 15.4 N in all; a 5 N pull along it beats μ = 0.3 (4.6 N, it slides 17 mm in 1 s) and not μ = 1.5 (23.2 N; it does not move).

**The body carries the cloth on it.** Before each substep, when the body moves, every vertex within `CARRY_MM` = 10 mm of it (its nearest face and point from the last collision pass) moves by the body's own displacement at that point; the constraints then settle the cloth from there. A tight garment does go where the skin under it goes; this replaces the gravity and friction that would take S times longer with scaled inertia. Test: a tube on a cylinder that slides 50 mm along its axis in 0.5 s moves 50 mm with it (friction alone, before: 42 mm; with the body's velocity also in the friction: 86.6 mm, counted twice).

Tests: the spec's 84 cm tube on a 96 cm cylinder (the cylinder `COLLISION_MM` thinner, so the garment's midsurface lies on 96 cm) settles at 14.29 % course strain with no vertex inside the cylinder.

### Shear modulus from a bias strip (measurement proposal, `cloth_spike.py` `KNIT_SHEAR_N_PER_M`)

The solver's shear constraint C = (F·u)·(F·v) is, for small strains, the engineering shear strain γ, and its energy ½ A G γ² gives a membrane shear stress τ = G γ: G is the fabric's in-plane shear modulus in N/m per radian. Test (`shear_stiffness_is_the_membrane_shear_modulus`): a strip 100 mm wide and 10 mm high, pulled 0.2 N along its top edge, carries τ = 0.2 / 0.1 = 2 N/m; at G = 20 N/m, γ = 0.1 and the edge moves 0.1 × 10 = 1.0 mm (measured 1.05), at G = 40 N/m 0.5 mm (0.54). A square sheet moved 4–5 mm more than that: it bent like a cantilever through its soft compression side, so shear has to be tested on a wide, low strip.

G is measured without a shear tester from three strip tests on the existing rig. With membrane moduli E_c and E_w (the slopes of the course and wale curves at small strain, N/m), E₄₅ that of a strip cut at 45° to the course, and ν_cw the width contraction of a course strip over its stretch, an orthotropic membrane obeys

    1/E₄₅ = ¼ · (1/E_c + 1/E_w + 1/G − 2ν_cw/E_c)   →   G = 1 / (4/E₄₅ − 1/E_c − 1/E_w + 2ν_cw/E_c)

Example with the example knit's 400 and 600 N/m, a bias strip of 100 N/m and ν = 0.3: 4/100 − 1/400 − 1/600 + 0.6/400 = 0.04 − 0.0025 − 0.001667 + 0.0015 = 0.037333, G = 26.8 N/m. A KES-FB1 shear tester gives G in gf/cm/deg; × 56.19 makes N/m per radian (0.00981 N / 0.01 m / (π/180)).

### Shear modulus from a KES-FB1 rigidity (`drape.py` `kes_shear_n_per_m`)

KES-FB1 reports G as shear force per unit width per degree of shear angle, the same quantity as the membrane τ = G γ with γ in degrees. In cN/cm/deg: 1 cN/cm = 0.01 N / 0.01 m = 1 N/m, and per degree is 180/π per radian, so G [N/m per rad] = G [cN/cm/deg] × 57.2958 (in gf/cm/deg × 56.19, 1 gf = 0.981 cN). Test: 1 cN/cm/deg → 57.2958 N/m; the weft-knit range 0.28–1.50 cN/cm/deg (US 6,561,230 B1) has geometric mean √(0.28 × 1.50) = 0.648074, → 37.1319 N/m, which is `KNIT_SHEAR_N_PER_M`. KES measures under a 9.8 cN/cm pretension at up to ±8°, so for a loose knit it reads stiffer than the solver's unloaded small-angle modulus.
