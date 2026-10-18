"""Garment rest state from the flat pattern: spec scenarios of cloth-sim-spike task 2.1."""

import numpy as np
import pytest

from simiq_fit.garment_mesh import load_garment

UV_MM = (100.0, 200.0)  # mm per UV unit along u (course) and v (wale), as fitted for an export


def obj_text(pieces, material="FABRIC_main"):
    """An OBJ like CLO's: one material block per pattern piece, v and vt numbered alike."""
    lines, n = [], 0
    for positions, uvs, _faces in pieces:
        lines += [f"v {x} {y} {z}" for x, y, z in positions]
        lines += [f"vt {u} {v}" for u, v in uvs]
    lines.append("")
    for positions, _uvs, faces in pieces:
        lines.append(f"usemtl {material}")
        lines += [
            "f " + " ".join(f"{n + i + 1}/{n + i + 1}/{n + i + 1}" for i in face) for face in faces
        ]
        n += len(positions)
    return "\n".join(lines) + "\n"


def write(tmp_path, text):
    path = tmp_path / "garment.obj"
    path.write_text(text)
    return path


# One triangle: 10 mm along the course (u = 0.1 at 100 mm per unit) and 10 mm along the wale.
TRIANGLE = ([(0, 0, 0), (10, 0, 0), (0, 10, 0)], [(0, 0), (0.1, 0), (0, 0.05)], [(0, 1, 2)])


def test_rest_lengths_come_from_the_pattern(tmp_path):
    mesh = load_garment(write(tmp_path, obj_text([TRIANGLE])), UV_MM, [(0.72, 1.0)])
    rest = mesh.rest_mm[0]  # corners in (course, wale) mm
    assert np.linalg.norm(rest[1] - rest[0]) == pytest.approx(7.2)
    assert np.linalg.norm(rest[2] - rest[0]) == pytest.approx(10.0)


def two_pieces(gap_mm):
    """Two triangles that share the edge x = 10, the second one `gap_mm` away from it."""
    left = ([(0, 0, 0), (10, 0, 0), (10, 10, 0)], [(0, 0), (0.1, 0), (0.1, 0.05)], [(0, 1, 2)])
    right = (
        [(10 + gap_mm, 0, 0), (20, 0, 0), (10 + gap_mm, 10, 0)],
        [(0.3, 0), (0.4, 0), (0.3, 0.05)],
        [(0, 1, 2)],
    )
    return [left, right]


def test_seams_are_joined(tmp_path):
    mesh = load_garment(write(tmp_path, obj_text(two_pieces(0.4))), UV_MM, [(1, 1), (1, 1)])
    assert len(mesh.positions) == 4  # 6 corners, 2 of them welded across the seam
    assert mesh.piece.tolist() == [0, 1]
    assert len(set(mesh.faces[0]) & set(mesh.faces[1])) == 2  # the shared seam edge


def test_vertices_farther_than_the_weld_distance_stay_apart(tmp_path):
    mesh = load_garment(write(tmp_path, obj_text(two_pieces(0.6))), UV_MM, [(1, 1), (1, 1)])
    assert len(mesh.positions) == 6


def test_vertices_of_one_piece_are_never_welded(tmp_path):
    folded = ([(0, 0, 0), (10, 0, 0), (0, 0, 0.1)], [(0, 0), (0.1, 0), (0, 0.05)], [(0, 1, 2)])
    mesh = load_garment(write(tmp_path, obj_text([folded])), UV_MM, [(1, 1)])
    assert len(mesh.positions) == 3


def test_a_folded_piece_is_not_welded_to_itself_through_another(tmp_path):
    # A binding folded around an edge: its corners 0 and 2 both lie on the other piece's corner 0.
    binding = ([(0, 0, 0), (10, 0, 0), (0, 0, 0.3)], [(0, 0), (0.1, 0), (0, 0.05)], [(0, 1, 2)])
    edge_uv = [(0.3, 0), (0.3, 0.05), (0.35, 0.05)]
    edge = ([(0, 0, 0.1), (0, 10, 0), (5, 10, 0)], edge_uv, [(0, 1, 2)])
    mesh = load_garment(write(tmp_path, obj_text([binding, edge])), UV_MM, [(1, 1), (1, 1)])
    assert len(mesh.positions) == 5  # the nearer binding corner (0.1 mm) joins, the other stays
    assert all(len(set(face)) == 3 for face in mesh.faces)


def test_other_materials_are_left_out(tmp_path):
    text = obj_text([TRIANGLE]) + "usemtl Topstitch\nf 1/1/1 2/2/2 3/3/3\n"
    mesh = load_garment(write(tmp_path, text), UV_MM, [(1, 1)], fabric="FABRIC")
    assert len(mesh.faces) == 1


def test_positions_can_come_from_a_drape(tmp_path):
    draped = np.array([[0, 0, 5], [10, 0, 5], [0, 10, 5]], float)
    mesh = load_garment(write(tmp_path, obj_text([TRIANGLE])), UV_MM, [(1, 1)], positions=draped)
    assert mesh.positions[:, 2].tolist() == [5, 5, 5]


def test_missing_pattern_coordinates_are_refused(tmp_path):
    text = "v 0 0 0\nv 10 0 0\nv 0 10 0\nusemtl FABRIC_main\nf 1 2 3\n"
    with pytest.raises(ValueError, match="pattern piece 0 has no UV"):
        load_garment(write(tmp_path, text), UV_MM, [(1, 1)])


def test_zero_uv_area_names_the_piece(tmp_path):
    flat = ([(0, 0, 0), (10, 0, 0), (0, 10, 0)], [(0, 0), (0.1, 0), (0.2, 0)], [(0, 1, 2)])
    with pytest.raises(ValueError, match="pattern piece 1 has a triangle with zero UV area"):
        load_garment(write(tmp_path, obj_text([TRIANGLE, flat])), UV_MM, [(1, 1), (1, 1)])


def test_one_shrinkage_per_piece(tmp_path):
    with pytest.raises(ValueError, match="2 pattern pieces, 1 shrinkage"):
        load_garment(write(tmp_path, obj_text(two_pieces(0.4))), UV_MM, [(1, 1)])


def test_a_trim_takes_its_rest_shape_from_the_drape(tmp_path):
    # A zipper tape whose UV is a texture, not a pattern: its rest triangle is its draped one,
    # edges 3 and 4 mm (a 3-4-5 triangle) whatever its UV, and it is sewn to the fabric piece.
    fabric = ([(0, 0, 0), (10, 0, 0), (10, 10, 0)], [(0, 0), (0.1, 0), (0.1, 0.05)], [(0, 1, 2)])
    tape = ([(10, 0, 0), (13, 0, 0), (10, 0, 4)], [(0, 0), (9, 0), (0, 99)], [(0, 1, 2)])
    text = obj_text([fabric, tape]).replace("usemtl FABRIC_main\nf 4/", "usemtl Zipper_tape\nf 4/")
    mesh = load_garment(write(tmp_path, text), UV_MM, [(1, 1)], trims=("Zipper",))
    assert mesh.piece.tolist() == [0, 1]
    rest = mesh.rest_mm[1]
    edges = sorted(np.linalg.norm(rest[[1, 2, 0]] - rest, axis=1).round(6))
    assert edges == [3.0, 4.0, 5.0]
    assert len(mesh.positions) == 5  # the tape's corner at (10, 0, 0) is sewn to the fabric's
