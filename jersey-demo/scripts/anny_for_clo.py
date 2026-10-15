"""Anny male 178/75 as OBJ avatars for CLO: arms like the CLO avatar, and the hoods pose as a morph target."""
import numpy as np
from simiq_fit.body import fit_body, load_model, pose_body
from simiq_fit.inputs import BodyInputs
from simiq_fit.poses import load_pose, rotation

OUT = "/mnt/user-data/outputs/r56/"
S = np.array([1.102, 1.081, 0.91]); T = np.array([0.0, -0.067, 0.024])  # avatar -> Anny (transfer.py)
model = load_model()
ph = fit_body(model, BodyInputs(sex="male", height_cm=178, weight_kg=75, body_type="regular"))
faces = np.asarray(model.faces)
a20 = pose_body(model, ph, {"upperarm01.L": rotation(0, 20, 0), "upperarm01.R": rotation(0, -20, 0)})["vertices"]
hoods = pose_body(model, ph, load_pose("hoods"))["vertices"]
z0 = a20[:, 2].min()
avatar = np.load("/tmp/claude-0/jersey/work/avatar_v.npy")
trunk = avatar[(avatar[:, 2] > 0.5 * 1.929) & (avatar[:, 2] < 0.8 * 1.929) & (np.abs(avatar[:, 0]) < 0.15)]
c = trunk.mean(0)
shift = (c - (c * S + T))  # Anny trunk centre onto the CLO avatar's, without scaling Anny


def write(v, name):
    v = v.copy(); v[:, 2] -= z0; v = v + shift
    v = np.c_[v[:, 0], v[:, 2], -v[:, 1]] * 100  # CLO: cm, Y up, facing +Z
    with open(OUT + name, "w") as f:
        f.write("# Anny (CC0 assets), male 178 cm 75 kg, units cm, Y up\n")
        f.writelines(f"v {x:.4f} {y:.4f} {z:.4f}\n" for x, y, z in v)
        f.writelines(f"f {a+1} {b+1} {d+1}\n" for a, b, d in faces)
    print(name, v.min(0).round(1), v.max(0).round(1))


write(a20, "anny-m178-75-apose.obj")
write(hoods, "anny-m178-75-hoods.obj")
