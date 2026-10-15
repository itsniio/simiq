"""Point Cache 2 animation of Anny from the CLO-like A-pose to the hoods pose, in the CLO frame (cm, Y up)."""
import json, struct
import numpy as np
from simiq_fit.body import fit_body, load_model, pose_body
from simiq_fit.inputs import BodyInputs
from simiq_fit.poses import POSES_DIR, rotation

FRAMES, FPS, HOLD = 120, 30.0, 30
S = np.array([1.102, 1.081, 0.91]); T = np.array([0.0, -0.067, 0.024])
model = load_model()
ph = fit_body(model, BodyInputs(sex="male", height_cm=178, weight_kg=75, body_type="regular"))
start = {"upperarm01.L": [0, 20, 0], "upperarm01.R": [0, -20, 0]}
end = json.loads((POSES_DIR / "hoods.json").read_text())["rotations_deg"]
bones = sorted(set(start) | set(end))
a20 = pose_body(model, ph, {b: rotation(*v) for b, v in start.items()})["vertices"]
z0 = a20[:, 2].min()
avatar = np.load("/tmp/claude-0/jersey/work/avatar_v.npy")
trunk = avatar[(avatar[:, 2] > 0.5 * 1.929) & (avatar[:, 2] < 0.8 * 1.929) & (np.abs(avatar[:, 0]) < 0.15)]
c = trunk.mean(0); shift = c - (c * S + T)
frames = []
for i in range(FRAMES + HOLD):
    f = min(i / FRAMES, 1.0); f = f * f * (3 - 2 * f)  # ease in and out
    pose = {b: rotation(*((1 - f) * np.array(start.get(b, [0, 0, 0])) + f * np.array(end.get(b, [0, 0, 0])))) for b in bones}
    v = pose_body(model, ph, pose)["vertices"].astype(float)
    v[:, 2] -= z0; v = v + shift
    frames.append((np.c_[v[:, 0], v[:, 2], -v[:, 1]] * 100).astype("<f4"))
n = len(frames[0])
with open("/mnt/user-data/outputs/r57/anny-m178-75-to-hoods.pc2", "wb") as fh:
    fh.write(struct.pack("<12siiffi", b"POINTCACHE2\0", 1, n, 0.0, 1.0, len(frames)))
    for fr in frames:
        fh.write(fr.tobytes())
print(n, len(frames), frames[0].min(0), frames[-1].max(0))
