"""Fit engine on the RenderHub jersey (size M) for Anny male 178/75: zone strains, painted on Anny."""
import json
import numpy as np
from simiq_fit.body import body_parts, fit_body, load_model, pose_body
from simiq_fit.fit import girth_fit, length_margin_cm, body_value_cm
from simiq_fit.garment import DATA, Fabric
from simiq_fit.inputs import BodyInputs
from simiq_fit.landmarks import load_landmarks
from simiq_fit.measure import girth_sections, measure_body
from simiq_fit.poses import load_pose

OUT = "/tmp/claude-0/jersey/fit/"
SHRINK_WEFT = 0.72  # CLO "Simulation Shrinkage Weft" of the project's pieces
PATTERN = {  # cm, measured on the pattern along the body's lines (pattern_poms.py, poms2/3)
    "chest_circumference": 120.0, "waist_circumference": 110.6, "hem_circumference": 98.0,
    "sleeve_opening_circumference": 33.3, "center_back_length": 59.6,
}
GIRTH_POMS = ("chest_circumference", "waist_circumference", "hem_circumference", "sleeve_opening_circumference")
VARIANTS = {
    "pattern": PATTERN,
    "effective": {k: round(v * SHRINK_WEFT, 1) if k in GIRTH_POMS else v for k, v in PATTERN.items()},
}
ZONES = [  # template jersey zones, sleeve level from the drape (sleeve ends ~13 cm past the armpit)
    ("chest", "chest_circumference", "chest_girth", None),
    ("waist", "waist_circumference", "waist_girth", None),
    ("hem", "hem_circumference", "hip_girth", None),
    ("sleeve_opening", "sleeve_opening_circumference", "upper_arm_girth", 12),
    ("back_length", "center_back_length", "back_length", None),
]
fabric = Fabric.model_validate(json.loads((DATA / "examples" / "fabric-knit.json").read_text()))
model = load_model()
ph = fit_body(model, BodyInputs(sex="male", height_cm=178, weight_kg=75, body_type="regular"))
results = {}
for pose in ("standing", "hoods"):
    m = measure_body(model, ph, pose)
    for variant, poms in VARIANTS.items():
        rows = []
        for zid, pom, body, at in ZONES:
            b = body_value_cm(m, body, at); g = poms[pom]
            if zid == "back_length":
                rows.append(dict(zone=zid, body_cm=round(b, 1), garment_cm=g, strain=round(b / g - 1, 3),
                                 margin_cm=round(length_margin_cm(g, b, fabric.curves["wale"].strain[-1]), 1)))
            else:
                f = girth_fit(b, g, fabric.curves["course"], fabric.specimen_width_mm)
                rows.append(dict(zone=zid, body_cm=round(b, 1), garment_cm=g, strain=round(f["strain"], 3),
                                 ease_cm=None if f["ease_cm"] is None else round(f["ease_cm"], 1),
                                 pressure_pa=None if f["pressure_pa"] is None else round(f["pressure_pa"]),
                                 flags=f["flags"]))
        results[f"{variant}/{pose}"] = rows
json.dump({"variants": VARIANTS, "results": results}, open(OUT + "fit.json", "w"), indent=1)
for k, rows in results.items():
    print(k); [print("   ", r) for r in rows]

# zone vertex sets on the template, chosen on the standing body
rest = pose_body(model, ph, {})
V = rest["vertices"].astype(float); Fc = np.asarray(rest["faces"])
data = load_landmarks(); lm = data["landmarks"]
parts = body_parts(model)
sec = girth_sections(V, Fc, parts, lm, data["waist_ring"])
torso_v = np.unique(Fc[parts["torso"]])
def band(point, normal, half=0.025):
    d = (V[torso_v] - point) @ normal
    return torso_v[np.abs(d) < half]
hip_c = V[data["hip_ring"]].mean(0)
sets = {
    "chest": band(sec["chest_girth"]["point"], sec["chest_girth"]["normal"]),
    "waist": band(sec["waist_girth"]["point"], sec["waist_girth"]["normal"]),
    "hem": band(hip_c, np.array([0, 0, 1.0])),
}
arm = []
for side in ("L", "R"):
    a = V[lm[f"armpit.{side}"]]
    d = np.linalg.norm(V - a, axis=1)
    arm.append(np.where((d > 0.10) & (d < 0.14) & (np.abs(V[:, 0]) > abs(a[0]) + 0.01) & (V[:, 2] > a[2] - 0.25))[0])
sets["sleeve_opening"] = np.concatenate(arm)
c7, hb = V[lm["c7"]], V[lm["hip_back"]]
sets["back_length"] = np.where((np.abs(V[:, 0]) < 0.03) & (V[:, 1] > 0.02) & (V[:, 2] < c7[2]) & (V[:, 2] > hb[2]))[0]
np.savez(OUT + "zones.npz", **sets)
for pose in ("standing", "hoods"):
    np.save(OUT + f"anny_{pose}.npy", pose_body(model, ph, load_pose(pose))["vertices"])
np.save(OUT + "faces.npy", Fc)
print({k: len(v) for k, v in sets.items()})
