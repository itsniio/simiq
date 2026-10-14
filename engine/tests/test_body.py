import importlib.util

import pytest

from simiq_fit.body import ANNY_TOPOLOGY, check_topology


def test_engine_uses_annys_own_topology():
    check_topology(ANNY_TOPOLOGY)
    assert ANNY_TOPOLOGY == "anny"


@pytest.mark.parametrize("topology", ["smplx", "smpl", "smplx-noeyes"])
def test_smpl_derived_topologies_are_refused(topology):
    # SMPL and SMPL-X topologies are non-commercial (CLAUDE.md, Constraints).
    with pytest.raises(ValueError, match="non-commercial"):
        check_topology(topology)


def test_annys_non_commercial_extra_is_not_installed():
    # `anny[smpl]` pulls the `smplx` package; it must never be a dependency.
    assert importlib.util.find_spec("smplx") is None
