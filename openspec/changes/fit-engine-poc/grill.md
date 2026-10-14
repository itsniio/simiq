# Grill: founder rulings for simiq

Typed answers from the founder during the planning session on 2026-10-14, kept as the factory requires for work above one day and for one-way doors. Quotes are the founder's own words (Slovak), followed by what they decide.

| # | Question | Founder's answer | Decides | Door |
|---|---|---|---|---|
| 1 | Backend and brand portal stack? (engine is Python because Anny runs on PyTorch; widget and viewer are TypeScript) | "Python + TypeScript" | Python (FastAPI) for engine and API, TypeScript for web. A deviation from niio's Rails default (os.niio.sk R1); the brand portal stack is re-decided before `brand-onboarding` starts. | one-way |
| 2 | When is demo day? | "20.11" | Roadmap ends Friday 2026-11-20; production freeze 2026-11-18. | two-way |
| 3 | Language of repository documents? | "README SK, specky EN" | README in Slovak, specs and code in English. | two-way |
| 4 | How many people will build it? | "3–4 ľudia" | Four tracks: F (engine), W (web/3D), B (business), S (study and measuring). | two-way |
| 5 | First brand? | "pilotna znacka bude isadore" | Path A, a D2C e-shop. Isadore runs a custom shop (Nette), so the pilot integrates with the snippet, not a platform adapter. | two-way |
| 6 | The Figma onboarding with silhouettes? | "pridaj figma je dolezita, myslime, ze je dobre navrhnuta" | Required inputs are the Figma flow's: sex, height, weight, body silhouette; age, region silhouettes and girths are optional. The viewer's form follows the frames. | two-way |
| 7 | Dot-grid strain photos? | "ak v tom vidis zmysel daj ale realne dresy nebudeme mat dlhsie" | Optional, only on the extra jersey the team owns, before it is cut for strip tests; borrowed garments are never marked. | two-way |
| 8 | Can 20–30 riders be found in November? | "uvidime" | Kept as an open risk in README; study rounds stay in T4–T5. | two-way |
| 9 | Build on the early-October prototype? | "we want fresh prototype" | Fresh build; nothing is copied from it. | two-way |
| 10 | Which engineering rules? | "takymi pravidlami by sme chceli aj toto vybudovat - nesmie to mat len vibekodik ale take veci, co naozaj budeme kontrolovat a plne im rozumiet" | niio factory rules from os.niio.sk, adapted in `CLAUDE.md`, with the "understanding is the bar" section. | two-way |

| 11 | Kill criterion and review dates as proposed in README? | "asi okej" | Accepted: reviews on 2026-12-04 and 2027-01-29; stop or change course if the study does not beat Isadore's size chart or no brand signs a pilot with data. | two-way |
| 12 | Where is the onboarding designed? | "https://www.figma.com/design/nmFcu26FyE2mqlIGnJJ9Vh/NIIO?node-id=211-1083" | The Figma page `simik` is the UI contract: three onboarding steps, the studio layout with a product panel and a bike control (`tryon-viewer-mvp/design.md` D4b). | two-way |
| 13 | GitHub issues per task? | "asi mozes ale malo by to byt vlastne zo specky 1:1" | One issue per task in `tasks.md`, its text taken word for word; the task line carries the issue number. | two-way |

From the Figma page itself (designer's notes, to be confirmed by the founders): sex `other` is built as `male`; more than three body types may come; an embed frame is still to be designed.

Not ruled yet (README, Open questions): API host; hip measurement in the flow; mobile and embed frames; definitions of the step-3 measurements.
