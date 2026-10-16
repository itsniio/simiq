"""One PC2 in the hoods pose: 178/75 -> 180/64 -> 176/88 -> 192/82 -> 178/75, starting where the CLO scene stands now."""
import json, struct, sys
from pathlib import Path
import numpy as np
from simiq_fit.body import fit_body, load_model, pose_body
from simiq_fit.inputs import BodyInputs
from simiq_fit.poses import POSES_DIR, rotation

OUT = Path(sys.argv[1])
SEQ = [(178, 75), (180, 64), (176, 88), (192, 82), (178, 75)]
LEAD, MORPH, HOLD = 15, 45, 45
model = load_model()
start = {"upperarm01.L": [0, 20, 0], "upperarm01.R": [0, -20, 0]}
end = json.loads((POSES_DIR / "hoods.json").read_text())["rotations_deg"]
bones = sorted(set(start) | set(end))
def posed(ph, f):
    return pose_body(model, ph, {b: rotation(*((1 - f) * np.array(start.get(b, [0, 0, 0])) + f * np.array(end.get(b, [0, 0, 0])))) for b in bones})["vertices"].astype(float)
def phen(h, w):
    return fit_body(model, BodyInputs(sex="male", height_cm=h, weight_kg=w, body_type="regular"))
ref = np.loadtxt([l for l in open(OUT.parent / "anny-m178-75-apose.obj") if l.startswith("v ")], usecols=(1, 2, 3))
p0 = phen(178, 75); a0 = posed(p0, 0.0); z00 = a0[:, 2].min()
shift = np.array([np.mean(ref[:, 0] / 100 - a0[:, 0]), np.mean(-ref[:, 2] / 100 - a0[:, 1]), np.mean(ref[:, 1] / 100 - (a0[:, 2] - z00))])
def clo(v, z0):
    return np.c_[v[:, 0] + shift[0], v[:, 2] - z0 + shift[2], -(v[:, 1] + shift[1])] * 100
hoods = []
for h, w in SEQ:
    ph = phen(h, w); z0 = posed(ph, 0.0)[:, 2].min()
    hoods.append(clo(posed(ph, 1.0), z0))
old = np.fromfile(OUT.parent / "anny-m178-75-to-hoods.pc2", dtype="<f4", offset=32).reshape(-1, len(ref), 3)[-1]
print("start vs previous animation end (cm):", float(np.abs(hoods[0] - old).max()))
frames = [hoods[0]] * LEAD
marks = {}
for i in range(1, len(SEQ)):
    for k in range(1, MORPH + 1):
        f = k / MORPH; f = f * f * (3 - 2 * f)
        frames.append((1 - f) * hoods[i - 1] + f * hoods[i])
    marks[f"{SEQ[i][0]}-{SEQ[i][1]}"] = len(frames) + HOLD // 2
    frames += [hoods[i]] * HOLD
with open(OUT / "anny-hoods-body-sequence.pc2", "wb") as fh:
    fh.write(struct.pack("<12siiffi", b"POINTCACHE2\0", 1, len(ref), 0.0, 1.0, len(frames)))
    for fr in frames:
        fh.write(fr.astype("<f4").tobytes())
json.dump({"frames": len(frames), "fps": 30, "mid_hold_frame": marks}, open(OUT / "anny-hoods-body-sequence.json", "w"), indent=1)
print(len(frames), marks)
