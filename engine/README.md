# engine — `simiq_fit`

The fit engine (fit-engine-poc). Python 3.12, managed with [uv](https://docs.astral.sh/uv/).

```sh
cd engine
uv sync                 # first run downloads PyTorch and Anny
uv run pytest
uv run ruff check
```

Once per clone, from the repository root, turn on the hook that refuses commits with files under `data/private/`:

```sh
git config core.hooksPath .githooks
```

## Anny spike (tasks 2.1–2.4)

```sh
uv run python scripts/anny_spike.py
```

The first model build parses the MakeHuman assets and takes a few minutes; later runs use Anny's cache in `~/.cache/anny/`. The script poses five bodies in `standing`, `hoods` and `drops` (`../data/poses/`) and writes:

- `docs/anny-spike/<body>.png`: each pose from the side, from behind and below, and from the front, coloured by how much the skin's edges stretch (red) or compress (blue) against the rest pose;
- `docs/anny-spike/<body>-hips.png`: close-ups of the hips in `hoods` and `drops`, neutral colour;
- `docs/anny-spike/metrics.md`: edge strain per region, volume change, torso and hip angles, glTF reload check;
- `docs/anny-spike/dependency-licenses.md`: the declared license of every installed package;
- `out/<body>-<pose>.glb`: meshes for any glTF viewer (not committed).

The decision and its reasoning go in `docs/anny-spike.md`.

## Garment and fabric data (tasks 5.1, 5.2)

Garment and fabric records live in `../data/garments/` and `../data/fabrics/` (one JSON file each; `garment.py` holds the models and the rules). Fictional examples are in `../data/examples/`, the default zones of a jersey and of bib shorts in `../data/templates/`.

```sh
uv run simiq-fit validate-data            # every file in data/garments, data/fabrics, data/examples
uv run simiq-fit validate-data FILE...    # only these
uv run simiq-fit schema                   # rewrite data/schema/*.schema.json after changing a model
```

`validate-data` prints each error with its file and field, warnings for points of measure that do not grow from size to size, and exits with 1 if any file is invalid. A garment whose `fabrics` names a fabric id not among the checked files is an error.
