"""Software render of a textured glTF scene (Y up, front +Z): front, side, back."""
import sys, numpy as np, trimesh
from PIL import Image

scene = trimesh.load(sys.argv[1]); out = sys.argv[2]
import json, struct
_b = open(sys.argv[1], "rb").read(); _n = struct.unpack("<I", _b[12:16])[0]; GJ = json.loads(_b[20:20 + _n])
XF = {}
for mesh in GJ["meshes"]:
    mi = mesh["primitives"][0].get("material")
    t = GJ["materials"][mi]["pbrMetallicRoughness"].get("baseColorTexture", {}).get("extensions", {}).get("KHR_texture_transform") if mi is not None else None
    XF[mesh["name"]] = t
meshes = []
for name, node in [(n, scene.graph.geometry_nodes[n][0]) for n in scene.geometry]:
    g = scene.geometry[name]; mat, _ = scene.graph[node]
    v = trimesh.transform_points(g.vertices, mat)
    vis = g.visual; tex = None; base = np.array([0.85, 0.85, 0.85])
    m = getattr(vis, "material", None)
    if m is not None and getattr(m, "baseColorTexture", None) is not None and getattr(vis, "uv", None) is not None:
        tex = np.asarray(m.baseColorTexture.convert("RGBA")).astype(float) / 255
    elif m is not None and getattr(m, "baseColorFactor", None) is not None:
        base = np.asarray(m.baseColorFactor[:3]) / 255.0 if np.max(m.baseColorFactor) > 1 else np.asarray(m.baseColorFactor[:3])
    if name.split("_Shape")[0] in ("MV_Hair", "shoes_l", "shoes_r") or name.startswith(("body", "eye")):
        continue
    uv = getattr(vis, "uv", None)
    if uv is not None:
        uv = np.c_[uv[:, 0], 1 - uv[:, 1]]  # back to glTF (v down)
        t = XF.get(name) or XF.get(name.rsplit("_", 1)[0])
        if t:
            uv = uv * np.array(t.get("scale", [1, 1])) + np.array(t.get("offset", [0, 0]))
    meshes.append((name, v, np.asarray(g.faces), tex, uv, base))
allv = np.concatenate([m[1] for m in meshes if "Stitch" not in m[0]])
lo, hi = np.percentile(allv, 0.5, 0), np.percentile(allv, 99.5, 0)
print("bounds", lo.round(2), hi.round(2))
H = 900; scale = H * 0.92 / (hi[1] - lo[1])
views = []
for yaw in (0, 90, 180):
    r = np.radians(yaw)
    R = np.array([[np.cos(r), 0, np.sin(r)], [0, 1, 0], [-np.sin(r), 0, np.cos(r)]])
    Wd = int(H * 0.75)
    img = np.ones((H, Wd, 3)); zb = np.full((H, Wd), -np.inf)
    c = (lo + hi) / 2
    for name, v, F, tex, uv, base in meshes:
        if "Stitch" in name:
            continue
        P = (v - c) @ R.T
        sx = P[:, 0] * scale + Wd / 2; sy = H / 2 - P[:, 1] * scale; depth = P[:, 2]
        n = np.cross(P[F[:, 1]] - P[F[:, 0]], P[F[:, 2]] - P[F[:, 0]])
        n /= np.linalg.norm(n, axis=1, keepdims=True) + 1e-12
        L = np.array([0.3, 0.5, 1.0]); light = np.abs(n @ L) / np.linalg.norm(L) * 0.65 + 0.35
        for fi in range(len(F)):
            idx = F[fi]; a = np.c_[sx[idx], sy[idx]]
            l0 = np.maximum(np.floor(a.min(0)).astype(int), 0); h0 = np.minimum(np.ceil(a.max(0)).astype(int), [Wd - 1, H - 1])
            if (h0 < l0).any():
                continue
            xs, ys = np.meshgrid(np.arange(l0[0], h0[0] + 1), np.arange(l0[1], h0[1] + 1))
            p = np.c_[xs.ravel(), ys.ravel()] + 0.5
            T = np.array([a[1] - a[0], a[2] - a[0]]).T
            if abs(np.linalg.det(T)) < 1e-9:
                continue
            w = np.linalg.solve(T, (p - a[0]).T).T; w = np.c_[1 - w.sum(1), w]
            m = (w >= -1e-6).all(1)
            if not m.any():
                continue
            w = w[m]; px = p[m].astype(int); z = w @ depth[idx]
            k = z > zb[px[:, 1], px[:, 0]]
            if not k.any():
                continue
            w, px, z = w[k], px[k], z[k]
            if tex is not None:
                t = w @ uv[idx]; th, tw = tex.shape[:2]
                col = tex[np.clip(((t[:, 1] % 1) * (th - 1)).astype(int), 0, th - 1), np.clip(((t[:, 0] % 1) * (tw - 1)).astype(int), 0, tw - 1)]
                keep = col[:, 3] > 0.5  # transparent parts of a graphic leave the cloth below visible
                col, px, z = col[keep, :3], px[keep], z[keep]
            else:
                col = np.tile(base, (len(px), 1))
            zb[px[:, 1], px[:, 0]] = z; img[px[:, 1], px[:, 0]] = col * light[fi]
    views.append(img)
Image.fromarray((np.concatenate(views, 1) * 255).astype(np.uint8)).save(out)
