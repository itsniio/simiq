"""Body measurements on a posed Anny mesh, defined by landmarks (docs/measurements.md)."""

import numpy as np

from simiq_fit.tape import surface_arc, surface_path


def back_length(vertices, faces, landmarks) -> float:
    """C7 down the spine to the back hip line, along the surface in the body's sagittal plane."""
    return surface_path(vertices, faces, **back_length_path(vertices, landmarks))


def back_length_path(vertices, landmarks) -> dict:
    """Start, end, plane normal and via point of the back-length path."""
    c7, hip, waist = (vertices[landmarks[n]] for n in ("c7", "hip_back_midline", "waist_back"))
    # The sagittal plane holds C7 and the hip point and is square to the shoulders' left-right axis.
    lateral = vertices[landmarks["acromion.L"]] - vertices[landmarks["acromion.R"]]
    down = (hip - c7) / np.linalg.norm(hip - c7)
    normal = lateral - (lateral @ down) * down
    return dict(start=c7, end=hip, normal=normal, via=waist)


CROTCH_BRIDGE_M = 0.01  # a trunk path within this of the crotch's height crosses straight to it


def vertical_trunk_girth(vertices, faces, landmarks) -> float:
    """Left shoulder top down the front, through the crotch and up the back: a bib's full loop."""
    return sum(length(arc) for arc in vertical_trunk_arcs(vertices, faces, landmarks))


def vertical_trunk_arcs(vertices, faces, landmarks) -> list[np.ndarray]:
    """Front and back halves, shoulder to crotch, bridged between the legs at crotch height."""
    crotch = vertices[landmarks["crotch"]]
    up = vertices[landmarks["c7"]] - crotch
    up /= np.linalg.norm(up)
    arcs = []
    for path in vertical_trunk_paths(vertices, landmarks):
        arc = surface_arc(vertices, faces, **path)
        # Where thighs touch, the section runs down a thigh before it reaches the crotch; a tape
        # pulled through the crotch spans that crease instead.
        first = int(np.argmax((arc - crotch) @ up <= CROTCH_BRIDGE_M))
        arcs.append(np.vstack([arc[: first + 1], crotch]))
    return arcs


def length(points) -> float:
    """Length of a polyline."""
    return float(np.linalg.norm(np.diff(points, axis=0), axis=1).sum())


def vertical_trunk_paths(vertices, landmarks) -> list[dict]:
    """The front and back halves, each in the plane through shoulder, crotch and its waist point."""
    shoulder, crotch = vertices[landmarks["shoulder.L"]], vertices[landmarks["crotch"]]
    paths = []
    for via in (vertices[landmarks["waist_front"]], vertices[landmarks["waist_back"]]):
        normal = np.cross(crotch - shoulder, via - shoulder)
        paths.append(dict(start=shoulder, end=crotch, normal=normal, via=via))
    return paths
