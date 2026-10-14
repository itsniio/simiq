"""Tape-measure geometry on a triangle mesh: girths, limb profiles. Pure numpy, unit-agnostic."""

import numpy as np


def section_loops(vertices, faces, point, normal) -> list[np.ndarray]:
    """Closed polylines (3D points) where the plane through `point` with `normal` cuts the mesh."""
    normal = np.asarray(normal, float) / np.linalg.norm(normal)
    side = (vertices - np.asarray(point, float)) @ normal
    side = np.where(side == 0, 1e-12, side)  # a vertex on the plane counts as above it
    crossings = {}  # mesh edge -> point where it crosses the plane
    links = {}  # mesh edge -> the other crossed edges of the faces it belongs to
    face_sides = side[faces]
    for face in faces[(face_sides.min(axis=1) < 0) & (face_sides.max(axis=1) > 0)]:
        crossed = [
            (min(a, b), max(a, b))
            for a, b in ((face[0], face[1]), (face[1], face[2]), (face[2], face[0]))
            if side[a] * side[b] < 0
        ]
        if len(crossed) != 2:
            continue
        for edge in crossed:
            if edge not in crossings:
                a, b = edge
                t = side[a] / (side[a] - side[b])
                crossings[edge] = vertices[a] + t * (vertices[b] - vertices[a])
        links.setdefault(crossed[0], []).append(crossed[1])
        links.setdefault(crossed[1], []).append(crossed[0])
    loops, seen = [], set()
    for start in links:
        if start in seen:
            continue
        loop, previous, current = [], None, start
        while current not in seen:
            seen.add(current)
            loop.append(crossings[current])
            following = [e for e in links[current] if e != previous]
            if not following:
                break
            previous, current = current, following[0]
        if len(loop) >= 3:
            loops.append(np.array(loop))
    return loops


def hull_perimeter(points_2d: np.ndarray) -> float:
    """Perimeter of the convex hull (Andrew's monotone chain): what a tape around them reads."""
    pts = sorted(map(tuple, points_2d))

    def turns_left(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0]) > 0

    def half(sequence):
        chain = []
        for p in sequence:
            while len(chain) >= 2 and not turns_left(chain[-2], chain[-1], p):
                chain.pop()
            chain.append(p)
        return chain[:-1]

    hull = np.array(half(pts) + half(reversed(pts)))
    return float(np.linalg.norm(hull - np.roll(hull, 1, axis=0), axis=1).sum())


def plane_basis(normal):
    """Two unit vectors spanning the plane with this normal."""
    normal = np.asarray(normal, float) / np.linalg.norm(normal)
    helper = np.array([1.0, 0, 0]) if abs(normal[0]) < 0.9 else np.array([0, 1.0, 0])
    u = np.cross(normal, helper)
    u /= np.linalg.norm(u)
    return u, np.cross(normal, u)


def contains(polygon_2d, p) -> bool:
    """Even-odd rule point-in-polygon test."""
    x, y = p
    inside = False
    for (x1, y1), (x2, y2) in zip(polygon_2d, np.roll(polygon_2d, -1, axis=0), strict=True):
        if (y1 > y) != (y2 > y) and x < x1 + (y - y1) * (x2 - x1) / (y2 - y1):
            inside = not inside
    return inside


def girth(vertices, faces, point, normal) -> float:
    """Tape girth of the section around `point`: convex hull perimeter of its cross-section loop."""
    loops = section_loops(vertices, faces, point, normal)
    if not loops:
        raise ValueError("the plane does not cut the mesh")
    u, v = plane_basis(normal)
    point = np.asarray(point, float)
    flat = [np.column_stack([(loop - point) @ u, (loop - point) @ v]) for loop in loops]
    around = [f for f in flat if contains(f, (0.0, 0.0))]
    # Nested loops around the point -> the outermost; no loop around it -> the nearest one.
    if around:
        chosen = max(around, key=hull_perimeter)
    else:
        chosen = min(flat, key=lambda f: np.linalg.norm(f, axis=1).min())
    return hull_perimeter(chosen)


def limb_profile(vertices, faces, start, end, step) -> np.ndarray:
    """Girths perpendicular to the axis start->end, every `step` from the start."""
    start, end = np.asarray(start, float), np.asarray(end, float)
    axis = end - start
    length = np.linalg.norm(axis)
    distances = np.arange(0, length + 1e-9, step)
    return np.array([girth(vertices, faces, start + d * axis / length, axis) for d in distances])


def profile_at(profile, step, distance) -> float:
    """Girth at `distance` from the profile's start, linearly interpolated between steps."""
    last = (len(profile) - 1) * step
    if not 0 <= distance <= last + 1e-12:
        raise ValueError(f"distance {distance} is outside the profile (0 to {last})")
    return float(np.interp(distance, np.arange(len(profile)) * step, profile))
