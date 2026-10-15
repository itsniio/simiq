"""Anny body for CLO: A-pose OBJ (arms like the CLO avatar) and a PC2 animation to the hoods pose (cm, Y up)."""
import json, struct, sys
import numpy as np
from simiq_fit.body import fit_body, load_model, pose_body
from simiq_fit.inputs import BodyInputs
from simiq_fit.poses import POSES_DIR, rotation

h, w = float(sys.argv[1]), float(sys.argv[2]); out = sys.argv[3]
tag = f"anny-m{int(h)}-{int(w)}"
FRAMES, HOLD = 120, 30
S = np.array([1.102, 1.081, 0.91]); T = np.array([0.0, -0.067, 0.024])
model = load_model()
ph = fit_body(model, BodyInputs(sex="male", height_cm=h, weight_kg=w, body_type="regular"))
faces = np.asarray(model.faces)
start = {"upperarm01.L": [0, 20, 0], "upperarm01.R": [0, -20, 0]}
end = json.loads((POSES_DIR / "hoods.json").read_text())["rotations_deg"]
bones = sorted(set(start) | set(end))
def posed(f):
    return pose_body(model, ph, {b: rotation(*((1 - f) * np.array(start.get(b, [0, 0, 0])) + f * np.array(end.get(b, [0, 0, 0])))) for b in bones})["vertices"].astype(float)
a20 = posed(0.0); z0 = a20[:, 2].min()
avatar = np.load("/tmp/claude-0/jersey/work/avatar_v.npy")
trunk = avatar[(avatar[:, 2] > 0.5 * 1.929) & (avatar[:, 2] < 0.8 * 1.929) & (np.abs(avatar[:, 0]) < 0.15)]
c = trunk.mean(0); shift = c - (c * S + T)
clo = lambda v: (np.c_[v[:, 0], v[:, 2] - z0 + shift[2], -(v[:, 1] + shift[1])] + np.array([shift[0], 0, 0])) * 100
with open(f"{out}/{tag}-apose.obj", "w") as fh:
    fh.write(f"# Anny (CC0 assets), male {h:g} cm {w:g} kg, units cm, Y up\n")
    fh.writelines(f"v {x:.4f} {y:.4f} {z:.4f}\n" for x, y, z in clo(a20))
    fh.writelines(f"f {a+1} {b+1} {d+1}\n" for a, b, d in faces)
frames = []
for i in range(FRAMES + HOLD):
    f = min(i / FRAMES, 1.0); f = f * f * (3 - 2 * f)
    frames.append(clo(posed(f)).astype("<f4"))
with open(f"{out}/{tag}-to-hoods.pc2", "wb") as fh:
    fh.write(struct.pack("<12siiffi", b"POINTCACHE2\0", 1, len(frames[0]), 0.0, 1.0, len(frames)))
    for fr in frames: fh.write(fr.tobytes())
print(tag, clo(a20).min(0).round(1), clo(a20).max(0).round(1))
