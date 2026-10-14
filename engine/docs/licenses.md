# Licenses of Anny and its dependencies

Task fit-engine-poc 2.4. The rule (CLAUDE.md, Constraints): Anny only, nothing SMPL-derived, no GPL code imported into `engine/` or `api/`.

## What `engine/` loads from Anny

| Part | Used | License | Source |
|---|---|---|---|
| Anny code (`anny` package, NAVER Corp.) | yes | Apache-2.0 | `LICENSE` in [naver/anny](https://github.com/naver/anny) |
| MakeHuman assets, `data/mpfb2` (mesh, blend shape targets, rig, skinning weights) | yes | CC0-1.0 | `src/anny/data/mpfb2/LICENSE.md` |
| Topology `anny` (default) | yes | as above: derived from the MakeHuman mesh | `simiq_fit.body.ANNY_TOPOLOGY` |
| Facial actions, `data/faceunits01` | no (`facial_actions="none"`) | CC0-1.0 | |
| SOMA topology and rig, `data/soma` | no | Apache-2.0 | |
| Topologies `smpl`, `smplx` and the `noncommercial.zip` download | **never** | non-commercial only | refused by `check_topology`; `anny[smpl]` extra not installed |

Anny downloads `noncommercial.zip` (SMPL / SMPL-X conversion data) only when an SMPL-family topology or conversion is requested (`anny/paths.py`). The spike run records whether `~/.cache/anny/noncommercial/` exists afterwards.

## Guard tests

`tests/test_body.py`:

- `check_topology` raises for `smpl`, `smplx` and their variants;
- `ANNY_TOPOLOGY` is `anny`;
- the `smplx` package (pulled only by `anny[smpl]`) is not installed.

## Python dependencies

Declared by Anny 0.6: torch, roma, numpy, pyyaml, pillow, requests, safetensors, trimesh, warp-lang. Declared by `engine/`: anny, torch, numpy, trimesh; dev only: pytest, ruff, matplotlib.

The authoritative list with versions is generated from the installed metadata by the spike run in [`anny-spike/dependency-licenses.md`](anny-spike/dependency-licenses.md). Status: **unverified** until that file is committed from a real run and read for GPL entries.
