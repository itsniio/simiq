# Tasks

## 1. Riders and garments

- [ ] 1.1 Publish a club sign-up form collecting name, contact, height, weight, and bike type; verify at least 24 sign-ups with tall-thin and short-broad builds present when height and weight are plotted
- [ ] 1.2 Choose the primary race-fit jersey (Isadore by default) and order every size plus one thin base layer model in a size range; verify all sizes received and logged in a garment record
- [ ] 1.3 Decide on the optional second relaxed jersey and order it if chosen; verify the decision and any order are recorded in the garment list
- [ ] 1.4 Book a venue and two session dates in spring 2027, and borrow two trainers from the club; verify dates, venue, and trainer owners are written in the lab plan

## 2. Protocol and forms

- [ ] 2.1 Write the measurement protocol with a definition and picture for every item in the lab list, including torso length; verify two measurers measure one person independently and their values agree within 1.5 cm on circumferences and 1 cm on lengths
- [ ] 2.2 Design the feel chart (front and back outline, eight zones, five-point scale, standing and riding columns, buy question) with the designer; verify a test rider fills it unaided in under two minutes
- [ ] 2.3 Write the Slovak consent form with purpose, retention, withdrawal, and a separate optional tick for body-capture photos; verify it is reviewed by one person outside the team for clarity
- [ ] 2.4 Write per-station checklists (A consent and self-report, B measurements, C try-on, D bike) and the rider ID card template; verify each checklist fits on one page and names what must be ticked before the rider moves on
- [ ] 2.5 Transcribe the brand's size chart and write down the rule that maps tape measurements to a chart size or size set; verify it is applied by hand to three sample riders and gives the expected result

## 3. Lab dataset tool

- [ ] 3.1 Create a Rails app with rider, garment, garment size, measurement set, observation, and consent records matching the fit-ground-truth-dataset spec; verify model tests cover required fields and the rider ID has no identity fields
- [ ] 3.2 Store the identity mapping in a separate table excluded from every export; verify a test shows the export contains no name, email, or phone
- [ ] 3.3 Enforce consent gating so measurements, observations, and photos are rejected without consent, and body-capture photos without the optional consent; verify tests for each rejection
- [ ] 3.4 Capture self-reported gender, height, weight, and silhouette picks through screens matching the Figma onboarding flow; verify a test rider's picks are stored as self-reported and separate from measured values
- [ ] 3.5 Add measurement entry per measurer with torso length required for completeness and duplicate sets retained; verify tests that a second set does not overwrite the first and that a missing torso length flags the rider incomplete
- [ ] 3.6 Add photo upload keyed by rider ID, size, pose, and view, rejecting uploads missing any key; verify tests and a manual upload from a phone on the lab network
- [ ] 3.7 Add feel chart entry requiring all eight zones, the per-size buy decision, and the final chosen size and fit preference; verify tests reject partial charts
- [ ] 3.8 Implement the size chart baseline from the rule in 2.5, recording a set when ambiguous; verify tests against the three sample riders
- [ ] 3.9 Implement withdrawal that excludes a rider from exports and counts the exclusion; verify a test exports with and without a withdrawn rider
- [ ] 3.10 Implement a pseudonymous dataset export (riders, measurements, garments, observations, baseline) in a documented file layout; verify the evaluation script from the body-model-spike reads it

## 4. Garment preparation

- [ ] 4.1 Flat-measure every size of each jersey per the points-of-measure list and enter them in the garment record; verify every size has all measurements
- [ ] 4.2 Test the fabric marker on a scrap for bleed and wash-out, then draw a 3 cm grid on front, back, and both sleeves of every jersey; verify every jersey's grid is complete and legible in a photo
- [ ] 4.3 Photograph each gridded jersey flat and relaxed with a scale reference and upload as the rest-state photo per size; verify every size is no longer flagged as unusable for stretch comparison

## 5. Photo lanes

- [ ] 5.1 Set up two tripod lanes with fixed height and distance, plain background, consistent light, and a scale reference in frame; verify a test photo from each lane shows the reference readable and the full body in frame
- [ ] 5.2 Set up two trainers in the bike lanes with space for front, side, and back shots; verify a test rider on a bike is fully visible from all three positions

## 6. Dry run

- [ ] 6.1 Run the full flow with the founders as riders, including consent, self-report, measurements, two sizes, standing and bike photos, feel charts, and final questions; verify each station's time is recorded and the whole flow is under 50 minutes per rider
- [ ] 6.2 Fix every form, checklist, or tool problem found in the dry run; verify a second founder pass shows no mislabelled photo or missing field

## 7. Sessions

- [ ] 7.1 Run session one with six volunteers in their roles; verify at the end that every rider has consent, a complete measurement set, observations for at least two sizes in both poses, and final answers
- [ ] 7.2 Review session one data within a week, list protocol problems, and apply fixes; verify the fixes are written into the checklists before session two
- [ ] 7.3 Run session two; verify the same completeness check as 7.1 and a total of at least 20 complete riders across both sessions
- [ ] 7.4 Re-photograph each jersey flat after the sessions; verify the post-session rest-state photo is stored alongside the pre-session one for grid drift checks

## 8. After the sessions

- [ ] 8.1 Compute the size chart baseline for every complete rider and the chart's accuracy against chosen sizes; verify the number is written in a results note with the rider count
- [ ] 8.2 Export the pseudonymous dataset and hand it to the body-model-spike and garment-sim-spike evaluation scripts; verify both scripts read it without error
- [ ] 8.3 Write a short retrospective of what the protocol got wrong and what to change for a second gender or garment run; verify it is saved next to the lab plan
