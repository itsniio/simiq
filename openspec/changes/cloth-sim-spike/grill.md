# Grill: founder rulings for cloth-sim-spike

Typed answers from the founder on 2026-10-16, given as choices in the session where the spike was planned. Quotes are the chosen options (Slovak), followed by what they decide.

| # | Question | Founder's answer | Decides | Door |
|---|---|---|---|---|
| 1 | What is our own simulation for? | "Výpočet aj vizuál" | Strain and relative pressure over the garment surface feed the fit zones and the viewer. Adopting it revises R1, in a follow-up change after the spike. | one-way (once adopted) |
| 2 | Where does it run? | "Najprv offline, neskôr web" | Python + Warp offline first, results precomputed like the CLO runs; the same algorithm is ported to WebGPU after the pilot. | two-way |
| 3 | When, given demo day on 20 Nov? | "Spike teraz, paralelne" | A time-boxed spike now; demo day stays on the CLO videos and the current engine. | two-way |
| 4 | Where does the garment shape come from? | "Oboje postupne" | Start from a sewn 3D garment with UVs in mm as the flat pattern; DXF and sewing follow once the simulation is validated. | two-way |
| 5 | When has the spike passed? | "Zhoda s CLO" | On 4 bodies × 3 poses: per-zone strain within ±3 percentage points of CLO, the same size ranking, one garment on one body under 60 s on the Mac. | two-way |
| 6 | How long? | "1 týždeň" | Until Fri 23 Oct 2026, then a go/no-go. | two-way |

Not ruled yet: who in track F owns the spike next to the engine PRs; whether pressure is ever checked with a sensor on people (option offered, not chosen for the spike).
