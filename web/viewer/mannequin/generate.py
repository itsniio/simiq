# /// script
# requires-python = ">=3.12,<3.13"
# dependencies = ["anny>=0.6", "torch>=2.4", "numpy>=2", "scipy", "scikit-image", "trimesh>=4",
#                 "warp-lang", "fast-simplification"]
# ///
"""Faceless studio mannequin (Figma "Widget / Body"): Anny sculpted as a signed distance field.

uv run generate.py [out.glb] [grid step m] [faces]

Anny is posed and fitted to 189 cm / 86 kg, turned into a distance field, blurred smooth, given
muscles as small displacements, its head swapped for a faceless egg on a blended neck, and meshed.
The muscle landmarks are heights in metres on this one body, not a general rig.
"""

import sys

import anny
import fast_simplification
import numpy as np
import torch
import trimesh
import warp as wp
from scipy.ndimage import gaussian_filter, map_coordinates
from skimage.measure import marching_cubes

OUT = sys.argv[1] if len(sys.argv) > 1 else "mannequin.glb"
VOX = float(sys.argv[2]) if len(sys.argv) > 2 else 0.003  # grid step in metres
HEIGHT_M = 1.89
BAND = 0.09  # signed distances are clamped to ±BAND, wider than any blend
FACES = int(sys.argv[3]) if len(sys.argv) > 3 else 160_000
WEIGHT_KG = 86
DENSITY = 1030  # kg/m³
NECK = (0.074, 0.068)  # neck half-width and half-depth, metres

PHENOTYPE = {"gender": 0.0, "age": 0.78, "muscle": 1.0, "height": 1.0,
             "proportions": 1.0}
LOCAL = {
    "torso-vshape-incr": 1.0, "measure-shoulder-dist-incr": 1.0, "torso-muscle-pectoral-incr": 0.7,
    "torso-muscle-dorsi-incr": 0.15, "stomach-tone-incr": 1.0, "measure-waist-circ-incr": -0.4,
    "bulge-incr": -0.2,
    "l-upperarm-shoulder-muscle-incr": 1.0, "r-upperarm-shoulder-muscle-incr": 1.0,
    "l-upperarm-muscle-incr": 1.0, "r-upperarm-muscle-incr": 1.0,
    "l-lowerarm-muscle-incr": 0.6, "r-lowerarm-muscle-incr": 0.6,
    "l-upperleg-muscle-incr": 1.0, "r-upperleg-muscle-incr": 1.0,
    "l-lowerleg-muscle-incr": 0.6, "r-lowerleg-muscle-incr": 0.6,
    "measure-upperarm-length-incr": 0.5, "measure-lowerarm-length-incr": 0.5,
    "measure-neck-height-incr": 0.4, "measure-neck-circ-incr": 0.8,
}
# Pose, degrees about Anny's axes (+X body left, -Y forward, +Z up).
POSE = {"upperarm01.L": (0, 22, 0), "upperarm01.R": (0, -22, 0),
        "lowerarm01.L": (36, 0, 0), "lowerarm01.R": (36, 0, 0),
        "wrist.L": (10, 0, 20), "wrist.R": (10, 0, -20),
        "upperleg01.L": (0, 3, 0), "upperleg01.R": (0, -3, 0)}
# Twists about a bone's own axis (degrees, right-hand rule along the bone): palms to the thighs.
TWIST = {"lowerarm02.L": (-20, "wrist.L"), "lowerarm02.R": (20, "wrist.R")}
for side in "LR":
    for finger in (2, 3, 4, 5):
        for seg in (1, 2, 3):
            curl = (5 + finger) * (1 if side == "L" else -1)
            POSE[f"finger{finger}-{seg}.{side}"] = (0, curl, 0)


def rotation(rx, ry, rz):
    """Rotation Rz·Ry·Rx from angles in degrees about the world axes."""
    x, y, z = np.radians([rx, ry, rz])
    cx, sx, cy, sy, cz, sz = np.cos(x), np.sin(x), np.cos(y), np.sin(y), np.cos(z), np.sin(z)
    return (np.array([[cz, -sz, 0], [sz, cz, 0], [0, 0, 1]])
            @ np.array([[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]])
            @ np.array([[1, 0, 0], [0, cx, -sx], [0, sx, cx]]))


def axis_rotation(axis, degrees):
    """Rotation by an angle about an axis (Rodrigues)."""
    k = np.asarray(axis, float) / np.linalg.norm(axis)
    K = np.array([[0, -k[2], k[1]], [k[2], 0, -k[0]], [-k[1], k[0], 0]])
    a = np.radians(degrees)
    return np.eye(3) + np.sin(a) * K + (1 - np.cos(a)) * K @ K


def posed_body():
    """Anny vertices, faces and bone head positions in metres, at HEIGHT_M and WEIGHT_KG."""
    model = anny.Anny(topology="anny-noeyes-notongue", local_changes=list(LOCAL),
                      extrapolate_phenotypes=True).to(dtype=torch.float32)
    T = torch.eye(4).repeat(1, model.bone_count, 1, 1)
    for bone, angles in POSE.items():
        T[0, model.bone_labels.index(bone), :3, :3] = torch.as_tensor(rotation(*angles))
    with torch.no_grad():
        rest = model(phenotype_kwargs={k: torch.tensor([v]) for k, v in PHENOTYPE.items()},
                     local_changes_kwargs={k: torch.tensor([v]) for k, v in LOCAL.items()})
    heads = rest["rest_bone_heads"][0].double().numpy()
    heads = dict(zip(model.bone_labels, heads, strict=True))
    for bone, (degrees, tip) in TWIST.items():
        i = model.bone_labels.index(bone)
        twist = axis_rotation(heads[tip] - heads[bone], degrees)
        T[0, i, :3, :3] = T[0, i, :3, :3] @ torch.as_tensor(twist, dtype=torch.float32)
    faces = model.faces.numpy()

    def run(weight):
        with torch.no_grad():
            out = model(pose_parameters=T,
                        phenotype_kwargs={k: torch.tensor([v]) for k, v in
                                          {**PHENOTYPE, "weight": weight}.items()},
                        local_changes_kwargs={k: torch.tensor([v]) for k, v in LOCAL.items()})
        v = out["vertices"][0].double().numpy()
        joints = out["bone_poses"][0, :, :3, 3].double().numpy()
        floor, scale = v[:, 2].min(), HEIGHT_M / np.ptp(v[:, 2])
        v, joints = (v - [0, 0, floor]) * scale, (joints - [0, 0, floor]) * scale
        return v, joints, trimesh.Trimesh(v, faces, process=False).volume * DENSITY

    # Secant steps on Anny's weight parameter until the mass matches.
    w0, w1 = 0.4, 0.8
    m0 = run(w0)[2]
    for _ in range(6):
        v, joints, m1 = run(w1)
        if abs(m1 - WEIGHT_KG) < 0.3:
            break
        w0, w1, m0 = w1, w1 + (WEIGHT_KG - m1) * (w1 - w0) / (m1 - m0), m1
    print(f"weight parameter {w1:.3f}: {m1:.1f} kg")
    return v, faces, dict(zip(model.bone_labels, joints, strict=True))


wp.config.quiet = True


@wp.kernel
def sdf_kernel(mesh: wp.uint64, lo: wp.vec3, vox: float, nx: int, ny: int, band: float,
               out: wp.array(dtype=float)):
    t = wp.tid()
    p = lo + wp.vec3(float(t % nx), float((t // nx) % ny), float(t // (nx * ny))) * vox
    q = wp.mesh_query_point_sign_winding_number(mesh, p, 1.0)
    d = band
    if q.result:
        d = wp.min(wp.length(p - wp.mesh_eval_position(mesh, q.face, q.u, q.v)), band) * q.sign
    out[t] = d


def body_sdf(v, f, lo, shape):
    """Signed distance to the Anny mesh on the grid, negative inside, indexed [x, y, z]."""
    mesh = wp.Mesh(points=wp.array(v.astype(np.float32), dtype=wp.vec3),
                   indices=wp.array(f.astype(np.int32).ravel(), dtype=int))
    n = int(np.prod(shape))
    out = wp.zeros(n, dtype=float)
    wp.launch(sdf_kernel, n, [mesh.id, wp.vec3(*lo.astype(np.float32)), VOX, int(shape[0]),
                              int(shape[1]), BAND, out])
    return out.numpy().reshape(shape[2], shape[1], shape[0]).transpose(2, 1, 0)


def smin(a, b, k):
    """Polynomial smooth minimum: a union of two distance fields with a fillet of size k."""
    h = np.clip(0.5 + 0.5 * (b - a) / k, 0, 1)
    return b * (1 - h) + a * h - k * h * (1 - h)


def smax(a, b, k):
    return -smin(-a, -b, k)


def segment_distance(P, a, b):
    """Distance from points P to segment ab, and the position t in [0, 1] along it."""
    ab = b - a
    t = np.clip(((P - a) @ ab) / (ab @ ab), 0, 1)
    return np.linalg.norm(P - a - t[:, None] * ab, axis=1), t


def head_and_neck(P, D, J):
    """Replace Anny's head with a faceless egg on a smooth neck; P are grid points, D their SDF."""
    neck_base, head_base = J["neck01"], J["head"]
    # The egg: a slightly forward-tilted ellipsoid whose lower half narrows to the chin.
    centre = head_base + np.array([0.0, -0.022, 0.07])
    r = np.array([0.082, 0.1, 0.12])
    q = P - centre
    tilt = np.radians(14)  # chin forward
    c, s = np.cos(tilt), np.sin(tilt)
    y = q[:, 1] * c + q[:, 2] * s
    z = -q[:, 1] * s + q[:, 2] * c
    lower = np.clip(-z / r[2], 0, 1)
    taper = 1 - 0.20 * lower ** 1.4
    back = 1 + 0.025 * (1 + np.tanh(2 * y / r[1]))  # fuller crown at the back
    rz = r[2] * (0.88 + 0.12 * (1 - np.tanh(4 * z / r[2])) / 2)  # a rounder crown, a longer chin
    k = np.sqrt((q[:, 0] / (r[0] * taper)) ** 2 + (y / (r[1] * taper * back)) ** 2 + (z / rz) ** 2)
    egg = (k - 1) * r[0] * 0.95
    # The body without its head: a plane under the chin, rising towards the nape.
    # It climbs steeply sideways past the neck, so the trapezius and shoulders keep their shape.
    side = np.abs(P[:, 0] - neck_base[0]) / 0.08
    cut_z = (neck_base[2] + 0.005 + 0.4 * (P[:, 1] - neck_base[1])
             + 4.0 * np.clip(side - 1.12, 0, None) ** 2)
    body = smax(D, P[:, 2] - cut_z, 0.03)
    # The neck: an elliptic cone from inside the chest to the egg's centre, with no flat ends.
    squash = np.array([NECK[1] / NECK[0], 1.0, 1.0])  # makes its cross-section round
    a = (neck_base + [0, -0.016, -0.08]) * squash
    b = (centre + [0, 0.004, -0.01]) * squash
    d, t = segment_distance(P * squash, a, b)
    neck = d - NECK[1] * (1 - 0.22 * t)
    return smin(body, smin(neck, egg, 0.04), 0.07)


class Surface:
    """Points on Anny's skin found by casting rays, to anchor the sculpted features."""

    def __init__(self, v, f):
        self.a, self.e1, self.e2 = v[f[:, 0]], v[f[:, 1]] - v[f[:, 0]], v[f[:, 2]] - v[f[:, 0]]

    def hit(self, inside, direction):
        """The outermost skin point on the ray from `inside` along `direction` (Möller-Trumbore)."""
        d = np.asarray(direction, float) / np.linalg.norm(direction)
        start = np.asarray(inside, float) + d * 0.5
        ray = -d
        p = np.cross(ray, self.e2)
        det = np.einsum("ij,ij->i", self.e1, p)
        ok = np.abs(det) > 1e-12
        inv = np.where(ok, 1 / np.where(ok, det, 1), 0)
        s = start - self.a
        u = np.einsum("ij,ij->i", s, p) * inv
        q = np.cross(s, self.e1)
        w = (q @ ray) * inv
        t = np.einsum("ij,ij->i", self.e2, q) * inv
        good = ok & (u >= 0) & (w >= 0) & (u + w <= 1) & (t > 0)
        if not good.any():
            return np.asarray(inside, float)
        return start + ray * t[good].min()

    def front(self, x, z):
        return self.hit([x, 0.0, z], [0, -1, 0])

    def back(self, x, z):
        return self.hit([x, 0.0, z], [0, 1, 0])


def polyline(points, n=60):
    """A Catmull-Rom curve through the points, sampled densely."""
    p = np.asarray(points, float)
    p = np.vstack([2 * p[0] - p[1], p, 2 * p[-1] - p[-2]])
    out = []
    for i in range(1, len(p) - 2):
        t = np.linspace(0, 1, n, endpoint=False)[:, None]
        a, b, c, d = p[i - 1], p[i], p[i + 1], p[i + 2]
        out.append(0.5 * (2 * b + (c - a) * t + (2 * a - 5 * b + 4 * c - d) * t ** 2
                          + (3 * b - a - 3 * c + d) * t ** 3))
    out.append(p[-2][None])
    return np.vstack(out)


def groove(P, curve, width, depth):
    """Inward displacement along a curve on the skin (a furrow between muscles)."""
    from scipy.spatial import cKDTree
    d, _ = cKDTree(curve).query(P, distance_upper_bound=4 * width)
    d = np.where(np.isinf(d), 1e3, d)
    return -depth * np.exp(-(d / width) ** 2)


def blob(P, centre, axis, radii, height):
    """Outward displacement of a muscle belly: an ellipsoid along `axis` with a soft rim."""
    axis = np.asarray(axis, float) / np.linalg.norm(axis)
    q = P - centre
    along = q @ axis
    across = np.linalg.norm(q - along[:, None] * axis, axis=1)
    r = np.hypot(along / radii[0], across / radii[1])
    return height * np.clip(1 - r ** 2, 0, 1) ** 1.5


def sculpt(P, N, J, S):
    """Displacement (metres, + outward) that draws the athletic muscles on the left half.

    P are points in Anny's frame mirrored to x >= 0, N their outward normals; the body is symmetric.
    """
    h = np.zeros(len(P))
    front = np.clip((-N[:, 1] - 0.15) / 0.45, 0, 1)
    back = np.clip((N[:, 1] - 0.15) / 0.45, 0, 1)
    F, B = S.front, S.back

    # Chest: pectoral mass with a crisp lower border, a sternal furrow, collarbones.
    h += front * blob(P, F(0.075, 1.465), [1, 0, 0.25], (0.085, 0.06), 0.006)
    h += front * groove(P, polyline([F(0.0, 1.405), F(0.06, 1.39), F(0.12, 1.405), F(0.16, 1.45)]),
                        0.010, 0.0045)
    h += front * groove(P, polyline([F(0.0, 1.40), F(0.0, 1.54)]), 0.011, 0.003)
    h += front * groove(P, polyline([F(0.03, 1.535), F(0.10, 1.55), F(0.17, 1.565)]), 0.012, 0.002)
    # Abdomen: rectus blocks between the linea alba and the tendinous lines; obliques; the V lines.
    h += front * groove(P, polyline([F(0.0, 1.385), F(0.0, 1.10)]), 0.009, 0.002)
    for z, bow in ((1.325, 0.012), (1.25, 0.010), (1.175, 0.006)):
        h += front * groove(P, polyline([F(0.0, z), F(0.04, z + bow * 0.5), F(0.08, z + bow)]),
                            0.010, 0.0012)
    for z0, z1 in ((1.33, 1.385), (1.255, 1.325), (1.18, 1.25), (1.03, 1.175)):
        zc = (z0 + z1) / 2
        h += front * blob(P, F(0.04, zc), [0, 0, 1], ((z1 - z0) * 0.62, 0.034), 0.0012)
    h += front * groove(P, polyline([F(0.10, 1.38), F(0.088, 1.25), F(0.078, 1.15)]), 0.012, 0.002)
    h += front * groove(P, polyline([F(0.135, 1.08), F(0.085, 1.0), F(0.035, 0.955)]), 0.012, 0.004)
    h += blob(P, S.hit([0.08, -0.02, 1.13], [1, -0.6, 0]), [0, 0, 1], (0.08, 0.04), 0.004)
    # Serratus fingers under the armpit.
    for z in (1.31, 1.345, 1.38):
        h += blob(P, S.hit([0.08, -0.04, z], [1, -0.9, 0]), [1, 0, 0.6], (0.03, 0.014), 0.0012)
    # Back: spine furrow, shoulder blades, lats.
    h += back * groove(P, polyline([B(0.0, 1.06), B(0.0, 1.25), B(0.0, 1.44)]), 0.014, 0.0035)
    h += back * blob(P, B(0.085, 1.46), [0.3, 0, 1], (0.075, 0.06), 0.003)
    h += back * blob(P, B(0.12, 1.30), [-0.4, 0, 1], (0.11, 0.05), 0.002)
    h += back * blob(P, B(0.05, 1.12), [0, 0, 1], (0.06, 0.025), 0.003)  # erector

    # Arm: deltoid cap with a furrow round its lower edge, biceps, triceps, forearm.
    sh, el, wr = J["upperarm01.L"], J["lowerarm01.L"], J["wrist.L"]
    arm = (el - sh) / np.linalg.norm(el - sh)
    out = np.cross(arm, [0, -1, 0])  # lateral, away from the body
    out /= np.linalg.norm(out)
    fwd = np.cross(out, arm)  # forward
    fwd *= -np.sign(fwd[1])
    def A(t, d):
        return S.hit(sh + t * (el - sh), d)

    delt = A(0.12, out + 0.2 * np.array([0, 0, 1]))
    h += blob(P, delt + 0.012 * out, arm + 0.2 * out, (0.11, 0.065), 0.007)
    h += groove(P, polyline([A(0.05, fwd + out * 0.1 - [0, 0, 0.3]), A(0.25, fwd + out),
                             A(0.45, out), A(0.30, -fwd + out), A(0.05, -fwd)]), 0.010, 0.0035)
    h += blob(P, A(0.55, fwd), arm, (0.13, 0.04), 0.0055)  # biceps
    h += blob(P, A(0.5, -fwd + 0.3 * out), arm, (0.16, 0.045), 0.005)  # triceps
    h += groove(P, polyline([A(0.38, out + 0.1 * fwd), A(0.85, out + 0.2 * fwd)]), 0.009, 0.0025)
    fa = (wr - el) / np.linalg.norm(wr - el)
    def Fa(t, d):
        return S.hit(el + t * (wr - el), d)

    h += blob(P, Fa(0.22, out + fwd), fa, (0.11, 0.035), 0.0045)  # brachioradialis
    h += blob(P, Fa(0.25, -out + fwd * 0.5), fa, (0.10, 0.03), 0.003)  # flexors

    # Leg: quadriceps heads with the vastus medialis teardrop, knee, calf heads.
    hip, kn, an = J["upperleg02.L"], J["lowerleg01.L"], J["foot.L"]
    th = (kn - hip) / np.linalg.norm(kn - hip)
    def L(t, d):
        return S.hit(hip + t * (kn - hip), d)

    h += blob(P, L(0.5, [0.25, -1, 0]), th, (0.26, 0.055), 0.006)  # rectus femoris
    h += blob(P, L(0.55, [1, -0.5, 0]), th, (0.26, 0.06), 0.007)  # vastus lateralis
    h += blob(P, L(0.83, [-0.8, -1, 0]), th + [0.3, 0, 0], (0.09, 0.05), 0.006)  # vastus medialis
    h += groove(P, polyline([L(0.08, [0.9, -1, 0]), L(0.4, [0, -1, 0]), L(0.75, [-0.9, -0.6, 0]),
                             L(0.95, [-1, -0.2, 0])]), 0.016, 0.0018)  # sartorius
    h += groove(P, polyline([L(0.3, [0.8, -0.8, 0]), L(0.8, [0.6, -1, 0])]), 0.014, 0.0015)
    h += groove(P, polyline([L(0.15, [1, 0.2, 0]), L(0.85, [1, 0.3, 0])]), 0.016, 0.0012)  # IT band
    h += blob(P, L(1.0, [0, -1, 0]) + [0, 0, 0.02], [0, 0, 1], (0.035, 0.03), 0.0012)  # patella
    h += groove(P, polyline([L(0.93, [0.8, -1, 0]), L(1.0, [0, -1, 0]) + [0, 0, 0.055],
                             L(0.93, [-0.8, -1, 0])]), 0.012, 0.0012)
    sh_ = (an - kn) / np.linalg.norm(an - kn)
    def C(t, d):
        return S.hit(kn + t * (an - kn), d)

    h += blob(P, C(0.28, [-0.6, 1, 0]), sh_, (0.13, 0.04), 0.008)  # medial gastrocnemius
    h += blob(P, C(0.24, [0.6, 1, 0]), sh_, (0.11, 0.035), 0.0065)  # lateral gastrocnemius
    h += groove(P, polyline([C(0.1, [0, 1, 0]), C(0.42, [0, 1, 0])]), 0.008, 0.0025)
    h += blob(P, C(0.35, [0.7, -1, 0]), sh_, (0.18, 0.025), 0.003)  # tibialis anterior
    return h


def main():
    v, f, J = posed_body()
    lo = v.min(0) - 0.02
    hi = v.max(0) + [0.02, 0.02, 0.10]
    shape = np.ceil((hi - lo) / VOX).astype(int) + 1
    print("grid", shape, f"{np.prod(shape) / 1e6:.1f}M")
    D = body_sdf(v, f, lo, shape)
    # Blur away the base mesh's facets; hands and feet get less, or fingers and toes fuse.
    fine = np.zeros(shape, bool)
    xs, ys, zs = (lo[i] + np.arange(shape[i]) * VOX for i in range(3))
    for bone in ("wrist.L", "wrist.R", "foot.L", "foot.R"):
        c = J[bone] + ([0, 0, -0.07] if bone.startswith("wrist") else [0, -0.06, -0.04])
        near = ((xs[:, None, None] - c[0]) ** 2 + (ys[None, :, None] - c[1]) ** 2
                + (zs[None, None, :] - c[2]) ** 2) < 0.13 ** 2
        fine |= near
    D = np.where(gaussian_filter(fine.astype(np.float32), 0.02 / VOX) > 0.5,
                 gaussian_filter(D, 0.0022 / VOX), gaussian_filter(D, 0.005 / VOX))
    # Muscles: displace the skin along its normal, on the left half mirrored to the right.
    S = Surface(v, f)
    G = np.stack(np.gradient(D), -1)
    idx = np.nonzero(np.abs(D) < 0.02)
    P = lo + np.stack(idx, 1) * VOX
    N = G[idx]
    N /= np.linalg.norm(N, axis=1, keepdims=True) + 1e-12
    side = np.where(P[:, 0] < 0, -1.0, 1.0)
    head = (P[:, 2] > J["neck01"][2] - 0.02) & (np.hypot(P[:, 0], P[:, 1]) < 0.11)
    keep = ~head
    h = np.zeros(len(P))
    h[keep] = sculpt(P[keep] * np.c_[side[keep], np.ones((keep.sum(), 2))],
                     N[keep] * np.c_[side[keep], np.ones((keep.sum(), 2))], J, S)
    D[idx] -= h
    del G
    # The head: everything above the shoulders' base is re-evaluated with the egg and neck.
    k0 = int((J["neck01"][2] - 0.25 - lo[2]) / VOX)  # below the reach of the neck blend
    Ix, Iy, Iz = np.meshgrid(np.arange(shape[0]), np.arange(shape[1]), np.arange(k0, shape[2]),
                           indexing="ij")
    Pt = lo + np.stack([Ix.ravel(), Iy.ravel(), Iz.ravel()], 1) * VOX
    D[:, :, k0:] = head_and_neck(Pt, D[:, :, k0:].ravel(), J).reshape(Ix.shape)
    # Soften the creases where the trapezius meets the neck: blend in a blurred field around it.
    n = J["neck01"]
    xs, ys, zs = (lo[i] + np.arange(shape[i]) * VOX for i in range(3))
    radial = np.hypot(xs[:, None, None] - n[0], ys[None, :, None] - n[1] + 0.01)
    ring = (np.exp(-((radial - 0.1) / 0.04) ** 2)
            * np.exp(-((zs[None, None, :] - n[2] - 0.02) / 0.06) ** 2))
    D = D + ring * (gaussian_filter(D, 0.008 / VOX) - D)

    verts, faces, _, _ = marching_cubes(D, 0.0, spacing=(VOX,) * 3)
    verts += lo
    mesh = trimesh.Trimesh(verts, faces[:, ::-1], process=True)
    mesh = max(mesh.split(only_watertight=False), key=lambda m: len(m.faces))
    if mesh.volume < 0:
        mesh.invert()
    print("marching cubes", len(mesh.faces), "faces")
    if len(mesh.faces) > FACES:  # a gentle collapse order: an aggressive one leaves pits
        vs, fs = fast_simplification.simplify(mesh.vertices, mesh.faces, target_count=FACES, agg=2)
        mesh = trimesh.Trimesh(vs, fs, process=True)
    # Normals from the field's gradient: smoother than the triangles' own.
    G = np.stack(np.gradient(gaussian_filter(D, 1.0)), -1)
    ijk = ((mesh.vertices - lo) / VOX).T
    n = np.stack([map_coordinates(G[..., i], ijk, order=1) for i in range(3)], 1)
    n /= np.linalg.norm(n, axis=1, keepdims=True)
    # Anny is z-up facing -y; glTF is y-up facing +z.
    R = np.array([[1, 0, 0], [0, 0, 1], [0, -1, 0]], float)
    out = trimesh.Trimesh(mesh.vertices @ R.T, mesh.faces, vertex_normals=n @ R.T, process=False)
    out.vertices -= [out.vertices[:, 0].mean(), out.vertices[:, 1].min(), out.vertices[:, 2].mean()]
    out.vertices *= HEIGHT_M / out.vertices[:, 1].max()  # the egg is taller than Anny's head
    out.export(OUT)
    print(OUT, len(out.faces), "faces, height", round(out.vertices[:, 1].max(), 3))


if __name__ == "__main__":
    main()
