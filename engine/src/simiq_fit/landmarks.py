"""Landmark vertex indices on the Anny template, from data/landmarks.json."""

import json
from pathlib import Path

LANDMARKS_PATH = Path(__file__).resolve().parents[3] / "data" / "landmarks.json"
LANDMARKS = (
    "c7",
    "acromion.L",
    "acromion.R",
    "shoulder.L",
    "shoulder.R",
    "armpit.L",
    "armpit.R",
    "waist_front",
    "waist_back",
    "hip_back",
    "hip_back_midline",
    "crotch",
    "elbow.L",
    "elbow.R",
    "knee.L",
    "knee.R",
)


def load_landmarks() -> dict:
    """The landmarks file: vertex indices by name, the waist ring, vertex count and provenance."""
    return json.loads(LANDMARKS_PATH.read_text())
