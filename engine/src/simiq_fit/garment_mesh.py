"""A sewn garment mesh and the rest shape of each triangle from the flat pattern (cloth-sim D1)."""

from dataclasses import dataclass
from pathlib import Path

import numpy as np

WELD_MM = 0.5  # vertices of different pieces closer than this in the drape are one seam vertex
MIN_UV_AREA = 1e-12  # UV units², below it a triangle has no pattern shape


@dataclass
class GarmentMesh:
    positions: np.ndarray  # (n, 3) welded vertex positions, mm
    faces: np.ndarray  # (m, 3) indices into positions
    rest_mm: np.ndarray  # (m, 3, 2) each face's corners in the flat pattern, (course, wale) mm
    piece: np.ndarray  # (m,) pattern piece of each face
    weld: np.ndarray  # (raw vertex count,) raw OBJ vertex -> welded vertex, -1 when not fabric


def read_obj(path: Path):
    """Vertices, UVs and per-material-block faces of an OBJ as CLO writes it."""
    vertices, uvs, blocks = [], [], []
    for line in Path(path).read_text().splitlines():
        kind, *rest = line.split() or [""]
        if kind == "v":
            vertices.append([float(x) for x in rest[:3]])
        elif kind == "vt":
            uvs.append([float(x) for x in rest[:2]])
        elif kind == "usemtl":
            blocks.append((rest[0], []))
        elif kind == "f":
            corners = [corner.split("/") for corner in rest]
            blocks[-1][1].append(
                [(int(c[0]) - 1, int(c[1]) - 1 if len(c) > 1 and c[1] else -1) for c in corners]
            )
    return np.array(vertices, float), np.array(uvs, float).reshape(-1, 2), blocks


def weld(positions: np.ndarray, piece_of_vertex: np.ndarray, weld_mm: float) -> np.ndarray:
    """Map each vertex to a representative, joining vertices of different pieces within weld_mm.

    Pairs are joined nearest first, and never so that one seam vertex holds two vertices of the same
    piece (a binding folded over an edge would otherwise collapse onto itself).
    """
    cells = {}
    keys = np.floor(positions / weld_mm).astype(np.int64)
    for i, key in enumerate(map(tuple, keys)):
        cells.setdefault(key, []).append(i)
    offsets = [(a, b, c) for a in (-1, 0, 1) for b in (-1, 0, 1) for c in (-1, 0, 1)]
    pairs = []
    for i, (x, y, z) in enumerate(keys):
        for dx, dy, dz in offsets:
            for j in cells.get((x + dx, y + dy, z + dz), ()):
                distance = np.linalg.norm(positions[i] - positions[j])
                if j > i and piece_of_vertex[j] != piece_of_vertex[i] and distance <= weld_mm:
                    pairs.append((distance, i, j))
    parent = np.arange(len(positions))
    pieces = {i: {piece_of_vertex[i]} for i in range(len(positions))}

    def root(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    for _, i, j in sorted(pairs):
        a, b = root(i), root(j)
        if a != b and not pieces[a] & pieces[b]:
            parent[b] = a
            pieces[a] |= pieces.pop(b)
    return np.array([root(i) for i in range(len(positions))])


def laid_flat(triangles: np.ndarray) -> np.ndarray:
    """Each 3D triangle in its own plane: corner 0 at the origin, corner 1 on the first axis."""
    e1, e2 = triangles[:, 1] - triangles[:, 0], triangles[:, 2] - triangles[:, 0]
    length = np.linalg.norm(e1, axis=1)
    along = np.einsum("ij,ij->i", e2, e1) / length
    across = np.linalg.norm(np.cross(e1, e2), axis=1) / length
    zero = np.zeros_like(length)
    return np.stack([np.c_[zero, zero], np.c_[length, zero], np.c_[along, across]], axis=1)


def load_garment(
    path,
    uv_mm: tuple[float, float],
    shrinkage: list[tuple[float, float]],
    fabric: str = "FABRIC",
    positions: np.ndarray | None = None,
    weld_mm: float = WELD_MM,
    trims: tuple[str, ...] = (),
) -> GarmentMesh:
    """The fabric pieces of an OBJ, welded at seams, rest shapes from UV × uv_mm × shrinkage.

    uv_mm: mm per UV unit along u (course) and v (wale) for this export. shrinkage: per pattern
    piece, in material-block order, the simulation shrinkage as fractions (course, wale).
    positions: vertex positions to use instead of the OBJ's, e.g. a drape from a cache.
    trims: materials whose UV is not a pattern (a zipper tape); their pieces follow the fabric
    pieces and each triangle rests in the shape it has in `positions`.
    """
    vertices, uvs, blocks = read_obj(path)
    if positions is not None:
        vertices = np.asarray(positions, float)
    pieces = [faces for material, faces in blocks if fabric in material]
    trim_pieces = [faces for material, faces in blocks if any(t in material for t in trims)]
    if len(pieces) != len(shrinkage):
        raise ValueError(f"{len(pieces)} pattern pieces, {len(shrinkage)} shrinkage values")
    faces, rest, piece_of_face = [], [], []
    for k, (corners, (course, wale)) in enumerate(zip(pieces, shrinkage, strict=True)):
        corners = np.array(corners)  # (faces, 3, [vertex, uv])
        if (corners[:, :, 1] < 0).any():
            raise ValueError(f"pattern piece {k} has no UV coordinates")
        uv = uvs[corners[:, :, 1]]
        edge1, edge2 = uv[:, 1] - uv[:, 0], uv[:, 2] - uv[:, 0]
        if (np.abs(edge1[:, 0] * edge2[:, 1] - edge1[:, 1] * edge2[:, 0]) / 2 < MIN_UV_AREA).any():
            raise ValueError(f"pattern piece {k} has a triangle with zero UV area")
        faces.append(corners[:, :, 0])
        rest.append(uv * np.array(uv_mm) * np.array([course, wale]))
        piece_of_face += [k] * len(corners)
    for k, corners in enumerate(trim_pieces, start=len(pieces)):
        corners = np.array(corners)[:, :, 0]
        faces.append(corners)
        rest.append(laid_flat(vertices[corners]))
        piece_of_face += [k] * len(corners)
    piece_of_vertex = np.full(len(vertices), -1)
    for k, piece_faces in enumerate(faces):
        piece_of_vertex[np.unique(piece_faces)] = k
    faces = np.concatenate(faces)
    used = np.unique(faces)
    representative = weld(vertices[used], piece_of_vertex[used], weld_mm)
    welded_ids, compact = np.unique(representative, return_inverse=True)
    raw_to_welded = np.full(len(vertices), -1)
    raw_to_welded[used] = compact
    return GarmentMesh(
        positions=vertices[used][welded_ids],
        faces=raw_to_welded[faces],
        rest_mm=np.concatenate(rest),
        piece=np.array(piece_of_face),
        weld=raw_to_welded,
    )
