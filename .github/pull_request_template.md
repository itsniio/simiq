## What
<!-- One paragraph. A diagram or pseudocode when the shape matters. -->

## Why
Closes #

## Evidence
<!-- From a real run: test output, before/after screenshots, a recording, the fit evaluation report. -->

## Door
<!-- One-way (hard to reverse: public API or loader contract, data schema, privacy, deploy) or two-way. -->

## Blast radius
<!-- core / feature / safe (see .niio.yml) — and the files to read closely. -->

## Left undone
<!-- What this PR does not do that the task mentions. -->

## Decisions made on my own
<!-- Anything the spec did not decide. -->

## Disclosure
<!-- Parts written by an agent that the author does not fully understand. "None" is an answer, and the only one for core paths. -->

- [ ] Tests added first (TDD) and passing
- [ ] Every new formula has a hand-computed test and a derivation in `engine/docs/`
- [ ] No body data in logs, events, fixtures or git
- [ ] No hardcoded UI strings (i18n test green)
- [ ] `openspec validate --all --strict` passes and the task is ticked in `tasks.md`
