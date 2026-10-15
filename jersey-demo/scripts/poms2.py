exec(open("/tmp/claude-0/jersey/scripts/pattern_poms.py").read().split("landmarks = load_landmarks()")[0])
landmarks = load_landmarks()["landmarks"]; waist_ring = load_landmarks()["waist_ring"]
sec = girth_sections(V, F, body_parts(model), landmarks, waist_ring)
POCKET, BACK, COLLAR = "Pattern2D_427952", "Pattern2D_428450", "Pattern2D_419254"
def cut(point, normal, keep, only=None, skip=()):
    t2 = t3 = 0.0
    for name, (v, f, uv) in pieces.items():
        if name in skip or (only and name not in only): continue
        segs, fidx = trimesh.intersections.mesh_plane(trimesh.Trimesh(v, f, process=False), normal, point, return_faces=True)
        for (a, b), fi in zip(segs, fidx):
            if not keep((a + b) / 2): continue
            t2 += np.linalg.norm(bary(a, v[f[fi]]) @ uv[f[fi]] - bary(b, v[f[fi]]) @ uv[f[fi]]) / 10
            t3 += np.linalg.norm(a - b) * 100
    return round(t2, 1), round(t3, 1)
torso = lambda m: abs(m[0]) < 0.19
res = {}
res["chest"] = cut(sec["chest_girth"]["point"], sec["chest_girth"]["normal"], torso)
res["waist"] = cut(sec["waist_girth"]["point"], sec["waist_girth"]["normal"], torso, skip=(POCKET,))
allv = np.concatenate([p[0] for n, p in pieces.items() if n != POCKET])
front = allv[allv[:, 1] < -0.05]
zf = front[:, 2].min()
res["hem (3 cm above front hem)"] = cut(np.array([0, 0, zf + 0.03]), np.array([0, 0, 1.0]), torso, skip=(POCKET,))
c7 = V[landmarks["c7"]]
res["centre back (back piece)"] = cut(np.array([0.0, 0, 0]), np.array([1.0, 0, 0]), lambda m: m[1] > 0, only=(BACK,))
print(res, "front hem z", round(zf, 3))
