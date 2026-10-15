"""Anny male 178/75 with upper arms lowered by ANGLE degrees, saved for the jersey transfer."""
import sys
import numpy as np
from simiq_fit.body import fit_body, load_model, pose_body
from simiq_fit.inputs import BodyInputs
from simiq_fit.poses import rotation

angle = float(sys.argv[1])
out = sys.argv[2]
model = load_model()
print([b for b in model.bone_labels if "arm" in b.lower() or "shoulder" in b.lower() or "clav" in b.lower()])
ph = fit_body(model, BodyInputs(sex="male", height_cm=178, weight_kg=75, body_type="regular"))
pose = {"upperarm01.L": rotation(0, -angle, 0), "upperarm01.R": rotation(0, angle, 0)}
p = pose_body(model, ph, pose)
v = p["vertices"]
print("hand x range", v[:, 0].min(), v[:, 0].max())
np.save(out, v)
np.save(out.replace(".npy", "_rest.npy"), p["rest_vertices"])
