exec(open("/tmp/claude-0/jersey/scripts/pattern_poms.py").read().split("landmarks = load_landmarks()")[0])
landmarks = load_landmarks()["landmarks"]; waist_ring = load_landmarks()["waist_ring"]
sec = girth_sections(V, F, body_parts(model), landmarks, waist_ring)
POCKET = "Pattern2D_427952"
def loops(point, normal, skip=(POCKET,)):
    P, L2 = [], []
    for name, (v, f, uv) in pieces.items():
        if name in skip: continue
        segs, fidx = trimesh.intersections.mesh_plane(trimesh.Trimesh(v, f, process=False), normal, point, return_faces=True)
        for (a, b), fi in zip(segs, fidx):
            P.append((a, b)); L2.append(np.linalg.norm(bary(a, v[f[fi]]) @ uv[f[fi]] - bary(b, v[f[fi]]) @ uv[f[fi]]) / 10)
    P = np.array(P); L2 = np.array(L2)
    parent = {}
    def find(a):
        while parent.setdefault(a, a) != a:
            parent[a] = parent[parent[a]]; a = parent[a]
        return a
    def key(p): return tuple(np.round(p / 0.003).astype(int))
    for a, b in P:
        ra, rb = find(key(a)), find(key(b))
        if ra != rb: parent[ra] = rb
    roots = {}
    seg_lab = np.array([roots.setdefault(find(key(a)), len(roots)) for a, b in P])
    k = len(roots)
    out = []
    for c in range(k):
        s = seg_lab == c
        mid = P[s].mean(axis=(0, 1))
        out.append((round(L2[s].sum(), 1), round(np.linalg.norm(P[s, 0] - P[s, 1], axis=1).sum() * 100, 1), mid.round(2)))
    return sorted(out, key=lambda o: -o[1])[:4]
for key in ("chest_girth", "waist_girth"):
    print(key, loops(sec[key]["point"], sec[key]["normal"]))
p0, nrm = sec["chest_girth"]["point"], sec["chest_girth"]["normal"]
for d in range(0, 16, 2):
    L = loops(p0 - d / 100 * nrm, nrm)
    print("down", d, "cm:", [(a, b, m[0]) for a, b, m in L])
