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

**Steps.** The fit starts from h = 0.5, m = m₀ and the w in `FIT_START_WEIGHTS` = (0, 0.25, 0.5, 0.75, 1) with the smallest Σ r². PyTorch gives the 3 × 3 Jacobian J = ∂r/∂(h, w, m); each step solves J Δ = r in the least-squares sense, freezes a parameter that sits at a bound and is pushed outward (its column zeroed, the rest re-solved), and limits each change to `FIT_MAX_PARAMETER_STEP` = 0.25:

    (h, w, m) ← clamp((h, w, m) − Δ, 0, 1)

A step is accepted only if it lowers Σ r²; otherwise it is halved, up to `FIT_MAX_HALVINGS` = 8 times (backtracking line search), which keeps a step from overshooting across a kink. The clamp keeps the parameters where Anny interpolates rather than extrapolates. The fit stops when |r₁| < 1 and |r₂| < 1, that is height within 0.05 cm and mass within 0.2 %, ten times tighter than the spec's 0.5 cm and 2 %. If no halving helps or `FIT_MAX_STEPS` = 30 steps pass, no Anny body in range reaches the inputs and the fit raises an error with the closest height, mass and parameters.

**Coverage limit.** Within [0, 1] Anny reaches about BMI 16–43 for men and 13–37 for women (at muscle 0, proportions 0.5, the tables above). The spec accepts BMI 15–45, so a very heavy woman or a very light man is refused with the error above. Either the spec range narrows, or Anny's extrapolation beyond the anchors is allowed for weight, at the risk of unnatural shapes.

`scripts/thin_bodies.py` (run 2026-10-14) tried that extrapolation below weight 0 for a 25-year-old man at 190 cm and woman at 175 cm (renders `measurements/thin-male.png`, `thin-female.png`). At weight 0 and muscle 0 the man is 58 kg (BMI 16.1) and the woman 43 kg (BMI 13.9), both still human-shaped. Already at weight −0.25 (man 44 kg, BMI 12.3) the pelvis bones stand out of the hips and the waist pinches in, and by −0.5 the body is a skeleton. Extrapolating weight downwards is therefore not usable; the thinnest body Anny models well is about BMI 16 for a man and 14 for a woman.

**Ruling (founders, 2026-10-14):** supported BMI is 14–40 for women and 16–40 for men and `other` (`BMI_RANGES` in `inputs.py`). The upper edge of 40 lies above what the weight parameter reaches for women (about 35–37 at muscle 0); there the fit must lower muscle further or fail. `test_bmi_range_edges_are_matched` fits all four edges at 160 and 190 cm and is the check.

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

A 512-sided polygon underestimates a circle's perimeter by 2πr (π/512)² / 6 ≈ 0.006 mm at r = 0.15 m, far inside the 1 mm tolerance.

### Limb profile

Upper-arm and thigh girths are measured on planes perpendicular to the bone axis from `start` to `end`, every `step` (`PROFILE_STEP_CM` = 2 cm in `measure.py`, task 4.3). A girth between two levels is linearly interpolated (`profile_at`); a distance outside the profile is an error rather than an extrapolation.

Test: a truncated cone whose radius falls linearly from 0.079 m by 0.1 m per metre of depth gives 2π(0.079 − 0.1 d) at each level d = 0, 0.02, …, 0.38 m; the profile 0.50, 0.48, 0.46 at 0.02 m steps gives 0.475 at 0.025 m (a quarter of the way from 0.48 to 0.46).
