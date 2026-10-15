"""Jersey pieces from the CLO glb in Anny axes (m), with per-vertex texture colours."""
import sys
import numpy as np
import trimesh
from scipy.spatial import cKDTree

glb, out = sys.argv[1], sys.argv[2]
avatar = np.load(sys.argv[3])
scene = trimesh.load(glb)
tree = cKDTree(avatar)
pieces = []
for name, node in [(n, scene.graph.geometry_nodes[n][0]) for n in scene.geometry]:
    g = scene.geometry[name]
    mat, _ = scene.graph[node]
    v = trimesh.transform_points(g.vertices, mat)
    v = np.c_[v[:, 0], -v[:, 2], v[:, 1]] / 100
    col = g.visual.to_color().vertex_colors[:, :3]
    d, _ = tree.query(v)
    pieces.append((name, v, np.asarray(g.faces), col, np.asarray(g.visual.uv)))
    print(f"{name:28s} {len(v):6d} mean dist {d.mean()*100:5.2f} cm  colour {col.mean(0).round()}")
scene.geometry[next(iter(scene.geometry))].visual.material.baseColorTexture.convert('RGB').save(out.replace('.npz', '_atlas.png'))
np.savez(out, **{f"{i}_{k}": a for i, (n, v, f, c, uv) in enumerate(pieces)
                 for k, a in (("v", v), ("f", f), ("c", c), ("uv", uv))},
         names=np.array([p[0] for p in pieces]))
