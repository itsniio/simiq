# Design

## Context

See proposal.md for motivation. Constraints that shape the protocol:

- The lab must run without any product software existing. It collects ground truth; the body spike and the garment spike are compared against it later, in any order.
- Riders are club volunteers available at the start of the cycling season (spring 2027). Each rider gives roughly 45 minutes. Throughput, not rigor, is the binding constraint on the day.
- The target garment class is tight race-fit apparel. The decisive dimensions for a jersey are chest, torso (back) length, shoulder width, and arm length. Fit changes materially between standing and riding posture, so both poses must be captured.
- Budget is a few thousand euros. No pressure sensors, no 3D scanners, no multi-camera rigs.
- Measurements and photos of identifiable people are personal data (GDPR). The company is EU-based.

## Goals / Non-Goals

**Goals:**

- Produce, in one or two sessions, a dataset that can score (a) a body model built from minimal inputs, (b) a fit simulation's per-zone tightness, and (c) a size verdict against the brand's size chart.
- Over-represent the riders a size chart fails: tall and thin, short and broad, long torso, long arms.
- Make every observation traceable to a rider ID, a garment size, and a pose, with no ambiguity.
- Be repeatable for a second gender, a second garment class, or a second brand without redesign.

**Non-Goals:**

- Measuring fabric pressure or objective comfort. Rider-reported feel is the primary truth.
- Precise 3D strain reconstruction. Single-view dot-grid photos give approximate local stretch in camera-facing zones; that is enough to sanity-check a simulator.
- Building the photo-based body capture dataset. A few optional phone photos are collected under separate consent for the future, nothing more.
- Running both genders in the first session.

## Decisions

### One garment line, one gender, all sizes

Run a men's size run first with a single race-fit jersey bought in every size, Isadore by default because it is the intended pilot brand and walking into that meeting with their own jersey already measured is worth more than a neutral choice. A second, more relaxed jersey in all sizes is optional and provides the "designer intent" contrast (the same rider should read as tight-but-right in the race fit and fine in the relaxed one).

Alternative considered: several garments in a few sizes each. Rejected because the key test is "which of two neighbouring sizes fits this rider", which needs every size of one garment, not many garments.

### Each rider tries their chart size plus one neighbour

The chart size is computed from the rider's tape measurements before try-on. The rider wears that size and one neighbour (two neighbours when the chart is ambiguous). This turns every rider into a comparison, not a rating, and makes the "which size would you order" answer meaningful.

Alternative: every rider tries every size. Rejected on throughput.

### Rider-reported feel chart is the primary truth; dot grid is secondary

A front and back body outline with eight zones (collar, shoulders, chest, upper back, belly, lower back and hem, sleeve hem, armpit), each rated on a five-point scale (too tight / tight but right / right / loose / too loose), filled once standing and once on the bike, per size. Followed by "would you buy this size?" per size, and at the end "which size would you actually order?" and "how do you like your kit: race / fitted / relaxed?".

The last question tests the fit-preference step that replaces the reference-garment idea for first-time buyers.

Alternative: pressure sensors or skin markers. Rejected on cost and because the shopper experiences feel, not pressure.

### Dot grid on the garment, photographed at rest and worn

Lay each jersey flat and relaxed on a table and draw a grid with a fabric marker at about 3 cm spacing on front, back, and both sleeves. Skip collar and side panels. Photograph each gridded jersey flat before it is worn; that is the rest state. Worn photos then give local stretch in both directions in camera-facing zones, which is the same quantity the simulator outputs. Budget 30 to 45 minutes of gridding per jersey, done before the day.

Alternative: rely on the garment's own print. Rejected, race jerseys rarely have a usable regular pattern.

### Fixed photo lanes with a scale reference in every frame

Phone on a tripod per lane, fixed height and distance, plain wall, consistent light, a ruler or checkerboard visible in every frame. Standing: front, side, back, arms down, then arms forward. On the bike: hoods and drops, front, side, back. Riders bring their own bike on a borrowed trainer, which captures their real position and removes bike-fit setup.

Alternative: multi-view photogrammetry. Rejected for v1; it would improve strain accuracy but not the decision the lab exists to make.

### Two parallel try-on and bike lanes, two shorter sessions

Four station types, with try-on and bike lanes doubled. Target 24 riders across two sessions (a weekend block and a club evening) rather than one twelve-hour day, which is kinder to volunteers and gives a second chance to fix the protocol between sessions.

### Measurement protocol with duplicate measurements

Two measurers, fixed written definitions with pictures (ISO 8559 conventions where they exist). Every fifth rider is measured twice, by both measurers, so the dataset carries its own estimate of tape noise. Without this, a body model's error cannot be judged against anything.

### The Figma onboarding flow is the self-report form

Riders enter gender, height, weight, and pick silhouettes on the existing prototype screens at the first station. Their picks are stored alongside tape measurements, so the lab also tests whether silhouette choice predicts chest and shoulders well enough to justify its place in the minimal inputs.

### Pseudonymous IDs and separate consent

Every form and photo carries a rider ID assigned at arrival. The ID-to-name sheet is stored separately from the dataset. A one-page Slovak consent form states purpose, retention, and the right to withdraw. A separately ticked optional consent covers a few phone photos in tight clothing for future photo-based capture work.

### Anny first for the body spike, SMPL via Meshcapade as the known fix

Not a lab decision, but the lab's body table is what settles it. The body spike starts on Anny (Apache 2.0, measurement-driven, no scan data) and is scored against the tape measurements. If its errors, especially in riding posture, exceed what the fit verdict can tolerate, the SMPL commercial license is the fallback, and the dataset scores that too.

## Protocol

### Station flow

```
  arrive --> [A] consent + self-report      5 min   rider ID assigned, consent
                 on the prototype                   signed, Figma flow completed
                     |
                     v
             [B] tape measurements         12 min   two measurers, written
                 + height + weight                  protocol, every 5th rider
                     |                              measured twice
                     v
             [C1] [C2] try-on lane         5 min    per size: standing photos,
                 per size                           arms down and forward,
                     |                              feel chart (standing)
                     v
             [D1] [D2] bike on trainer     5 min    per size: hoods and drops,
                 per size                           front / side / back,
                     |                              feel chart (riding),
                     v                              "would you buy this size?"
             done --> final questions,     3 min    "which size would you order?"
                      food                          "race / fitted / relaxed?"
```

About 45 minutes per rider end to end. With two lanes, roughly 12 riders per 3.5-hour session.

### Measurements taken at station B

height, weight, neck, chest (fullest), waist, hips, shoulder width (acromion to acromion), back length (C7 to waist), torso length (C7 to intended hem line), arm length (acromion to wrist), upper arm circumference, wrist, thigh, inseam, calf.

Torso length is mandatory; it is the dimension height and weight predict worst and the one that breaks jersey fit on tall, thin riders.

### Volunteers

Six: one host on consent and the prototype, two measurers, two lane runners, one data wrangler whose only job is that every photo and form carries the right rider ID, size, and pose.

### Before the day, in order

1. Recruit riders with height and weight at sign-up; check the spread covers the chart's edges.
2. Order the primary jersey in every size (and the optional second jersey). Order one thin base layer model for all riders.
3. Write the measurement protocol with definitions and pictures. Print feel charts, consent forms, station checklists.
4. Grid every jersey and photograph each flat at rest.
5. Set up and calibrate two photo lanes; borrow trainers.
6. Dry run with the founders as riders; time every station; fix the forms.

### After the day

1. Compute the size chart baseline per rider from tape measurements. This needs no software.
2. Fit the body model to each rider's minimal inputs, then to minimal plus optional inputs; tabulate error per measurement against tape, with tape noise alongside.
3. Hold feel charts and grid photos for the garment spike; they do not expire.

### Budget

| Item | Rough cost |
|---|---|
| primary jersey, all sizes | 600 to 1,000 EUR |
| optional second jersey, all sizes | 500 to 800 EUR |
| base layers, markers, tapes, scale, tripods, printing | 200 to 300 EUR |
| trainers | borrowed from the club |
| food for 30 people | 150 EUR |

## Risks / Trade-offs

- [Mislabelled photos or forms make observations untraceable] → a dedicated data wrangler, rider ID on a card held in every photo, and a per-station checklist that is ticked before the rider moves on.
- [Rider pool skews toward average builds, teaching nothing about chart failures] → collect height and weight at sign-up and recruit deliberately for the edges before the day.
- [Tape measurements are noisy enough to hide body model error] → duplicate measurements on every fifth rider give a noise floor; written definitions and two trained measurers reduce it.
- [Single-view photos give only approximate strain] → accepted; the feel chart is the primary truth and the grid is a sanity check, not a strain reconstruction.
- [Jerseys stretch out or get sweaty across many riders] → base layer for everyone, riders wear each size briefly, and the rest-state grid photo is taken once before any wear so drift can be seen.
- [Sweat and handling smear the grid] → fabric marker tested on a scrap first; re-photograph the rest state after the session to see how much the grid drifted.
- [Brand size chart is ambiguous for some riders] → record the chart's answer as a set when it is ambiguous; those riders try two neighbours.
- [Consent is incomplete or the data is later unusable] → consent signed before any measurement, optional photo consent as a separate tick, ID-to-name mapping stored apart from the dataset.
- [Session runs long and volunteers burn out] → two shorter sessions, two parallel lanes, and a dry run that times every station.

## Open Questions

- Whether to run the optional second (relaxed) jersey in the first session or defer it to the second session. Does not change the protocol.
- Which club evening and weekend block in spring 2027. Does not change the protocol.
- Whether riders' own bikes cover enough drop-bar positions, or whether one club bike on a trainer should be available for riders arriving without one.
