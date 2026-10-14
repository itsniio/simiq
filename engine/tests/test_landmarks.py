from simiq_fit.landmarks import LANDMARKS, load_landmarks


def test_every_landmark_is_a_vertex_of_the_anny_topology():
    data = load_landmarks()
    assert data["topology"] == "anny"
    assert set(data["landmarks"]) == set(LANDMARKS)
    for name, index in data["landmarks"].items():
        assert isinstance(index, int) and 0 <= index < data["vertex_count"], name


def test_landmarks_are_distinct_vertices():
    indices = list(load_landmarks()["landmarks"].values())
    assert len(indices) == len(set(indices))


def test_waist_ring_is_a_loop_of_vertices():
    data = load_landmarks()
    ring = data["waist_ring"]
    assert len(ring) >= 10 and all(0 <= i < data["vertex_count"] for i in ring)
    assert data["landmarks"]["waist_front"] in ring


def test_every_landmark_has_a_rule_and_provenance():
    data = load_landmarks()
    assert set(data["rules"]) == set(LANDMARKS)
    assert "mark_landmarks.py" in data["provenance"]
