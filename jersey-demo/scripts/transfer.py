"""Register the CLO avatar to Anny and bake the jersey's colours into Anny's UV texture."""
import sys
import numpy as np
import trimesh
from PIL import Image
from scipy.spatial import cKDTree

W = "/tmp/claude-0/jersey/work/"
SIZE = int(sys.argv[1]) if len(sys.argv) > 1 else 2048
COVER_M = 0.035  # skin closer than this to the jersey surface is covered

V = np.load(W + "anny_a20.npy").astype(float)
F = np.load(W + "anny_f.npy")
UV = np.load(W + "anny_uv.npy")
FUV = np.load(W + "anny_fuv.npy")
V[:, 2] -= V[:, 2].min()
A = np.load(W + "avatar_v.npy").astype(float)
J = np.load(W + "jersey_pieces.npz")
n = len(J["names"])
JV = np.concatenate([J[f"{i}_v"] for i in range(n)])
JC = np.concatenate([J[f"{i}_c"] for i in range(n)]).astype(float)
JUV = np.concatenate([J[f"{i}_uv"] for i in range(n)])
JP = np.concatenate([np.full(len(J[f"{i}_v"]), i // 3) for i in range(n)])
JV, keep = np.unique(JV.round(5), axis=0, return_index=True)
JC, JUV, JP = JC[keep], JUV[keep], JP[keep]
ATLAS = np.asarray(Image.open(W + "jersey_pieces_atlas.png")).astype(float)
AH, AW = ATLAS.shape[:2]


def atlas_colour(pts, tree):
    """Texture colour at points: UVs of the 4 nearest jersey vertices of the nearest one's piece."""
    dd, jj = tree.query(pts, k=4)
    same = JP[jj] == JP[jj[:, :1]]
    w = same / np.maximum(dd, 1e-4)
    uv = (JUV[jj] * w[..., None]).sum(1) / w.sum(1, keepdims=True)
    x = np.clip((uv[:, 0] % 1) * (AW - 1), 0, AW - 1).astype(int)
    y = np.clip((1 - uv[:, 1] % 1) * (AH - 1), 0, AH - 1).astype(int)
    return ATLAS[y, x], dd[:, 0]

# per-axis scale and translation, avatar -> Anny, by ICP on the trunk and upper arms
hA, hV = A[:, 2].max(), V[:, 2].max()
band = lambda P, h: P[(P[:, 2] > 0.50 * h) & (P[:, 2] < 0.80 * h) & (np.abs(P[:, 0]) < 0.15)]
src, dst = band(A, hA), band(V, hV)
s = np.array([1.0, 1.0, hV / (hA - 0.05)]); t = np.zeros(3)
t = dst.mean(0) - (src * s).mean(0)
tree_dst = cKDTree(dst)
for it in range(60):
    moved = src * s + t
    dj, j = tree_dst.query(moved)
    dk, k = cKDTree(moved).query(dst)
    lim = max(0.02, 0.08 * 0.9 ** it)
    P = np.r_[src[dj < lim], src[k][dk < lim]]; Q = np.r_[dst[j][dj < lim], dst[dk < lim]]
    for ax in range(3):
        M = np.c_[P[:, ax], np.ones(len(P))]
        s[ax], t[ax] = np.linalg.lstsq(M, Q[:, ax], rcond=None)[0]
d, _ = tree_dst.query(src * s + t)
print("scale", s.round(3), "shift", t.round(3), f"trunk residual mean {d.mean()*100:.2f} cm p90 {np.percentile(d,90)*100:.2f}")
JV = JV * s + t
np.save(W + "jersey_on_anny.npy", JV)

# coverage per Anny vertex and baked texture
mesh = trimesh.Trimesh(V, F, process=False)
jt = cKDTree(JV)
dv, jv = jt.query(V)
covered = dv < COVER_M
nbr = [set() for _ in range(len(V))]
for a, b, c in F:
    nbr[a] |= {b, c}; nbr[b] |= {a, c}; nbr[c] |= {a, b}
for _ in range(3):  # close small holes: a vertex mostly surrounded by covered ones is covered
    share = np.array([covered[list(x)].mean() for x in nbr])
    covered = covered | (share >= 0.6)
np.save(W + "covered.npy", covered)
vcol = np.where(covered[:, None], JC[jv], 200)
np.save(W + "vertex_colours.npy", vcol.astype(np.uint8))
print("covered vertices", covered.sum(), "of", len(V))

img = np.zeros((SIZE, SIZE, 4), np.uint8)
uvp = UV * (SIZE - 1)
for fi in range(len(F)):
    a, b, c = uvp[FUV[fi]]
    lo = np.floor(np.minimum(np.minimum(a, b), c)).astype(int)
    hi = np.ceil(np.maximum(np.maximum(a, b), c)).astype(int)
    xs, ys = np.meshgrid(np.arange(lo[0], hi[0] + 1), np.arange(lo[1], hi[1] + 1))
    p = np.c_[xs.ravel(), ys.ravel()] + 0.0
    T = np.array([b - a, c - a]).T
    if abs(np.linalg.det(T)) < 1e-9:
        continue
    l = np.linalg.solve(T, (p - a).T).T
    w = np.c_[1 - l.sum(1), l]
    inside = (w > -0.02).all(1)
    if not inside.any():
        continue
    w, p = w[inside], p[inside].astype(int)
    pts = w @ V[F[fi]]
    col, dd = atlas_colour(pts, jt)
    inside_all = covered[F[fi]].all()
    rgba = np.c_[col, np.where(inside_all | ((dd < COVER_M) & covered[F[fi]].any()), 255, 0)]
    img[SIZE - 1 - p[:, 1], p[:, 0]] = rgba
Image.fromarray(img).save(W + "anny_jersey_texture.png")
print("texture written")
