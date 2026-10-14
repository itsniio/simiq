"""Body measurements on a posed Anny mesh, defined by landmarks (docs/measurements.md)."""

import numpy as np
from pydantic import BaseModel

from simiq_fit.tape import hull_girth, limb_profile, ring_girth, surface_arc, surface_path

PROFILE_STEP_CM = 2  # upper-arm and thigh girths are measured every 2 cm (design D4)
CHEST_SEARCH_CM = (1, 10)  # the chest girth is the largest one this far below the armpits


GIRTHS = ("chest_girth", "waist_girth", "hip_girth")
PROFILES = ("upper_arm_girth", "thigh_girth")
LENGTHS = ("back_length", "vertical_trunk_girth")


class Measurements(BaseModel):
    """Body measurements in one pose, in cm (design D4)."""

    pose: str
    girths_cm: dict[str, float]  # chest_girth, waist_girth, hip_girth
    profiles_cm: dict[str, list[float]]  # upper_arm_girth, thigh_girth; PROFILE_STEP_CM apart
    lengths_cm: dict[str, float]  # back_length, vertical_trunk_girth


def measure(
    vertices, faces, parts, landmarks, rings, joints, limb_starts, pose: str
) -> Measurements:
    """Every body measurement of a posed mesh.

    parts: face indices per body part (body.body_parts); rings: the waist_ring and hip_ring vertex
    indices of data/landmarks.json; joints: bone head positions; limb_starts: how far below its top
    joint each limb profile starts (limb_starts, from the standing body).
    """
    step = PROFILE_STEP_CM / 100
    limbs = {"upper_arm_girth": faces[parts["upper_arm.L"]], "thigh_girth": faces[parts["thigh.L"]]}
    sections = girth_sections(vertices, faces, parts, landmarks, rings["waist_ring"])
    girths = {
        n: hull_girth(vertices, s["faces"], s["point"], s["normal"]) for n, s in sections.items()
    }
    girths["hip_girth"] = ring_girth(vertices[rings["hip_ring"]])
    return Measurements(
        pose=pose,
        girths_cm={name: 100 * girths[name] for name in GIRTHS},
        profiles_cm={
            name: list(100 * limb_profile(vertices, limbs[name], start, end, step))
            for name, (start, end) in limb_axes(joints, limb_starts).items()
        },
        lengths_cm={
            "back_length": 100 * back_length(vertices, faces, landmarks),
            "vertical_trunk_girth": 100 * vertical_trunk_girth(vertices, faces, landmarks),
        },
    )


def measure_body(model, phenotype, pose: str) -> Measurements:
    """Pose a fitted body with a preset and measure it."""
    from simiq_fit.body import body_parts, pose_body
    from simiq_fit.landmarks import load_landmarks
    from simiq_fit.poses import load_pose

    rotations = load_pose(pose)  # an unknown pose fails here, before any body is built
    data = load_landmarks()
    landmarks = data["landmarks"]

    def joints_of(posed):
        return {name: posed["bone_poses"][i, :3, 3] for i, name in enumerate(model.bone_labels)}

    standing = pose_body(model, phenotype, {})
    starts = limb_starts(standing["vertices"], landmarks, joints_of(standing))
    posed = pose_body(model, phenotype, rotations)
    return measure(
        posed["vertices"],
        posed["faces"],
        body_parts(model),
        landmarks,
        {ring: data[ring] for ring in ("waist_ring", "hip_ring")},
        joints_of(posed),
        starts,
        pose,
    )


def torso_up(vertices, landmarks):
    """Unit vector from the crotch to C7: the torso's own up, leaning forward in a riding pose."""
    up = vertices[landmarks["c7"]] - vertices[landmarks["crotch"]]
    return up / np.linalg.norm(up)


def girth_sections(vertices, faces, parts, landmarks, waist_ring) -> dict[str, dict]:
    """Where chest and waist girths are taken: the faces cut, a point of the plane, its normal.

    Both planes are square to the torso. Chest: the fullest section of the torso faces 1 to 10 cm
    below the armpits. Waist: through the centre of Anny's waist ring.
    """
    up = torso_up(vertices, landmarks)
    torso = faces[parts["torso"]]
    armpits = (vertices[landmarks["armpit.L"]] + vertices[landmarks["armpit.R"]]) / 2
    below = np.arange(CHEST_SEARCH_CM[0], CHEST_SEARCH_CM[1] + 1) / 100
    chest = max((armpits - d * up for d in below), key=lambda p: hull_girth(vertices, torso, p, up))
    return {
        "chest_girth": dict(faces=torso, point=chest, normal=up),
        "waist_girth": dict(faces=torso, point=vertices[waist_ring].mean(axis=0), normal=up),
    }


# Profiles end this far before the elbow or knee joint: Anny's skinning gives the last few cm to the
# forearm or calf bones, so a section there cuts only part of the limb (a thin man's arm: 20.8 cm
# 4.4 cm before the elbow, 18.3 cm at 2.4 cm, nothing at the joint).
LIMB_END_BEFORE_JOINT_M = 0.04

LIMBS = {  # profile: (top joint, bottom joint, landmark where the limb leaves the torso)
    "upper_arm_girth": ("upperarm01.L", "lowerarm01.L", "armpit.L"),
    "thigh_girth": ("upperleg01.L", "lowerleg01.L", "crotch"),
}


def limb_starts(vertices, landmarks, joints) -> dict[str, float]:
    """On the standing body, how far below its top joint each limb leaves the torso (metres)."""
    starts = {}
    for name, (top, bottom, level) in LIMBS.items():
        a, b = np.asarray(joints[top]), np.asarray(joints[bottom])
        starts[name] = float((vertices[landmarks[level]] - a) @ (b - a) / np.linalg.norm(b - a))
    return starts


def limb_axes(joints, starts) -> dict[str, tuple]:
    """Start and end of each limb profile along its bone; both are fixed on the bone."""
    axes = {}
    for name, (top, bottom, _) in LIMBS.items():
        a, b = np.asarray(joints[top]), np.asarray(joints[bottom])
        axis = (b - a) / np.linalg.norm(b - a)
        axes[name] = (a + starts[name] * axis, b - LIMB_END_BEFORE_JOINT_M * axis)
    return axes


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
