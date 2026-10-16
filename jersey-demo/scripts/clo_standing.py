"""One PC2 continuing from 178/75 in hoods: -> drops, body sequence in drops, -> standing (A-pose arms), body sequence standing."""
import json, struct, sys
from pathlib import Path
import numpy as np
from simiq_fit.body import fit_body, load_model, pose_body
from simiq_fit.inputs import BodyInputs
from simiq_fit.poses import POSES_DIR, rotation

OUT = Path(sys.argv[1])
BODIES = [(178, 75), (180, 64), (176, 88), (192, 82)]
POSE_T, LEAD, MORPH, HOLD = 75, 15, 45, 45
model = load_model()
P = {
    "apose": {"upperarm01.L": [0, 20, 0], "upperarm01.R": [0, -20, 0]},
    "hoods": json.loads((POSES_DIR / "hoods.json").read_text())["rotations_deg"],
    "drops": json.loads((POSES_DIR / "drops.json").read_text())["rotations_deg"],
}
def blend(a, b, f):
    bones = set(P[a]) | set(P[b])
    return {k: rotation(*((1 - f) * np.array(P[a].get(k, [0, 0, 0])) + f * np.array(P[b].get(k, [0, 0, 0])))) for k in bones}
phs = {bw: fit_body(model, BodyInputs(sex="male", height_cm=bw[0], weight_kg=bw[1], body_type="regular")) for bw in BODIES}
def verts(bw, a, b, f):
    return pose_body(model, phs[bw], blend(a, b, f))["vertices"].astype(float)
z0 = {bw: verts(bw, "apose", "apose", 0)[:, 2].min() for bw in BODIES}
ref = np.loadtxt([l for l in open(OUT.parent / "anny-m178-75-apose.obj") if l.startswith("v ")], usecols=(1, 2, 3))
a0 = verts((178, 75), "apose", "apose", 0)
shift = np.array([np.mean(ref[:, 0] / 100 - a0[:, 0]), np.mean(-ref[:, 2] / 100 - a0[:, 1]), np.mean(ref[:, 1] / 100 - (a0[:, 2] - z0[(178, 75)]))])
def clo(v, bw):
    return np.c_[v[:, 0] + shift[0], v[:, 2] - z0[bw] + shift[2], -(v[:, 1] + shift[1])] * 100
def ease(k, n):
    f = k / n; return f * f * (3 - 2 * f)
seq = np.fromfile(OUT.parent / "anny-m178-75-to-hoods.pc2", dtype="<f4", offset=32).reshape(-1, len(ref), 3)
first = clo(verts((178, 75), "apose", "apose", 0), (178, 75))
print("start vs scene (cm):", float(np.abs(first - seq[0]).max()))
frames, marks = [first] * LEAD, {}
def pose_change(a, b):
    for k in range(1, POSE_T + 1):
        frames.append(clo(verts((178, 75), a, b, ease(k, POSE_T)), (178, 75)))
    frames.extend([frames[-1]] * LEAD)
def body_tour(pose):
    shapes = [clo(verts(bw, pose, pose, 0), bw) for bw in BODIES] + [None]
    shapes[-1] = shapes[0]
    order = BODIES[1:] + [BODIES[0]]
    for i, bw in enumerate(order):
        a, b = shapes[i], shapes[i + 1]
        for k in range(1, MORPH + 1):
            f = ease(k, MORPH); frames.append((1 - f) * a + f * b)
        marks[f"{pose}/{bw[0]}-{bw[1]}"] = len(frames) + HOLD // 2
        frames.extend([b] * HOLD)
segments = {}
segments["standing"] = len(frames); body_tour("apose")
with open(OUT / "anny-standing-sequence.pc2", "wb") as fh:
    fh.write(struct.pack("<12siiffi", b"POINTCACHE2\0", 1, len(ref), 0.0, 1.0, len(frames)))
    for fr in frames:
        fh.write(fr.astype("<f4").tobytes())
json.dump({"frames": len(frames), "fps": 30, "segment_start": segments, "mid_hold_frame": marks}, open(OUT / "anny-standing-sequence.json", "w"), indent=1)
print(len(frames), segments, marks)
