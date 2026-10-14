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

The authoritative list with versions is generated from the installed metadata by the spike run: [`anny-spike/dependency-licenses.md`](anny-spike/dependency-licenses.md) (run 2026-10-14, macOS arm64).

Read on 2026-10-14: **no GPL or AGPL package is installed.** Licenses found: Apache-2.0 (anny, torch, warp-lang, requests, safetensors), BSD (numpy, roma, idna, networkx, sympy and others), MIT (trimesh, pyyaml, urllib3 and others), MIT-CMU (pillow), PSF (matplotlib, dev only; typing_extensions), MPL-2.0 (certifi).

- certifi (MPL-2.0) arrives through requests, which Anny uses only to download the non-commercial data we never request. MPL-2.0 is file-level copyleft: it applies to changes of certifi's own files, which we do not make.
- anny's own metadata has no license field; its repository states Apache-2.0 (`LICENSE`).
- After the spike run, `~/.cache/anny/noncommercial/` does not exist: nothing SMPL-derived was downloaded.
