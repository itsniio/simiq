"""Relaxed jersey dimensions from the CLO drape on Anny: 3D cuts mapped to pattern (UV mm) lengths."""
import json, struct
import numpy as np
import trimesh
from simiq_fit.body import body_parts, fit_body, load_model, pose_body
from simiq_fit.inputs import BodyInputs
from simiq_fit.landmarks import load_landmarks
from simiq_fit.measure import girth_sections
from simiq_fit.poses import rotation

GLB = "/tmp/claude-0/jersey/clo/anny-jersey-standing.glb"
S = np.array([1.102, 1.081, 0.91]); T = np.array([0.0, -0.067, 0.024])

model = load_model()
ph = fit_body(model, BodyInputs(sex="male", height_cm=178, weight_kg=75, body_type="regular"))
a20 = pose_body(model, ph, {"upperarm01.L": rotation(0, 20, 0), "upperarm01.R": rotation(0, -20, 0)})
V = a20["vertices"].astype(float); F = np.asarray(a20["faces"])
z0 = V[:, 2].min()
avatar = np.load("/tmp/claude-0/jersey/work/avatar_v.npy")
trunk = avatar[(avatar[:, 2] > 0.5 * 1.929) & (avatar[:, 2] < 0.8 * 1.929) & (np.abs(avatar[:, 0]) < 0.15)]
c = trunk.mean(0); shift = c - (c * S + T)


def to_anny(p):  # glTF metres (Y up, front +Z) -> Anny frame of a20
    a = np.c_[p[:, 0], -p[:, 2], p[:, 1]]
    return a - shift + np.array([0, 0, z0])


scene = trimesh.load(GLB)
raw = open(GLB, "rb").read(); n = struct.unpack("<I", raw[12:16])[0]; gj = json.loads(raw[20:20 + n])
pieces = {}
for name in scene.geometry:
    node = scene.graph.geometry_nodes[name][0]; m, _ = scene.graph[node]
    g = scene.geometry[name]
    v = to_anny(trimesh.transform_points(g.vertices, m))
    if name == "Obj_Avatar_Shape":
        print(f"Anny in export vs rebuilt: max {np.abs(v - V).max()*1000:.1f} mm")
        continue
    if name.startswith("Pattern2D"):
        uv = np.asarray(g.visual.uv) * np.array([1, -1])  # pattern mm (v sign irrelevant to lengths)
        pieces[name] = (v, np.asarray(g.faces), uv)
print(len(pieces), "pieces")
for name, (v, f, uv) in pieces.items():  # UV scale check: 3D edge vs 2D edge lengths (drape strain)
    e = f[:, [0, 1]]
    r = np.linalg.norm(uv[e[:, 0]] - uv[e[:, 1]], axis=1) / 1000 / np.maximum(np.linalg.norm(v[e[:, 0]] - v[e[:, 1]], axis=1), 1e-9)
    print(f"  {name}: 2D/3D edge median {np.median(r):.3f}, z {v[:,2].min():.2f}-{v[:,2].max():.2f}")


def bary(p, tri):
    a, b, c = tri
    v0, v1, v2 = b - a, c - a, p - a
    d00, d01, d11, d20, d21 = v0 @ v0, v0 @ v1, v1 @ v1, v2 @ v0, v2 @ v1
    den = d00 * d11 - d01 * d01
    y = (d11 * d20 - d01 * d21) / den; z = (d00 * d21 - d01 * d20) / den
    return np.array([1 - y - z, y, z])


def cut_length(point, normal, keep=lambda mid: True):
    """Pattern length (cm) of the jersey along a plane cut, and its 3D length."""
    total2d = total3d = 0.0
    for name, (v, f, uv) in pieces.items():
        mesh = trimesh.Trimesh(v, f, process=False)
        segs, fidx = trimesh.intersections.mesh_plane(mesh, normal, point, return_faces=True)
        for (p, q), fi in zip(segs, fidx):
            if not keep((p + q) / 2):
                continue
            tri = v[f[fi]]; tuv = uv[f[fi]]
            pu, qu = bary(p, tri) @ tuv, bary(q, tri) @ tuv
            total2d += np.linalg.norm(pu - qu) / 10; total3d += np.linalg.norm(p - q) * 100
    return total2d, total3d


landmarks = load_landmarks()["landmarks"]; waist_ring = load_landmarks()["waist_ring"]
sec = girth_sections(V, F, body_parts(model), landmarks, waist_ring)
out = {}
for key, pom in (("chest_girth", "chest_circumference"), ("waist_girth", "waist_circumference")):
    p, nrm = sec[key]["point"], sec[key]["normal"]
    # the cut through the torso only: drop sleeve pieces crossing the plane beside the body
    l2, l3 = cut_length(p, nrm, keep=lambda mid: abs(mid[0] - p[0]) < 0.22)
    out[pom] = round(l2, 1); print(f"{pom}: pattern {l2:.1f} cm, draped {l3:.1f} cm")


def boundary_length(select):
    """Pattern length (cm) of open edges whose midpoints pass select."""
    total = 0.0
    for name, (v, f, uv) in pieces.items():
        edges = np.sort(np.r_[f[:, [0, 1]], f[:, [1, 2]], f[:, [2, 0]]], axis=1)
        u, cnt = np.unique(edges, axis=0, return_counts=True)
        b = u[cnt == 1]
        mids = (v[b[:, 0]] + v[b[:, 1]]) / 2
        s = select(mids, v[b[:, 0]], v[b[:, 1]])
        total += np.linalg.norm(uv[b[s, 0]] - uv[b[s, 1]], axis=1).sum() / 10
    return total


allv = np.concatenate([p[0] for p in pieces.values()])
zmin = allv[:, 2].min()
hem = boundary_length(lambda m, a, b: (m[:, 2] < zmin + 0.10) & (np.abs(a[:, 2] - b[:, 2]) < 0.5 * np.linalg.norm(a - b, axis=1)) & (np.abs(m[:, 0]) < 0.25))
out["hem_circumference"] = round(hem, 1); print(f"hem: pattern {hem:.1f} cm (open edges within 10 cm of the lowest point)")
# left sleeve end: the open edges farthest along the arm from the left shoulder
xs = allv[allv[:, 0] > 0.15]
far = xs[:, 0].max()
sl = boundary_length(lambda m, a, b: (m[:, 0] > far - 0.06) & (m[:, 2] > zmin + 0.25))
out["sleeve_opening_circumference"] = round(sl, 1); print(f"sleeve opening: pattern {sl:.1f} cm")
# centre back: cut x = 0, back half (+y), below the collar seam
back = lambda mid: mid[1] > V[landmarks["c7"]][1] - 0.15 and mid[2] < V[landmarks["c7"]][2] - 0.005
cb2, cb3 = cut_length(np.array([0.0, 0, 0]), np.array([1.0, 0, 0]), keep=lambda mid: mid[1] > 0.0 and mid[2] < V[landmarks["c7"]][2])
out["center_back_length"] = round(cb2, 1); print(f"centre back (below C7 height): pattern {cb2:.1f} cm, draped {cb3:.1f}")
arm = V[landmarks["armpit.L"]]
print("sleeve end to armpit (3D, along x):", round((far - arm[0]) * 100, 1), "cm; armpit z", round(arm[2], 3))
out["sleeve_underarm_length"] = round(float(np.hypot(far - arm[0], 0.0) * 100), 1)
json.dump(out, open("/tmp/claude-0/jersey/fit/poms.json", "w"), indent=1); print(out)
