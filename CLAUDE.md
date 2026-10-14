# simiq — fit in the riding position

Virtual fitting for tight cycling apparel (jerseys, bib shorts), sold to brands and embedded on their product pages. Pilot brand: Isadore. Demo day: 2026-11-20.

Python 3.12 · uv · Anny + PyTorch (offline only) · FastAPI · pytest · ruff
TypeScript · pnpm · Vite · Preact · Three.js · vitest · Playwright

    bin/setup                          # tools, OpenSpec 1.14.1, pnpm; --check changes nothing
    openspec validate --all --strict   # the spec must stay valid; CI runs the same, pinned
    cd engine && uv run pytest         # once engine/ exists (fit-engine-poc 1.2)
    cd web && pnpm test                # once web/ exists (tryon-viewer-mvp 3.1)

## Sources of truth
Plan: `README.md` (Slovak) — weeks to demo day, tracks, decisions R1–R13, open questions, kill criterion.
Spec: `openspec/changes/<change>/` — `design.md` (decisions D1…, program design), `specs/<capability>/spec.md`
(WHEN/THEN scenarios: the test contract), `tasks.md` (a task's issue number sits next to it), `grill.md`
(founder rulings). Archived into `openspec/specs/` when a change is done.
Research: `simiq-prehlad.md` (Slovak).
Factory: niio's rules come from `itsniio/os.niio.sk` (its `CLAUDE.md` and design R8–R16); this file adapts them.
`.niio.yml`: radius classes and checks per stage (draft until os.niio.sk task 5.2 fixes the schema).
Fresh build: the early-October prototype (`body/`, `garment/`, never pushed) is not carried over. It may be
read for a lesson; its code is never copied in (founder ruling 2026-10-14, README R12).
Design: Figma file NIIO (`nmFcu26FyE2mqlIGnJJ9Vh`), page `simik` (`211:1083`) — the onboarding, studio layout and
product panel; frame map in `openspec/changes/tryon-viewer-mvp/design.md` D4b. The viewer follows it frame by frame.
Backlog: GitHub issues, one per task in `tasks.md`, text taken 1:1 from the task; labels `part:n` · `spec-ready` →
`implement-ready` (human-applied) · `hitl` / `afk`. The task line carries its issue number.

## The workflow
Issue from a template with `Estimate: Nd`, `hitl` or `afk`, `part:n` → `spec-ready` (the change validates)
→ a human applies `implement-ready` → branch → failing test first → implement → PR with the body below
→ a human reads it → merge.
One PR, one behaviour, ≤ ~400 changed lines excluding tests (`large-pr-ok` label with a reason to exceed).
Stacks over parallel master PRs. `/opsx:apply <change>` works through `tasks.md`; tick the task in the same PR.
Everything is `hitl` until the niio runtime picks this repo up (os.niio.sk part 5).
Above one day of work: a grill session first, typed answers for one-way doors, kept in the change's `grill.md`.
Before a change's first `implement-ready` issue, its `design.md` has a Program design section a human approved.

### PR body
What (one paragraph with a diagram or pseudocode when the shape matters) · Why / Closes #n ·
Before/after evidence from a real run (test output, screenshot, recording) · One-way or two-way door ·
Blast radius (`core` / `feature` / `safe`, the paths to read closely) · Left undone ·
Decisions made on my own · Disclosure: parts written by an agent that the author does not fully understand.

### Corrections
A review comment starting `/rule: <text>` is a correction. It becomes a lint or a test where one can be
written, a reviewer line where a specialist review can catch it, a prose rule in this file last — by its
own PR, never auto-merged. The same feedback is never given twice by a human.

## Understanding is the bar
"Not vibecoded" means, mechanically:
- The author can explain every line they merge. What they cannot goes in Disclosure; a PR touching `core`
  paths merges only with Disclosure "None".
- Every formula in `engine/` (strain, tension, Laplace pressure, length margin, penalty, confidence) has a
  derivation in `engine/docs/` and a test with hand-computed numbers; the spec scenarios are those numbers.
- Evidence comes from CI or a recorded run (test output, screenshots, load-test report), never from an agent
  saying "tests pass".
- Numbers that decide a size (fit ranges, thresholds, body density, poses) are constants or data files with
  provenance. Changing one is its own PR with before/after evaluation numbers.
- A check that could not run is `unverified`, never green. The fit evaluation needs `data/private/`, so it runs
  on a founder's machine and its report is attached to the PR; CI cannot claim it.

## Which tool for which file
| Working on | Do this first |
| --- | --- |
| `engine/`, `api/` | superpowers:test-driven-development — pytest, failing test first |
| a screen that exists in Figma | figma MCP — read the frame, never eyeball it |
| `web/viewer`, `web/widget`, `web/demo-shop` | agent-skills:frontend-ui-engineering; the spec's budgets are build checks |
| an HTTP or postMessage contract | agent-skills:api-and-interface-design |
| anything that touches body data | agent-skills:security-and-hardening, then the privacy requirements in the specs |
| a bug | superpowers:systematic-debugging |

## Simplicity — the constraint that outranks the rest
The default failure here is an agent building a framework around a few formulas. A codebase a human can
read start to finish beats a clever one.

- **Plain modules, no layers.** No `services/`, `managers/`, `repositories/`, `utils/`, `helpers/`. `engine/` is
  one flat package of modules named for what they compute. A new package or directory needs a reason in the PR.
- **One way per concern.** When a convention changes, migrate the old code in the same change.
- **No abstraction before the third occurrence.** Two similar things stay duplicated.
- A constant before a setting. A function before a class. A dataclass before a framework. The standard library
  before a dependency. A dependency before a homegrown framework.
- **No setting for a value that has never changed.** "Make it configurable" belongs in Out of scope.
- No class or module whose name ends in `Manager`, `Handler`, `Processor`, `Factory`, `Helper` or `Util`.
- Delete rather than generalize. Equal result with less code wins; a small gain bought with complexity loses.
- Soft size target: 6,000 lines of product code (`engine/src`, `api/src`, `web/*/src`), reported in CI;
  crossing it is a review question, not a build failure.
- Screens are the same: if it needs a tooltip to be understood, redesign it.

## Constraints
- Body data (sex, height, weight, age, silhouettes, girths) may be health data by inference: never logged,
  never stored server-side, never in analytics events, never in git. Study data lives in `data/private/`.
- Body model: Anny only (Apache-2.0 code, CC0 assets). Nothing SMPL-derived, ever.
- No GPL code imported into `engine/` or `api/`; Blender and MakeHuman stay external tools.
- The loader runs on customers' shops: ≤ 10 KB, no uncaught errors, no layout shift.
- Every user-facing string through i18n (Slovak, Czech, English; a test enforces it). Code and specs in
  English; README in Slovak.
- Design tokens only in `web/` — no raw hex outside `tokens.css`.
- One short sentence per function comment max; derivations belong in `docs/`.
- Money (billing, later) is `Decimal`. Never float.
- Never `git add -A` / `git add .` / `git commit -a` (hook refuses). Name the paths.
- No AI attribution trailers in commits or PR bodies.
- This repository is public: no secrets, no personal data, no customer data, no unpublished prices in git.
- A human reads what merges.
