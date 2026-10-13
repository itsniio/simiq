# Tasks

## 1. Environment and first body

- [x] 1.1 Set up a Python project with a pinned Anny version and a lock file; verify a fresh clone installs and generates a default body mesh from a script
- [x] 1.2 Export the default body as glTF and OBJ in metres, Y up, facing positive Z, origin between the feet; verify both files open in Blender at the correct scale and orientation
- [x] 1.3 Build a minimal three.js page that loads the glTF and lets the user rotate it; verify the body appears at the expected size in a browser

## 2. Body from minimal inputs

- [x] 2.1 Map gender, height, and weight to Anny parameters; verify a test that the virtual height of the produced body is within 1 cm for ten height and weight combinations
- [x] 2.2 Map the three body silhouettes and the optional per-limb silhouettes to shape parameter priors; verify a test that "athletic" yields larger chest and shoulder width than "slim" at the same height and weight
- [x] 2.3 Validate inputs against plausible adult ranges and mutual consistency with a reason naming the field; verify tests for out-of-range height and for a chest value inconsistent with weight and height
- [x] 2.4 Make generation deterministic; verify a test that two calls with identical inputs produce vertex-identical meshes

## 3. Virtual tape

- [x] 3.1 Define landmark vertex indices (C7, acromions, chest level, waist level, hip level, wrists, elbows, hem line) on the pinned Anny topology and store them as named constants; verify a test checks their positions on a reference body against expected coordinates
- [x] 3.2 Implement circumferences as slice perimeters at landmark heights and lengths as landmark-to-landmark distances, following the lab measurement protocol definitions; verify a test that each item in the lab list is returned in centimetres
- [ ] 3.3 Cross-check the virtual tape against hand measurements of the two founders generated from their own full inputs; verify each virtual value is within 3 cm of the tape value and record the differences in a note

## 4. Optional measurements

- [x] 4.1 Implement a least-squares fit of shape parameters to supplied optional measurements with the minimal-input prior; verify tests that a supplied chest and a supplied torso length are each reproduced within 1 cm while height stays within 1 cm
- [x] 4.2 Verify unsupplied measurements stay within their error bands when optional inputs are added; verify a test over ten random riders

## 5. Error bands and next input

- [x] 5.1 Estimate per-measurement error bands by sampling bodies consistent with the supplied inputs; verify a test that every measurement has a non-zero band from minimal inputs and the chest band shrinks when chest is supplied
- [x] 5.2 Implement "most informative next input" for jersey fit from the bands of chest, torso length, and shoulder width; verify a test that the suggestion changes after that input is supplied

## 6. Poses

- [x] 6.1 Implement the standing pose with arms slightly forward matching the lab's arms-forward photo; verify a test that topology is unchanged and the export loads
- [x] 6.2 Implement the riding pose driven by an aggressiveness value (hip flexion, spine curvature, shoulder protraction, arms to hoods); verify a test that increasing aggressiveness lowers the torso angle and increases surface back length
- [ ] 6.3 Visually compare the riding pose at two aggressiveness values against the founders' own on-bike photos from the garment spike self-check; verify a side-by-side image is saved with notes on mismatches

## 7. Body contract and evaluation

- [x] 7.1 Write the body contract document (parameters, mesh format, orientation, poses, landmarks, measurement list, error bands) in the repo; verify the garment-sim-spike can dress an exported body using only that document
- [x] 7.2 Write the evaluation script that reads the lab dataset export and reports error per measurement for minimal and minimal-plus-optional inputs next to tape noise; verify it runs on a synthetic dataset with known errors and reports them correctly
- [x] 7.3 Define the candidate interface so a second body model (SMPL via Meshcapade) can be scored by the same script; verify a stub candidate that returns constant measurements runs through the script end to end

## 8. After the fit lab

- [ ] 8.1 Run the evaluation on the real lab export; verify the report is saved with rider count and exclusions
- [ ] 8.2 Record the Anny versus SMPL decision with the numbers that drove it; verify the decision note is saved next to the body contract
