"""Drape a garment on a body with XPBD on Warp (cloth-sim D2).

Per substep: predict from velocity and forces, then a few iterations of anisotropic stretch from
the fabric curves (course, wale, shear), bending, and body collision, then velocities with
friction. Constraints are solved colour by colour, so no two of one launch move the same vertex
and a run is deterministic. Internally SI units (m, kg, s); positions in and out are mm.
"""

from dataclasses import dataclass

import numpy as np
import warp as wp

from simiq_fit.garment import Fabric

GRAVITY_M_S2 = 9.81
SUBSTEPS_PER_S = 500
ITERATIONS = 2
DAMPING_PER_S = 2.0  # velocity decays by e^(−2·t)
SHEAR_N_PER_M = 20.0  # membrane shear modulus, N/m per rad; not measured, a spike guess
COMPRESSION_SCALE = 1.0  # compression resists at the first slope; 0.1 left sleeve and back short
BENDING_N_M = 1e-5  # bending rigidity; a spike guess, tuned on 178/75 (1e-6 before)
COLLISION_MM = 4.6  # the garment keeps this far off the body: CLO's start drape, p1 4.58 mm
FRICTION = 1.0  # fabric on skin, per-vertex default: at 0.3 the jersey rode up 87 mm in hoods
CARRY_MM = 10.0  # cloth this close to the body moves with it before each substep is solved
QUERY_MM = 15.0  # how far from the body a vertex is looked up: well past any collision distance

wp.config.quiet = True


def kes_shear_n_per_m(g_cn_per_cm_deg):
    """KES-FB1 shear rigidity G, cN/cm per degree, as the membrane shear modulus in N/m per rad."""
    return g_cn_per_cm_deg * 0.01 / 0.01 * 180 / np.pi


@dataclass
class Cloth:
    faces: wp.array  # (m,) vec3i
    dm_inv: wp.array  # (m,) mat22, inverse of each triangle's rest edges in m
    area: wp.array  # (m,) rest area, m²
    stiffness_scale: wp.array  # (m,) multiplier of the fabric's stretch and shear stiffness
    shear: float  # membrane shear modulus, N/m per radian
    colours: list  # wp.arrays of triangle indices, one launch each (see `launches`)
    hinges: wp.array  # (h,) vec4i: the edge's two vertices, then the two opposite ones
    hinge_k: wp.array  # (h,) vec4: bending weights K of the four vertices, 1/m
    hinge_stiffness: wp.array  # (h,) J per rad²
    hinge_colours: list
    x: wp.array  # (n,) vec3 positions, m
    v: wp.array  # (n,) vec3 velocities, m/s
    previous: wp.array  # (n,) vec3 positions at the start of the substep
    inv_mass: wp.array  # (n,) 1/kg (scaled inertia), 0 for pinned vertices
    friction: wp.array  # (n,) static Coulomb coefficient of each vertex against what it touches
    friction_kinetic: wp.array  # (n,) the coefficient once the vertex slides
    slip: float  # regularized friction μN·min(1, v/slip), m/s; 0 is plain Coulomb
    adhesion: float  # friction τ·A as an acceleration, τ / (areal density · inertia), m/s²
    force: wp.array  # (n,) vec3 force on each vertex: its weight plus any load, N
    lam: wp.array  # (m,) vec3 λ of each triangle's course, wale and shear constraint
    hinge_lam: wp.array  # (h,) λ of each hinge
    contact_push: wp.array  # (n,) vec3 how far collision pushed the vertex this substep, m
    near_face: wp.array  # (n,) body face last found nearest, −1 before the first lookup
    near_uv: wp.array  # (n,) vec2 barycentric point on it
    near_distance: wp.array  # (n,) signed distance from it, m
    layer_mesh: wp.Mesh | None  # the under layer's faces over x, when a layer lies on another
    layer_ids: wp.array | None  # vertices of the upper layer
    layer_side: wp.array | None  # which side of the under layer each starts on, ±1
    layer_distance: float  # how far the upper layer keeps off the under one, m
    course: tuple  # (strain, tension N/m) arrays of the fabric curve
    wale: tuple


@dataclass
class Body:
    mesh: wp.Mesh  # points: the body now
    previous: wp.array  # (k,) vec3 body points at the start of the substep
    start: wp.array  # (k,) vec3 body at the start of the current move
    end: wp.array  # (k,) vec3 body at its end
    moving: bool = False


def colour(stencils: np.ndarray) -> list[np.ndarray]:
    """Greedy colouring: each stencil takes the first colour none of its vertices has yet."""
    used = [set() for _ in range(stencils.max() + 1)]
    colours = np.empty(len(stencils), int)
    for t, stencil in enumerate(stencils):
        taken = set().union(*(used[i] for i in stencil))
        c = next(c for c in range(len(taken) + 1) if c not in taken)
        colours[t] = c
        for i in stencil:
            used[i].add(c)
    return [
        wp.array(np.where(colours == c)[0].astype(np.int32), dtype=int)
        for c in range(colours.max() + 1)
    ]


def launches(colours: list) -> list:
    """The launches that solve these colours: one per colour, or one in all on the CPU.

    A CPU launch runs its threads one after another, so one launch over the colours' indices
    in order does exactly what one launch per colour does, without the launch overhead.
    """
    if not colours or not wp.get_device().is_cpu:
        return colours
    return [wp.array(np.concatenate([c.numpy() for c in colours]), dtype=int)]


def curve_arrays(fabric: Fabric, direction: str):
    curve = fabric.curves[direction]
    tension = np.array(curve.force_n, float) / (fabric.specimen_width_mm / 1000)
    return wp.array(np.array(curve.strain, float), dtype=float), wp.array(tension, dtype=float)


def hinge_frame(rest, a, b, opposite):
    """Along-edge fraction and height of the opposite vertex over edge a→b, in one rest triangle."""
    edge, to = rest[b] - rest[a], rest[opposite] - rest[a]
    length = np.linalg.norm(edge)
    return to @ edge / length**2, abs(edge[0] * to[1] - edge[1] * to[0]) / length, length


def hinges(faces: np.ndarray, rest: np.ndarray, area: np.ndarray):
    """Interior edges with the bending weights of a flat rest state (see formulas.md)."""
    sides = {}
    for t, face in enumerate(faces):
        for k in range(3):
            a, b = face[k], face[(k + 1) % 3]
            sides.setdefault((min(a, b), max(a, b)), []).append((t, k))
    stencils, weights, stiffness = [], [], []
    for (a, b), shared in sides.items():
        if len(shared) != 2:
            continue
        frames = []
        for t, k in shared:
            corner = {faces[t][j]: rest[t][j] for j in range(3)}
            frames.append((faces[t][(k + 2) % 3], hinge_frame(corner, a, b, faces[t][(k + 2) % 3])))
        (c, (s2, h2, e2)), (d, (s3, h3, e3)) = frames
        k2, k3 = 1 / h2, 1 / h3
        k1 = -(k2 * s2 + k3 * s3)
        stencils.append((a, b, c, d))
        weights.append((-(k2 + k3) - k1, k1, k2, k3))
        edge = (e2 + e3) / 2
        stiffness.append(BENDING_N_M * 6 * edge**2 / (area[shared[0][0]] + area[shared[1][0]]))
    return (
        np.array(stencils, np.int32).reshape(-1, 4),
        np.array(weights).reshape(-1, 4),
        np.array(stiffness),
    )


def cloth(
    rest_mm,
    faces,
    positions_mm,
    fabric: Fabric,
    pinned=(),
    force_n=None,
    stiffness_scale=None,
    layer=None,
    inertia_scale=1.0,
    friction=None,
    shear_n_per_m=SHEAR_N_PER_M,
    friction_kinetic=None,
    slip_mm_s=0.0,
    adhesion_pa=0.0,
) -> Cloth:
    """A cloth ready to simulate: rest triangles (course, wale) mm, faces, positions mm.

    force_n: (n, 3) external force per vertex in N, e.g. a load hung on an edge.
    stiffness_scale: (m,) multiplier of each triangle's stretch and shear stiffness (a zipper tape).
    layer: (upper vertex ids, under-layer faces, distance mm): the one place cloth meets cloth,
    the upper layer kept on the side of the under one it starts on.
    inertia_scale: inertia × this, weight unchanged: the settled state is the same, a heavy load
    on light cloth converges, but the cloth falls that much slower (only for load tests).
    friction: (n,) Coulomb coefficient per vertex, default FRICTION (a silicone gripper more).
    shear_n_per_m: the fabric's membrane shear modulus (τ = G γ), default SHEAR_N_PER_M.
    friction_kinetic: (n,) the coefficient while a vertex slides, default the static one.
    slip_mm_s: above 0, friction μN·min(1, v/slip): below that slip speed a held vertex creeps.
    adhesion_pa: friction μN + τA: a shear strength τ of the contact, whatever the pressure.
    """
    faces = np.asarray(faces)
    rest = np.asarray(rest_mm, float) / 1000
    dm = np.stack([rest[:, 1] - rest[:, 0], rest[:, 2] - rest[:, 0]], axis=2)
    area = np.abs(np.linalg.det(dm)) / 2
    mass = np.zeros(len(positions_mm))
    for k in range(3):
        np.add.at(mass, faces[:, k], area * fabric.weight_g_m2 / 1000 / 3)
    inv_mass = np.where(mass > 0, 1 / np.maximum(mass * inertia_scale, 1e-30), 0.0)
    inv_mass[np.asarray(pinned, int)] = 0.0
    x = np.asarray(positions_mm, float) / 1000
    force = np.zeros_like(x) if force_n is None else np.array(force_n, float)
    force[:, 1] -= mass * GRAVITY_M_S2
    stencils, weights, stiffness = hinges(faces, rest, area)
    static = np.full(len(x), FRICTION) if friction is None else friction
    n = len(x)
    c = Cloth(
        faces=wp.array(faces.astype(np.int32), dtype=wp.vec3i),
        dm_inv=wp.array(np.linalg.inv(dm), dtype=wp.mat22),
        area=wp.array(area, dtype=float),
        stiffness_scale=wp.array(
            np.ones(len(faces)) if stiffness_scale is None else stiffness_scale, dtype=float
        ),
        shear=shear_n_per_m,
        colours=launches(colour(faces)),
        hinges=wp.array(stencils, dtype=wp.vec4i),
        hinge_k=wp.array(weights, dtype=wp.vec4),
        hinge_stiffness=wp.array(stiffness, dtype=float),
        hinge_colours=launches(colour(stencils)) if len(stencils) else [],
        x=wp.array(x, dtype=wp.vec3),
        v=wp.zeros(n, dtype=wp.vec3),
        previous=wp.array(x, dtype=wp.vec3),
        inv_mass=wp.array(inv_mass, dtype=float),
        friction=wp.array(static, dtype=float),
        slip=slip_mm_s / 1000.0,
        adhesion=adhesion_pa / (fabric.weight_g_m2 / 1000 * inertia_scale),
        friction_kinetic=wp.array(
            static if friction_kinetic is None else friction_kinetic, dtype=float
        ),
        force=wp.array(force, dtype=wp.vec3),
        lam=wp.zeros(len(faces), dtype=wp.vec3),
        hinge_lam=wp.zeros(len(stencils), dtype=float),
        contact_push=wp.zeros(n, dtype=wp.vec3),
        near_face=wp.full(n, -1, dtype=int),
        near_uv=wp.zeros(n, dtype=wp.vec2),
        near_distance=wp.zeros(n, dtype=float),
        layer_mesh=None,
        layer_ids=None,
        layer_side=None,
        layer_distance=0.0,
        course=curve_arrays(fabric, "course"),
        wale=curve_arrays(fabric, "wale"),
    )
    if layer is not None:
        upper, under, distance_mm = layer
        upper = np.setdiff1d(upper, np.asarray(under).ravel())  # sewn vertices belong to both
        c.layer_mesh = wp.Mesh(
            points=c.x, indices=wp.array(np.asarray(under, np.int32).ravel(), dtype=int)
        )
        c.layer_ids = wp.array(upper.astype(np.int32), dtype=int)
        c.layer_side = wp.zeros(len(upper), dtype=float)
        c.layer_distance = distance_mm / 1000
        wp.launch(layer_sides, len(upper), [c.layer_mesh.id, c.layer_ids, c.x, c.layer_side])
    return c


def body(positions_mm, faces) -> Body:
    """A body surface (closed, normals outward) the cloth collides with."""
    points = wp.array(np.asarray(positions_mm, float) / 1000, dtype=wp.vec3)
    indices = wp.array(np.asarray(faces, np.int32).ravel(), dtype=int)
    return Body(
        mesh=wp.Mesh(points=points, indices=indices, support_winding_number=True),
        previous=wp.clone(points),
        start=wp.clone(points),
        end=wp.clone(points),
    )


def move_body(b: Body, positions_mm) -> None:
    """The next run moves the body from where it is now to these positions."""
    wp.copy(b.start, b.mesh.points)
    end = np.asarray(positions_mm, float) / 1000
    b.moving = not np.array_equal(end, b.end.numpy())
    b.end.assign(end)


def positions_mm(c: Cloth) -> np.ndarray:
    return c.x.numpy().astype(float) * 1000


@wp.func
def stiffness(strain: wp.array(dtype=float), tension: wp.array(dtype=float), e: float):
    """(slope N/m, zero-tension strain) of the curve's linear piece at strain e."""
    if e < 0.0:
        return wp.vec2((tension[1] - tension[0]) / (strain[1] - strain[0]) * COMPRESSION_SCALE, 0.0)
    i = int(0)  # noqa: UP018 (Warp needs the explicit type for a variable changed in a loop)
    while i < strain.shape[0] - 2 and e > strain[i + 1]:
        i += 1
    slope = (tension[i + 1] - tension[i]) / (strain[i + 1] - strain[i])
    return wp.vec2(slope, strain[i] - tension[i] / slope)


@wp.func
def project(
    x: wp.array(dtype=wp.vec3),
    w: wp.array(dtype=float),
    i0: int,
    i1: int,
    i2: int,
    g1: wp.vec3,
    g2: wp.vec3,
    c: float,
    k: float,
    lam: float,
    dt: float,
):
    """Move three vertices along the constraint gradient by one XPBD update; returns the new λ."""
    g0 = -g1 - g2
    compliance = 1.0 / (k * dt * dt)
    denom = w[i0] * wp.dot(g0, g0) + w[i1] * wp.dot(g1, g1) + w[i2] * wp.dot(g2, g2) + compliance
    dl = (-c - compliance * lam) / denom
    x[i0] = x[i0] + w[i0] * dl * g0
    x[i1] = x[i1] + w[i1] * dl * g1
    x[i2] = x[i2] + w[i2] * dl * g2
    return lam + dl


@wp.func
def stretch(
    x: wp.array(dtype=wp.vec3),
    w: wp.array(dtype=float),
    i0: int,
    i1: int,
    i2: int,
    a1: float,
    a2: float,
    area: float,
    strain: wp.array(dtype=float),
    tension: wp.array(dtype=float),
    lam: float,
    dt: float,
):
    """Stretch along one pattern axis: C = |F·axis| − e0, stiffness area × the curve's slope."""
    f = a1 * (x[i1] - x[i0]) + a2 * (x[i2] - x[i0])
    length = wp.length(f)
    if length > 1.0e-12:
        piece = stiffness(strain, tension, length - 1.0)
        if piece[0] > 0.0:
            n = f / length
            c = length - 1.0 - piece[1]
            return project(x, w, i0, i1, i2, a1 * n, a2 * n, c, area * piece[0], lam, dt)
    return lam


@wp.kernel
def solve_triangles(
    ids: wp.array(dtype=int),
    faces: wp.array(dtype=wp.vec3i),
    dm_inv: wp.array(dtype=wp.mat22),
    areas: wp.array(dtype=float),
    scales: wp.array(dtype=float),
    x: wp.array(dtype=wp.vec3),
    w: wp.array(dtype=float),
    course_strain: wp.array(dtype=float),
    course_tension: wp.array(dtype=float),
    wale_strain: wp.array(dtype=float),
    wale_tension: wp.array(dtype=float),
    lams: wp.array(dtype=wp.vec3),
    shear: float,
    dt: float,
):
    t = ids[wp.tid()]
    f = faces[t]
    d = dm_inv[t]
    area = areas[t] * scales[t]  # stiffness is area × slope: scaling the area scales it
    lam = lams[t]
    # F = Ds · Dm⁻¹: F·u = d[0,0]·(x1 − x0) + d[1,0]·(x2 − x0), F·v likewise with column 1.
    lc = stretch(
        x, w, f[0], f[1], f[2], d[0, 0], d[1, 0], area, course_strain, course_tension, lam[0], dt
    )
    lw = stretch(
        x, w, f[0], f[1], f[2], d[0, 1], d[1, 1], area, wale_strain, wale_tension, lam[1], dt
    )
    e1 = x[f[1]] - x[f[0]]
    e2 = x[f[2]] - x[f[0]]
    fu = d[0, 0] * e1 + d[1, 0] * e2
    fv = d[0, 1] * e1 + d[1, 1] * e2
    # Shear: C = F·u · F·v, zero while the course and wale lines stay square.
    g1 = d[0, 0] * fv + d[0, 1] * fu
    g2 = d[1, 0] * fv + d[1, 1] * fu
    ls = project(x, w, f[0], f[1], f[2], g1, g2, wp.dot(fu, fv), area * shear, lam[2], dt)
    lams[t] = wp.vec3(lc, lw, ls)


@wp.kernel
def solve_hinges(
    ids: wp.array(dtype=int),
    hinges: wp.array(dtype=wp.vec4i),
    weights: wp.array(dtype=wp.vec4),
    stiffness: wp.array(dtype=float),
    x: wp.array(dtype=wp.vec3),
    w: wp.array(dtype=float),
    lams: wp.array(dtype=float),
    dt: float,
):
    """Bending: C = |Σ Kᵢ xᵢ|, the fold angle of a flat-at-rest hinge, gradient Kᵢ · direction."""
    h = ids[wp.tid()]
    i = hinges[h]
    k = weights[h]
    s = k[0] * x[i[0]] + k[1] * x[i[1]] + k[2] * x[i[2]] + k[3] * x[i[3]]
    c = wp.length(s)
    if c < 1.0e-9:
        return
    n = s / c
    denom = float(0.0)  # noqa: UP018 (as above)
    for j in range(4):
        denom += w[i[j]] * k[j] * k[j]
    compliance = 1.0 / (stiffness[h] * dt * dt)
    dl = (-c - compliance * lams[h]) / (denom + compliance)
    for j in range(4):
        x[i[j]] = x[i[j]] + w[i[j]] * dl * k[j] * n
    lams[h] = lams[h] + dl


LAYER_QUERY_MM = 20.0  # how far from the under layer an upper-layer vertex is looked up
REFRESH_EVERY = 4  # each substep one vertex in 4 looks its nearest body face up afresh


@wp.kernel
def collide(
    mesh: wp.uint64,
    x: wp.array(dtype=wp.vec3),
    w: wp.array(dtype=float),
    near_face: wp.array(dtype=int),
    near_uv: wp.array(dtype=wp.vec2),
    near_distance: wp.array(dtype=float),
    contact_push: wp.array(dtype=wp.vec3),
    previous: wp.array(dtype=wp.vec3),
    friction: wp.array(dtype=float),
    friction_kinetic: wp.array(dtype=float),
    slip: float,
    adhesion: float,
    dt: float,
    step: int,
):
    """Push a vertex closer than COLLISION_MM to the body (or inside it) out to that distance.

    The body face found nearest last time is tried first: if the vertex projects inside it, that
    is the closest point; otherwise, and for one vertex in REFRESH_EVERY, the BVH is asked.
    """
    i = wp.tid()
    if w[i] == 0.0:
        return
    body = wp.mesh_get(mesh)
    face = near_face[i]
    found = False
    p = wp.vec3()
    n = wp.vec3()
    signed = float(0.0)  # noqa: UP018 (Warp needs the explicit type for a variable set in a branch)
    u = float(0.0)  # noqa: UP018
    v = float(0.0)  # noqa: UP018
    if face >= 0 and (i + step) % REFRESH_EVERY != 0:
        a = body.points[body.indices[3 * face]]
        b = body.points[body.indices[3 * face + 1]]
        c = body.points[body.indices[3 * face + 2]]
        normal = wp.normalize(wp.cross(b - a, c - a))
        h = wp.dot(x[i] - a, normal)
        q = x[i] - h * normal
        area = wp.dot(wp.cross(b - a, c - a), normal)
        la = wp.dot(wp.cross(b - q, c - q), normal) / area
        lb = wp.dot(wp.cross(c - q, a - q), normal) / area
        if la > 0.0 and lb > 0.0 and 1.0 - la - lb > 0.0 and wp.abs(h) < QUERY_MM / 1000.0:
            found = True
            p = q
            n = normal
            signed = h
            u = la
            v = lb
    if not found:
        query = wp.mesh_query_point_sign_normal(mesh, x[i], QUERY_MM / 1000.0)
        if not query.result:
            return
        if query.sign < 0.0:
            # The normal's sign fails in creases such as the armpit; the winding number does not.
            query = wp.mesh_query_point_sign_winding_number(mesh, x[i], QUERY_MM / 1000.0)
        face = query.face
        near_face[i] = face
        p = wp.mesh_eval_position(mesh, face, query.u, query.v)
        delta = x[i] - p
        distance = wp.length(delta)
        n = wp.mesh_eval_face_normal(mesh, face)
        if distance > 1.0e-9:
            n = delta / distance * query.sign
        signed = distance * query.sign
        u = query.u
        v = query.v
    near_uv[i] = wp.vec2(u, v)
    near_distance[i] = signed
    if signed < COLLISION_MM / 1000.0:
        target = p + n * (COLLISION_MM / 1000.0)
        # Coulomb friction on the substep's slide over the skin: held while it is within μ_s times
        # the push, else shortened by μ_k times it (the body's own move was given by `carry`).
        push = wp.length(target - x[i])
        slide = target - previous[i]
        slide = slide - wp.dot(slide, n) * n
        length = wp.length(slide)
        if length > 1.0e-12:
            held = friction[i] * push + adhesion * dt * dt  # μN + τA, as a move per substep
            if slip > 0.0:
                # (μN + τA)·min(1, v/slip): viscous below the slip speed (implicit, never a full
                # stop), capped at the full friction
                beta = held / (slip * dt)
                removal = wp.min(held, length * beta / (1.0 + beta))
                target = target - slide * (removal / length)
            elif length <= held:
                target = target - slide
            else:
                moving = friction_kinetic[i] * push + adhesion * dt * dt
                target = target - slide * wp.min(1.0, moving / length)
        contact_push[i] = contact_push[i] + (target - x[i])
        x[i] = target


@wp.kernel
def layer_sides(
    mesh: wp.uint64,
    ids: wp.array(dtype=int),
    x: wp.array(dtype=wp.vec3),
    side: wp.array(dtype=float),
):
    t = wp.tid()
    q = wp.mesh_query_point_sign_normal(mesh, x[ids[t]], LAYER_QUERY_MM / 1000.0)
    side[t] = 1.0
    if q.result:
        p = wp.mesh_eval_position(mesh, q.face, q.u, q.v)
        if wp.dot(x[ids[t]] - p, wp.mesh_eval_face_normal(mesh, q.face)) < 0.0:
            side[t] = -1.0


@wp.kernel
def collide_layer(
    mesh: wp.uint64,
    ids: wp.array(dtype=int),
    side: wp.array(dtype=float),
    x: wp.array(dtype=wp.vec3),
    w: wp.array(dtype=float),
    contact_push: wp.array(dtype=wp.vec3),
    distance: float,
):
    """Keep an upper-layer vertex `distance` off the under layer, on its own side."""
    i = ids[wp.tid()]
    if w[i] == 0.0:
        return
    q = wp.mesh_query_point_sign_normal(mesh, x[i], LAYER_QUERY_MM / 1000.0)
    if not q.result:
        return
    p = wp.mesh_eval_position(mesh, q.face, q.u, q.v)
    n = wp.mesh_eval_face_normal(mesh, q.face) * side[wp.tid()]
    h = wp.dot(x[i] - p, n)
    if h < distance:
        contact_push[i] = contact_push[i] + (distance - h) * n
        x[i] = x[i] + (distance - h) * n


@wp.kernel
def carry(
    mesh: wp.uint64,
    body_previous: wp.array(dtype=wp.vec3),
    x: wp.array(dtype=wp.vec3),
    w: wp.array(dtype=float),
    near_face: wp.array(dtype=int),
    near_uv: wp.array(dtype=wp.vec2),
    near_distance: wp.array(dtype=float),
):
    """Move a vertex lying on the body (within CARRY_MM) by the body's own move at that point."""
    i = wp.tid()
    face = near_face[i]
    if w[i] == 0.0 or face < 0 or near_distance[i] > CARRY_MM / 1000.0:
        return
    uv = near_uv[i]
    b = wp.mesh_get(mesh).indices
    old = uv[0] * body_previous[b[3 * face]] + uv[1] * body_previous[b[3 * face + 1]]
    old = old + (1.0 - uv[0] - uv[1]) * body_previous[b[3 * face + 2]]
    x[i] = x[i] + wp.mesh_eval_position(mesh, face, uv[0], uv[1]) - old


@wp.kernel
def lerp_body(
    start: wp.array(dtype=wp.vec3),
    end: wp.array(dtype=wp.vec3),
    f: float,
    points: wp.array(dtype=wp.vec3),
):
    i = wp.tid()
    points[i] = start[i] + f * (end[i] - start[i])


@wp.kernel
def predict(
    x: wp.array(dtype=wp.vec3),
    v: wp.array(dtype=wp.vec3),
    previous: wp.array(dtype=wp.vec3),
    w: wp.array(dtype=float),
    force: wp.array(dtype=wp.vec3),
    contact_push: wp.array(dtype=wp.vec3),
    dt: float,
):
    i = wp.tid()
    previous[i] = x[i]
    contact_push[i] = wp.vec3()
    if w[i] > 0.0:
        v[i] = v[i] + dt * w[i] * force[i]
        x[i] = x[i] + dt * v[i]


@wp.kernel
def update_velocity(
    x: wp.array(dtype=wp.vec3),
    v: wp.array(dtype=wp.vec3),
    previous: wp.array(dtype=wp.vec3),
    contact_push: wp.array(dtype=wp.vec3),
    dt: float,
):
    """Velocity from the move; a pushed vertex does not bounce off the surface.

    The push of a collision is a position change, so it would otherwise leave the vertex flying
    off; contact is inelastic. Friction already acted on the position, in `collide`.
    """
    i = wp.tid()
    vel = (x[i] - previous[i]) / dt
    push = contact_push[i]
    pushed = wp.length(push)
    if pushed > 1.0e-12:
        n = push / pushed
        away = wp.dot(vel, n)
        if away > 0.0:
            vel = vel - away * n
    v[i] = vel * wp.exp(-DAMPING_PER_S * dt)


def run(
    c: Cloth,
    seconds: float,
    body: Body | None = None,
    substeps_per_s=SUBSTEPS_PER_S,
    iterations=ITERATIONS,
):
    """Advance the cloth by `seconds` under gravity (y up); the body moves from start to end."""
    dt = 1.0 / substeps_per_s
    n = c.x.shape[0]
    steps = round(seconds * substeps_per_s)
    for step in range(steps):
        if body is not None:
            wp.copy(body.previous, body.mesh.points)
            if body.moving:
                args = [body.start, body.end, (step + 1) / steps, body.mesh.points]
                wp.launch(lerp_body, body.start.shape[0], args)
                body.mesh.refit()
                args = [body.mesh.id, body.previous, c.x, c.inv_mass, c.near_face, c.near_uv]
                wp.launch(carry, n, [*args, c.near_distance])
        args = [c.x, c.v, c.previous, c.inv_mass, c.force, c.contact_push, dt]
        wp.launch(predict, n, args)
        c.lam.zero_()
        c.hinge_lam.zero_()
        for _ in range(iterations):
            for ids in c.colours:
                args = [ids, c.faces, c.dm_inv, c.area, c.stiffness_scale, c.x, c.inv_mass]
                wp.launch(
                    solve_triangles, ids.shape[0], [*args, *c.course, *c.wale, c.lam, c.shear, dt]
                )
        for ids in c.hinge_colours:
            args = [ids, c.hinges, c.hinge_k, c.hinge_stiffness, c.x, c.inv_mass, c.hinge_lam, dt]
            wp.launch(solve_hinges, ids.shape[0], args)
        if c.layer_mesh is not None:
            c.layer_mesh.refit()
            args = [c.layer_mesh.id, c.layer_ids, c.layer_side, c.x, c.inv_mass, c.contact_push]
            wp.launch(collide_layer, c.layer_ids.shape[0], [*args, c.layer_distance])
        if body is not None:
            args = [body.mesh.id, c.x, c.inv_mass, c.near_face, c.near_uv, c.near_distance]
            wp.launch(
                collide,
                n,
                [
                    *args,
                    c.contact_push,
                    c.previous,
                    c.friction,
                    c.friction_kinetic,
                    c.slip,
                    c.adhesion,
                    dt,
                    step,
                ],
            )
        wp.launch(update_velocity, n, [c.x, c.v, c.previous, c.contact_push, dt])
