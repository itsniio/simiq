# Anny spike: go / no-go

Task fit-engine-poc 2.3. **Status: recommendation written, waiting for team sign-off.**

## The question

Anny has no pose-corrective shapes, so its skin follows the bones by plain linear blend skinning. In deep hip flexion that can collapse the crotch, pinch the front of the hip or over-stretch the buttocks, which is exactly where bib shorts sit (design D3). Can we measure garment zones on an Anny body in `hoods` and `drops`?

## Setup

- Model: `anny.Anny()` defaults: 104-bone `anny` rig, `anny` topology, `local-ref` poses (`simiq_fit.body.load_model`). Anny 0.6.1, torch 2.14.1, macOS arm64.
- Poses: `data/poses/standing.json` (rest A-pose), `hoods.json`, `drops.json`. The left crank is at the top of the stroke, which closes the hip the most; the right is near the bottom.
- Bodies: male average, female average, male heavy, female tall and slim, male short and muscular (`BODIES` in `scripts/anny_spike.py`).
- Run: `uv run python scripts/anny_spike.py`, 10 s after the first model build. Full numbers: [`anny-spike/metrics.md`](anny-spike/metrics.md).

## Results

### The poses reach bike-fit angles

Torso is the line from the hip joints to the shoulder joints.

| | Torso from horizontal | Closed hip angle, crank at top | Knee angle, crank at top / bottom |
|---|---|---|---|
| Target `hoods` | 40–50° | 45–60° | |
| Anny `hoods`, 5 bodies | 41–47° | 54–61° | 62–63° / 137–138° |
| Target `drops` | 25–35° | 40–45° | |
| Anny `drops`, 5 bodies | 25–32° | 35–43° | 62–63° / 137–138° |

### Skin strain by region (share of edges, 5 bodies)

Ratio of each skin edge's length posed to its length at rest. Standing has no artifacts (all regions 0–0.3 %).

| Region | Pose | Compressed below 0.7× | Stretched above 1.4× | Worst 1 % (p1 / p99) |
|---|---|---|---|---|
| Hip front (groin crease) | hoods | 12–16 % | 9–13 % | 0.28–0.34 / 2.3–4.3 |
| Hip front | drops | 13–16 % | 11–16 % | 0.29–0.31 / 2.5–5.0 |
| Buttock and crotch | hoods | 2–3 % | 14–15 % | 0.60–0.66 / 2.3–2.5 |
| Buttock and crotch | drops | 4 % | 15–18 % | 0.53–0.57 / 2.5–2.7 |
| Shoulder | both | 11–14 % | 7–9 % | 0.30–0.35 / 1.8–2.7 |

Whole-body volume drops by 8–10 % in the riding poses.

### What the renders show

`anny-spike/<body>-hips.png` (neutral and strain-coloured close-ups) and `anny-spike/<body>.png`:

- The surface stays smooth: no visible self-intersection, no collapsed crotch, no candy-wrapper twist at the hip or shoulder.
- Strain sits where real skin strains: the buttocks and the front of the knee stretch, the groin crease and the back of the knee compress, the chest stretches and the armpit compresses.
- **But the amount is not physical.** Edges over the buttocks reach 2.5×, and in the groin crease up to 5× their rest length. Real skin over a flexed hip stretches by tens of percent, not by 150 %. Linear blend skinning spreads the buttock surface and folds the crease too much.
- The torso between the waist and the chest, where a jersey's chest and waist girths are taken, shows little strain.

## Decision (recommended, needs sign-off)

| Zone | Measure on posed Anny? | Why |
|---|---|---|
| Jersey: chest girth, waist girth, hem | **Go** | Planar sections of a torso that only the spine bones bend; little strain there |
| Jersey: back length (surface path) | **Go, with a check** | The back stretches smoothly; check against the team's tape deltas (4.4, 7.4) |
| Jersey: sleeve and shoulder | **Go for girth below the armpit; not the armpit itself** | 11–14 % of shoulder edges compress |
| Bib shorts: hip girth, leg opening near the crotch, vertical trunk loop | **No-go on the posed mesh → fallback (a) of design D3** | The loop runs over the buttocks and through the crotch, where skin stretches 2.5–5×; a path length there would be overestimated |

Fallback (a), concretely:

1. Measure the bib zones on the **standing** Anny body.
2. Add a **pose delta per zone** measured with a tape on 3–5 team members, standing and then on a trainer in `hoods` and `drops`: back length (C7 to the back hip line) and the vertical trunk loop (shoulder, front, crotch, back).
3. Store the deltas as data with provenance (`data/`), not as code constants.
4. Revisit (b), corrective vertex offsets for the hip region, only if the fit study shows the bib recommendations miss.

Posed Anny meshes stay fine for the **visuals** in the viewer: the artifacts are in edge lengths, not in what the surface looks like.

## Also found

- Torso and head: the bike-fit torso angle has to be taken from the hip joints to the shoulder joints. An early metric from the root to `spine01` read wrong, because Anny's rest pose leans the lower back slightly backwards.
- Rest volume of `female-tall-slim` (95 L) exceeds `male-average` (84 L): height 0.9 outweighs weight 0.2 more than expected. Task 3.4 (fitting phenotypes to height and mass) has to handle this; the spike does not depend on it.
- glTF export: all 15 meshes reload with the same vertex count (`out/*.glb`, not committed).
- Licenses: see [`licenses.md`](licenses.md).

## Sign-off

_Team decision and names: …_
