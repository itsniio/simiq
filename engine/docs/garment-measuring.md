# Measuring a garment

How the team measures a jersey or bib shorts for a garment record (`data/garments/*.json`, task 5.4). Every number in a record is a **relaxed** garment dimension in cm: the garment lies flat and is never pulled. The fit engine compares these with body measurements (design D6), so a measurement taken under tension makes every size look bigger than it is.

## You need

- a flexible fibreglass tape with mm marks, and a 1 m steel ruler for long straight lines;
- a clean table long enough for the whole garment, and a few strips of masking tape to mark points;
- two people, who measure independently (see "Two measurers").

## Laying flat

1. Close every zip. Turn nothing inside out.
2. Lay the garment front up on the table. Smooth it from the centre outwards with flat hands until there are no ripples, but do not stretch it: lift it and let it settle again if in doubt.
3. Side seams lie exactly on the folds. If a garment has no side seams, fold it so that the front centre line is centred.
4. Measure along straight lines on the table. Read the tape at eye level, to the nearest 0.5 cm.

## Circumferences: measure flat, store doubled

A flat garment shows half of each circumference. Measure the width from fold to fold and **store twice that value** (design D5: "Circumferences measured flat SHALL be stored doubled"). Write down the flat width you read; the doubling happens once, when the record is written, so the sheet and the record can be compared.

## Points of measure

The names are the `pom` keys in the record and in `data/templates/`.

### Jersey

| `pom` | Where | How |
|---|---|---|
| `chest_circumference` | 2.5 cm below the lowest point of the armhole seam | fold to fold, × 2 |
| `waist_circumference` | the narrowest width between the chest line and the hem; if the sides are straight, halfway between them | fold to fold, × 2 |
| `hem_circumference` | the bottom edge, at the top of the silicone gripper | fold to fold, × 2 |
| `sleeve_opening_circumference` | the sleeve's end, at the top of its gripper or hem | edge to edge across the sleeve, × 2 |
| `center_back_length` | lay the jersey front down; from the collar seam at the centre back to the hem at the centre back | straight, along the centre line |
| `sleeve_underarm_length` | from the lowest point of the armhole seam to the sleeve end, along the underarm seam | along the seam |

`sleeve_underarm_length` places the sleeve-opening zone on the body: the upper-arm profile starts level with the armpit (measurements.md), so the zone's `body_at_cm` is this length.

### Bib shorts

| `pom` | Where | How |
|---|---|---|
| `hip_circumference` | front up; 8 cm above the crotch point (where the four leg seams meet), about where the seat is fullest on a standing body (a team convention until the study checks it) | fold to fold, × 2 |
| `leg_opening_circumference` | the leg's end, at the top of the gripper | edge to edge across the leg, × 2 |
| `inseam_length` | from the crotch point to the leg end, along the inner leg seam | along the seam |
| `vertical_loop_length` | front rise + strap + back rise, all of the left side (below) | sum of three |

`inseam_length` places the leg-opening zone: the thigh profile starts level with the crotch, so the zone's `body_at_cm` is this length.

**Vertical loop.** The body counterpart is the vertical trunk girth: shoulder top, down the front, through the crotch, up the back (measurements.md). On the bibs, measure three pieces and add them:

1. *front rise*: from the crotch point up the centre front to the top edge of the front panel, along the centre line;
2. *strap*: the left strap from where it leaves the front panel to where it joins the back panel, lying straight but not stretched;
3. *back rise*: from the crotch point up the centre back to where the left strap joins the back panel, along the straight line between them.

Write all three on the sheet; the record stores the sum.

## Two measurers

Each size is measured by two people who do not see each other's numbers. For every point of measure:

- if the two values differ by **0.5 cm or less**, store their mean;
- if they differ by more, both measure again; if they still differ, a third person measures and the two closest values are averaged. Note this on the sheet.

The record's `provenance` holds both names, the date and `method: "flat x2"` (design D5, "Provenance").

## The measuring sheet

Copy this table for every garment and size; keep the sheets (photos are fine) with the record's pull request.

| Garment, size | `pom` | measurer A (flat) | measurer B (flat) | difference | stored (cm) |
|---|---|---|---|---|---|
| | | | | | |

"stored" is the mean, doubled for circumferences.

## Checking this guide (task 5.3)

Before measuring the Isadore garments, one team member measures one size following this file, then a second member measures the same size using **only this file**, without talking to the first. The guide passes when every point of measure agrees within 0.5 cm; otherwise the unclear step is rewritten and the check repeated. Record the result here:

| Date | Garment, size | Measurer 1 | Measurer 2 | Largest difference | Passed |
|---|---|---|---|---|---|
| | | | | | |
