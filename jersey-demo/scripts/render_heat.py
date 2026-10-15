"""Per-vertex heatmap render of Anny: zone strain colours over the jersey coverage."""
import json, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont

D = "/tmp/claude-0/jersey/fit/"
variant = sys.argv[1]; out = sys.argv[2]
fit = json.load(open(D + "fit.json")); zones = np.load(D + "zones.npz")
F = np.load(D + "faces.npy"); covered = np.load("/tmp/claude-0/jersey/work/covered.npy")
SKIN = np.array([0.82, 0.82, 0.82]); JERSEY = np.array([0.62, 0.70, 0.66])
LIM = 0.30


def strain_colour(s):
    t = float(np.clip(s / LIM, -1, 1))
    blue, white, red = np.array([0.15, 0.35, 0.85]), np.array([0.97, 0.97, 0.97]), np.array([0.85, 0.15, 0.12])
    return white + (red - white) * t if t > 0 else white + (blue - white) * (-t)


def colours(pose):
    c = np.tile(SKIN, (len(covered), 1)); c[covered] = JERSEY
    for r in fit["results"][f"{variant}/{pose}"]:
        c[zones[r["zone"]]] = strain_colour(r["strain"])
    return c


def raster(V, C, yaw, H=700):
    r = np.radians(yaw)
    R = np.array([[np.cos(r), np.sin(r), 0], [-np.sin(r), np.cos(r), 0], [0, 0, 1]])
    P = (V - V.mean(0)) @ R.T
    scale = H * 0.9 / 1.9; Wd = int(H * 0.62)
    sx = P[:, 0] * scale + Wd / 2; sy = H / 2 - P[:, 2] * scale; depth = P[:, 1]
    img = np.ones((H, Wd, 3)); zb = np.full((H, Wd), np.inf)
    n = np.cross(P[F[:, 1]] - P[F[:, 0]], P[F[:, 2]] - P[F[:, 0]]); n /= np.linalg.norm(n, axis=1, keepdims=True) + 1e-12
    L = np.array([0.3, -1, 0.5]); light = np.abs(n @ L) / np.linalg.norm(L) * 0.55 + 0.45
    for fi, idx in enumerate(F):
        a = np.c_[sx[idx], sy[idx]]
        lo = np.maximum(np.floor(a.min(0)).astype(int), 0); hi = np.minimum(np.ceil(a.max(0)).astype(int), [Wd - 1, H - 1])
        if (hi < lo).any(): continue
        xs, ys = np.meshgrid(np.arange(lo[0], hi[0] + 1), np.arange(lo[1], hi[1] + 1))
        p = np.c_[xs.ravel(), ys.ravel()] + 0.5
        T = np.array([a[1] - a[0], a[2] - a[0]]).T
        if abs(np.linalg.det(T)) < 1e-9: continue
        w = np.linalg.solve(T, (p - a[0]).T).T; w = np.c_[1 - w.sum(1), w]
        m = (w >= -1e-6).all(1)
        if not m.any(): continue
        w = w[m]; px = p[m].astype(int); z = w @ depth[idx]
        k = z < zb[px[:, 1], px[:, 0]]
        if not k.any(): continue
        w, px, z = w[k], px[k], z[k]
        zb[px[:, 1], px[:, 0]] = z; img[px[:, 1], px[:, 0]] = (w @ C[idx]) * light[fi]
    return img


panels = []
for pose, yaws in (("standing", (0, 180)), ("hoods", (0, 90, 180))):
    V = np.load(D + f"anny_{pose}.npy").astype(float); C = colours(pose)
    panels += [raster(V, C, y) for y in yaws]
img = Image.fromarray((np.concatenate(panels, 1) * 255).astype(np.uint8))
W, H = img.size
canvas = Image.new("RGB", (W, H + 230), "white"); canvas.paste(img, (0, 60))
d = ImageDraw.Draw(canvas)
try:
    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 22)
    small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 17)
except OSError:
    font = small = ImageFont.load_default()
title = {"pattern": "Strih (DXF), velkost M - natiahnutie latky po zonach",
         "effective": "Efektivny rozmer podla simulacie CLO (zrazanie utku 72 %), velkost M"}[variant]
d.text((20, 15), title + "  |  muz 178 cm / 75 kg  |  stoj (2x)  +  hoods (3x)", fill="black", font=font)
y0 = H + 75
for i in range(301):  # legend bar
    s = -LIM + 2 * LIM * i / 300
    d.line([(20 + i * 2, y0), (20 + i * 2, y0 + 22)], fill=tuple(int(255 * v) for v in strain_colour(s)))
d.text((20, y0 + 28), "-30 % volne", fill="black", font=small); d.text((290, y0 + 28), "0", fill="black", font=small)
d.text((520, y0 + 28), "+30 % tesne", fill="black", font=small)
names = {"chest": "hrudnik", "waist": "pas", "hem": "lem / boky", "sleeve_opening": "rukav", "back_length": "dlzka chrbta"}
x = 700
for pose in ("standing", "hoods"):
    d.text((x, y0 - 10), pose, fill="black", font=font)
    for j, r in enumerate(fit["results"][f"{variant}/{pose}"]):
        d.text((x, y0 + 20 + j * 22), f"{names[r['zone']]}: telo {r['body_cm']} / dres {r['garment_cm']} cm  ->  {r['strain']*100:+.0f} %", fill="black", font=small)
    x += 560
canvas.save(out)
