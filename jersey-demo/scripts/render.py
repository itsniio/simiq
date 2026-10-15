"""Software render of Anny wearing the baked jersey texture: front, side, back."""
import sys, numpy as np
from PIL import Image
W = "/tmp/claude-0/jersey/work/"
V = np.load(sys.argv[1]).astype(float); V[:, 2] -= V[:, 2].min()
F = np.load(W + "anny_f.npy"); UV = np.load(W + "anny_uv.npy"); FUV = np.load(W + "anny_fuv.npy")
tex = np.asarray(Image.open(sys.argv[2])).astype(float) / 255
out = sys.argv[3]
SKIN = np.array([0.80, 0.66, 0.58])
H = 900
views = []
for yaw in (0, 90, 180):
    r = np.radians(yaw)
    R = np.array([[np.cos(r), np.sin(r), 0], [-np.sin(r), np.cos(r), 0], [0, 0, 1]])
    P = V @ R.T  # camera looks along +y from -y (front of body faces -y)
    scale = H * 0.9 / 1.9
    sx = (P[:, 0] + 0.5) * scale; sy = H - (P[:, 2] + 0.05) * scale; depth = P[:, 1]
    Wd = int(1.0 * scale)
    img = np.ones((H, Wd, 3)); zb = np.full((H, Wd), np.inf)
    n = np.cross(P[F[:, 1]] - P[F[:, 0]], P[F[:, 2]] - P[F[:, 0]])
    n /= np.linalg.norm(n, axis=1, keepdims=True) + 1e-12
    L = np.array([0.3, -1, 0.5]); light = np.abs(n @ L) / np.linalg.norm(L) * 0.65 + 0.35
    th, tw = tex.shape[:2]
    for fi in range(len(F)):
        if n[fi, 1] > 0.05 and False:
            continue
        idx = F[fi]
        a = np.c_[sx[idx], sy[idx]]
        lo = np.floor(a.min(0)).astype(int); hi = np.ceil(a.max(0)).astype(int)
        lo = np.maximum(lo, 0); hi = np.minimum(hi, [Wd - 1, H - 1])
        if (hi < lo).any():
            continue
        xs, ys = np.meshgrid(np.arange(lo[0], hi[0] + 1), np.arange(lo[1], hi[1] + 1))
        p = np.c_[xs.ravel(), ys.ravel()] + 0.5
        T = np.array([a[1] - a[0], a[2] - a[0]]).T
        det = np.linalg.det(T)
        if abs(det) < 1e-9:
            continue
        l = np.linalg.solve(T, (p - a[0]).T).T
        w = np.c_[1 - l.sum(1), l]
        m = (w >= -1e-6).all(1)
        if not m.any():
            continue
        w = w[m]; px = p[m].astype(int)
        z = w @ depth[idx]
        closer = z < zb[px[:, 1], px[:, 0]]
        if not closer.any():
            continue
        w, px, z = w[closer], px[closer], z[closer]
        uv = w @ UV[FUV[fi]]
        tx = np.clip((uv[:, 0] * (tw - 1)).astype(int), 0, tw - 1)
        ty = np.clip(((1 - uv[:, 1]) * (th - 1)).astype(int), 0, th - 1)
        c = tex[ty, tx]
        col = c[:, :3] * c[:, 3:4] + SKIN * (1 - c[:, 3:4])
        zb[px[:, 1], px[:, 0]] = z
        img[px[:, 1], px[:, 0]] = col * light[fi]
    views.append(img)
Image.fromarray((np.concatenate(views, 1) * 255).astype(np.uint8)).save(out)
