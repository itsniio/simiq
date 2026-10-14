"""Riding-pose presets stored as data files in data/poses/."""

import json
from pathlib import Path

import numpy as np

POSES = ("standing", "hoods", "drops")
POSES_DIR = Path(__file__).resolve().parents[3] / "data" / "poses"


def rotation(rx: float, ry: float, rz: float) -> np.ndarray:
    """Rotation matrix Rz·Ry·Rx from angles in degrees about the world axes."""
    x, y, z = np.radians([rx, ry, rz])
    rot_x = np.array([[1, 0, 0], [0, np.cos(x), -np.sin(x)], [0, np.sin(x), np.cos(x)]])
    rot_y = np.array([[np.cos(y), 0, np.sin(y)], [0, 1, 0], [-np.sin(y), 0, np.cos(y)]])
    rot_z = np.array([[np.cos(z), -np.sin(z), 0], [np.sin(z), np.cos(z), 0], [0, 0, 1]])
    return rot_z @ rot_y @ rot_x


def load_pose(name: str) -> dict[str, np.ndarray]:
    """Bone name to rotation matrix for a preset; bones not listed stay at rest."""
    if name not in POSES:
        raise ValueError(f"unknown pose {name!r}; available: {', '.join(POSES)}")
    data = json.loads((POSES_DIR / f"{name}.json").read_text())
    return {bone: rotation(*angles) for bone, angles in data["rotations_deg"].items()}
