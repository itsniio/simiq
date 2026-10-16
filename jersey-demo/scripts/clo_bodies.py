"""Anny bodies for CLO: a PC2 per body that morphs from the 178/75 A-pose (where the jersey is draped) into the body, then into hoods."""
import json, struct, sys
from pathlib import Path
import numpy as np
from simiq_fit.body import fit_body, load_model, pose_body
from simiq_fit.inputs import BodyInputs
from simiq_fit.poses import POSES_DIR, rotation

OUT = Path(sys.argv[1])
BODIES = [(180, 64), (176, 88), (192, 82), (178, 75)]
MORPH, SETTLE, POSE, HOLD = 40, 15, 120, 30  # frames at 30 fps

model = load_model()
faces = np.asarray(model.faces)
start = {"upperarm01.L": [0, 20, 0], "upperarm01.R": [0, -20, 0]}
end = json.loads((POSES_DIR / "hoods.json").read_text())["rotations_deg"]
bones = sorted(set(start) | set(end))


def posed(ph, f):
    return pose_body(model, ph, {b: rotation(*((1 - f) * np.array(start.get(b, [0, 0, 0])) + f * np.array(end.get(b, [0, 0, 0])))) for b in bones})["vertices"].astype(float)


def phen(h, w):
    return fit_body(model, BodyInputs(sex="male", height_cm=h, weight_kg=w, body_type="regular"))


# Recover the CLO placement from the OBJ the previous session aligned to the CLO avatar.
ref = np.loadtxt([l for l in open(OUT.parent / "anny-m178-75-apose.obj") if l.startswith("v ")], usecols=(1, 2, 3))
a_ref = posed(phen(178, 75), 0.0)
z0_ref = a_ref[:, 2].min()
shift = np.array([
    np.mean(ref[:, 0] / 100 - a_ref[:, 0]),
    np.mean(-ref[:, 2] / 100 - a_ref[:, 1]),
    np.mean(ref[:, 1] / 100 - (a_ref[:, 2] - z0_ref)),
])


def clo(v, z0):
    return np.c_[v[:, 0] + shift[0], v[:, 2] - z0 + shift[2], -(v[:, 1] + shift[1])] * 100


base = clo(a_ref, z0_ref)
print("placement error vs reference OBJ (cm):", float(np.abs(base - ref).max()))

for h, w in BODIES:
    ph = phen(h, w)
    a = posed(ph, 0.0); z0 = a[:, 2].min()
    target = clo(a, z0)
    frames = []
    for i in range(MORPH):
        f = i / (MORPH - 1); f = f * f * (3 - 2 * f)
        frames.append((1 - f) * base + f * target)
    frames += [target] * SETTLE
    for i in range(1, POSE + 1):
        f = i / POSE; f = f * f * (3 - 2 * f)
        frames.append(clo(posed(ph, f), z0))
    frames += [frames[-1]] * HOLD
    tag = f"anny-m{h}-{w}"
    with open(OUT / f"{tag}-apose.obj", "w") as fh:
        fh.write(f"# Anny (CC0 assets), male {h} cm {w} kg, units cm, Y up\n")
        fh.writelines(f"v {x:.4f} {y:.4f} {z:.4f}\n" for x, y, z in target)
        fh.writelines(f"f {p+1} {q+1} {r+1}\n" for p, q, r in faces)
    with open(OUT / f"{tag}-morph-hoods.pc2", "wb") as fh:
        fh.write(struct.pack("<12siiffi", b"POINTCACHE2\0", 1, len(base), 0.0, 1.0, len(frames)))
        for fr in frames:
            fh.write(fr.astype("<f4").tobytes())
    print(tag, "BMI", round(w / (h / 100) ** 2, 1), "frames", len(frames))
