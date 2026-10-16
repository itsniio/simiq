"""Course and wale strain, pressure and zone means over a draped garment (cloth-sim D3, D4)."""

import numpy as np

from simiq_fit.fabric import tension_n_per_m
from simiq_fit.garment import Fabric


def deformation_gradients(rest_mm: np.ndarray, faces: np.ndarray, positions: np.ndarray):
    """Per face the 3×2 map F from the flat pattern (course, wale) to the drape: F = Ds · Dm⁻¹."""
    dm = np.stack([rest_mm[:, 1] - rest_mm[:, 0], rest_mm[:, 2] - rest_mm[:, 0]], axis=2)
    corners = positions[faces]
    ds = np.stack([corners[:, 1] - corners[:, 0], corners[:, 2] - corners[:, 0]], axis=2)
    return ds @ np.linalg.inv(dm)


def strains(rest_mm: np.ndarray, faces: np.ndarray, positions: np.ndarray) -> np.ndarray:
    """Per face (course, wale) strain: |F·u| − 1 and |F·v| − 1, u and v the pattern axes."""
    return np.linalg.norm(deformation_gradients(rest_mm, faces, positions), axis=1) - 1


def face_areas(faces: np.ndarray, positions: np.ndarray) -> np.ndarray:
    """Area of each face in the drape, mm²."""
    a, b, c = positions[faces[:, 0]], positions[faces[:, 1]], positions[faces[:, 2]]
    return np.linalg.norm(np.cross(b - a, c - a), axis=1) / 2


def zone_means(values: np.ndarray, areas: np.ndarray, zones: dict[str, np.ndarray]) -> dict:
    """Area-weighted mean of a per-face value in each zone (face indices); NaN faces left out."""
    means = {}
    for name, ids in zones.items():
        known = ids[~np.isnan(values[ids])]
        means[name] = float(values[known] @ areas[known] / areas[known].sum())
    return means


def vertex_normals(positions: np.ndarray, faces: np.ndarray) -> np.ndarray:
    """Unit normal at each vertex, its faces' normals weighted by their angle there."""
    x = positions[faces]
    face_normal = np.cross(x[:, 1] - x[:, 0], x[:, 2] - x[:, 0])
    face_normal /= np.linalg.norm(face_normal, axis=1, keepdims=True)
    normals = np.zeros_like(positions)
    for k in range(3):
        to_next, to_prev = x[:, (k + 1) % 3] - x[:, k], x[:, (k + 2) % 3] - x[:, k]
        cos = np.einsum("mi,mi->m", to_next, to_prev) / (
            np.linalg.norm(to_next, axis=1) * np.linalg.norm(to_prev, axis=1)
        )
        np.add.at(normals, faces[:, k], face_normal * np.arccos(np.clip(cos, -1, 1))[:, None])
    return normals / np.linalg.norm(normals, axis=1, keepdims=True)


def normal_curvatures(positions, faces, directions, at=None):
    """Normal curvature of the surface along each direction, 1/mm, positive where convex.

    at: the face each direction is taken on (default: direction i on face i); a direction off the
    face's plane is projected onto it.
    """
    normals = vertex_normals(positions, faces)
    at_faces = faces if at is None else faces[at]
    x, n = positions[at_faces], normals[at_faces]
    edges = np.stack([x[:, 1] - x[:, 0], x[:, 2] - x[:, 0]], axis=2)
    turns = np.stack([n[:, 1] - n[:, 0], n[:, 2] - n[:, 0]], axis=2)
    e1 = edges[:, :, 0] / np.linalg.norm(edges[:, :, 0], axis=1, keepdims=True)
    face_normal = np.cross(edges[:, :, 0], edges[:, :, 1])
    e2 = np.cross(face_normal / np.linalg.norm(face_normal, axis=1, keepdims=True), e1)
    basis = np.stack([e1, e2], axis=2)  # (m, 3, 2) orthonormal tangent frame
    to_plane = basis.transpose(0, 2, 1)
    shape = to_plane @ turns @ np.linalg.inv(to_plane @ edges)  # dn = S · dx in the face's plane
    shape = (shape + shape.transpose(0, 2, 1)) / 2
    d = (to_plane @ directions[:, :, None])[:, :, 0]
    return np.einsum("mi,mij,mj->m", d, shape, d) / np.einsum("mi,mi->m", d, d)


def pressures(rest_mm, faces, positions, fabric: Fabric, body) -> np.ndarray:
    """Per face p = T_c·κ_c + T_w·κ_w in Pa (Laplace); NaN where a strain is beyond its curve.

    body: (positions, faces, the body face under each garment face); κ is the body's (D4).
    """
    f = deformation_gradients(rest_mm, faces, positions)
    eps = np.linalg.norm(f, axis=1) - 1
    p = np.zeros(len(faces))
    for k, direction in enumerate(("course", "wale")):
        curve = fabric.curves[direction]
        tension = np.array(
            [tension_n_per_m(curve, e, fabric.specimen_width_mm) for e in eps[:, k]], dtype=float
        )  # None beyond the curve becomes NaN
        kappa_per_m = normal_curvatures(body[0], body[1], f[:, :, k], at=body[2]) * 1000
        p += tension * kappa_per_m
    return p
