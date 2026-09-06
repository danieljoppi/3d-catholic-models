#!/usr/bin/env python3
"""Inspect an STL for the faults that stop a print, and optionally repair them.

Meshes that come out of photogrammetry or AI reconstruction (Meshy, Tripo,
TRELLIS and friends) are usually watertight-ish but rarely print-ready. The
recurring faults are duplicate and degenerate triangles, inconsistent face
winding, stray floating shells, small holes, and arbitrary scale.

    scripts/inspect_mesh.py figure.stl
    scripts/inspect_mesh.py figure.stl --fix clean.stl --fill-holes --drop-shells
    scripts/inspect_mesh.py figure.stl --fix clean.stl --height-mm 180

What it does NOT do: detect self-intersections, or thicken walls that are too
thin to print. Both need more than this script; check them in the slicer.
"""

from __future__ import annotations

import argparse
import struct
import sys
from pathlib import Path

import numpy as np


# --------------------------------------------------------------------------- io

def read_stl(path: Path) -> np.ndarray:
    """Return an (n, 3, 3) array of triangles. Handles binary and ASCII."""
    raw = path.read_bytes()
    if len(raw) < 84:
        raise SystemExit(f"error: {path} is too small to be an STL")

    count = struct.unpack("<I", raw[80:84])[0]
    if len(raw) == 84 + count * 50:
        data = np.frombuffer(raw[84:], dtype=[("n", "<f4", 3), ("v", "<f4", (3, 3)), ("a", "<u2")])
        return data["v"].astype(np.float64)

    text = raw.decode("utf-8", errors="replace")
    if "facet" not in text:
        raise SystemExit(f"error: {path} is neither valid binary nor ASCII STL")
    values = [
        [float(p) for p in line.split()[1:4]]
        for line in text.splitlines()
        if line.strip().startswith("vertex")
    ]
    if len(values) % 3:
        raise SystemExit("error: ASCII STL has a vertex count that is not a multiple of 3")
    return np.asarray(values, dtype=np.float64).reshape(-1, 3, 3)


def write_stl(path: Path, vertices: np.ndarray, faces: np.ndarray) -> None:
    tri = vertices[faces]
    normals = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0])
    lengths = np.linalg.norm(normals, axis=1, keepdims=True)
    normals = np.divide(normals, lengths, out=np.zeros_like(normals), where=lengths > 1e-12)

    buf = np.zeros(len(faces), dtype=[("d", "<f4", 12), ("attr", "<u2")])
    buf["d"][:, 0:3] = normals
    buf["d"][:, 3:12] = tri.reshape(len(faces), 9)

    with open(path, "wb") as f:
        f.write(b"\0" * 80)
        f.write(struct.pack("<I", len(faces)))
        f.write(buf.tobytes())


# ---------------------------------------------------------------------- topology

def weld(tri: np.ndarray, decimals: int) -> tuple[np.ndarray, np.ndarray]:
    flat = tri.reshape(-1, 3)
    vertices, index = np.unique(np.round(flat, decimals), axis=0, return_inverse=True)
    return vertices, index.reshape(-1, 3)


def edge_table(faces: np.ndarray):
    e = np.vstack([faces[:, [0, 1]], faces[:, [1, 2]], faces[:, [2, 0]]])
    key = np.sort(e, axis=1)
    uniq, inverse, counts = np.unique(key, axis=0, return_inverse=True, return_counts=True)
    return uniq, inverse, counts


def components(faces: np.ndarray, n_vertices: int) -> np.ndarray:
    """Label each face by connected component, via union-find over vertices."""
    parent = np.arange(n_vertices)

    def find(a: int) -> int:
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a

    for f in faces:
        r = [find(int(v)) for v in f]
        for x in r[1:]:
            if x != r[0]:
                parent[x] = r[0]
    roots = np.array([find(int(f[0])) for f in faces])
    _, labels = np.unique(roots, return_inverse=True)
    return labels


def orient(faces: np.ndarray) -> tuple[np.ndarray, int]:
    """Make face winding consistent by walking the adjacency graph."""
    n = len(faces)
    edge_map: dict[tuple[int, int], list[int]] = {}
    for i, (a, b, c) in enumerate(faces):
        for u, v in ((a, b), (b, c), (c, a)):
            edge_map.setdefault((min(u, v), max(u, v)), []).append(i)

    out = faces.copy()
    seen = np.zeros(n, dtype=bool)
    flipped = 0
    for start in range(n):
        if seen[start]:
            continue
        seen[start] = True
        stack = [start]
        while stack:
            i = stack.pop()
            a, b, c = out[i]
            for u, v in ((a, b), (b, c), (c, a)):
                for j in edge_map.get((min(u, v), max(u, v)), ()):
                    if j == i or seen[j]:
                        continue
                    seen[j] = True
                    x, y, z = out[j]
                    # Neighbour agrees when it traverses the shared edge the other way.
                    if (u, v) in ((x, y), (y, z), (z, x)):
                        out[j] = [x, z, y]
                        flipped += 1
                    stack.append(j)
    return out, flipped


def signed_volume(vertices: np.ndarray, faces: np.ndarray) -> float:
    tri = vertices[faces]
    return float(np.einsum("ij,ij->i", tri[:, 0], np.cross(tri[:, 1], tri[:, 2])).sum() / 6.0)


def boundary_loops(faces: np.ndarray) -> list[list[int]]:
    """Ordered vertex loops around holes."""
    uniq, _, counts = edge_table(faces)
    border = uniq[counts == 1]
    if len(border) == 0:
        return []

    adj: dict[int, list[int]] = {}
    for a, b in border:
        adj.setdefault(int(a), []).append(int(b))
        adj.setdefault(int(b), []).append(int(a))

    loops: list[list[int]] = []
    unused = {(int(min(a, b)), int(max(a, b))) for a, b in border}
    while unused:
        a, b = next(iter(unused))
        unused.discard((a, b))
        loop = [a, b]
        while True:
            nxt = None
            for cand in adj.get(loop[-1], ()):
                key = (min(loop[-1], cand), max(loop[-1], cand))
                if key in unused:
                    nxt = cand
                    unused.discard(key)
                    break
            if nxt is None:
                break
            if nxt == loop[0]:
                break
            loop.append(nxt)
        loops.append(loop)
    return loops


def fill_holes(vertices: np.ndarray, faces: np.ndarray, max_edges: int):
    """Fan-fill each boundary loop from its centroid. Small holes only."""
    loops = boundary_loops(faces)
    new_vertices = [vertices]
    new_faces = [faces]
    filled = skipped = 0
    next_index = len(vertices)

    for loop in loops:
        if len(loop) < 3:
            continue
        if len(loop) > max_edges:
            skipped += 1
            continue
        centroid = vertices[loop].mean(axis=0)
        new_vertices.append(centroid[None, :])
        c = next_index
        next_index += 1
        patch = [(c, loop[i], loop[(i + 1) % len(loop)]) for i in range(len(loop))]
        new_faces.append(np.array(patch, dtype=np.int64))
        filled += 1

    return np.vstack(new_vertices), np.vstack(new_faces), filled, skipped


# -------------------------------------------------------------------------- main

def report(title: str, rows: list[tuple[str, str]]) -> None:
    print(f"\n{title}")
    for label, value in rows:
        print(f"  {label:<22} {value}")


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("mesh", type=Path)
    p.add_argument("--fix", type=Path, metavar="OUT.STL", help="write a repaired copy")
    p.add_argument("--weld-decimals", type=int, default=5,
                   help="rounding used to merge coincident vertices (default 5)")
    p.add_argument("--fill-holes", action="store_true", help="fan-fill boundary loops")
    p.add_argument("--max-hole-edges", type=int, default=200, help="largest loop to fill (default 200)")
    p.add_argument("--drop-shells", action="store_true",
                   help="keep only the largest connected shell")
    p.add_argument("--height-mm", type=float, help="uniformly scale so the tallest axis is this")
    args = p.parse_args()

    if not args.mesh.is_file():
        print(f"error: {args.mesh} not found", file=sys.stderr)
        return 1

    tri = read_stl(args.mesh)
    vertices, faces = weld(tri, args.weld_decimals)

    size = vertices.max(axis=0) - vertices.min(axis=0)
    report(f"{args.mesh}", [
        ("triangles", f"{len(faces):,}"),
        ("vertices (welded)", f"{len(vertices):,} (from {len(tri) * 3:,} corners)"),
        ("bounding box", f"{size[0]:.2f} x {size[1]:.2f} x {size[2]:.2f} (file units)"),
    ])

    areas = 0.5 * np.linalg.norm(np.cross(vertices[faces[:, 1]] - vertices[faces[:, 0]],
                                          vertices[faces[:, 2]] - vertices[faces[:, 0]]), axis=1)
    degenerate = int((areas <= 1e-12).sum())
    collapsed = int((faces[:, 0] == faces[:, 1]).sum() + (faces[:, 1] == faces[:, 2]).sum()
                    + (faces[:, 0] == faces[:, 2]).sum())
    _, unique_index, dup_counts = np.unique(np.sort(faces, axis=1), axis=0,
                                            return_index=True, return_counts=True)
    duplicates = int((dup_counts > 1).sum())

    _, _, counts = edge_table(faces)
    holes = int((counts == 1).sum())
    nonmanifold = int((counts > 2).sum())
    labels = components(faces, len(vertices))
    shells = int(labels.max() + 1)
    volume = signed_volume(vertices, faces)

    watertight = holes == 0 and nonmanifold == 0
    report("Topology", [
        ("degenerate faces", f"{degenerate:,}" + ("" if degenerate == 0 else "   <-- remove")),
        ("collapsed faces", f"{collapsed:,}"),
        ("duplicate faces", f"{duplicates:,}" + ("" if duplicates == 0 else "   <-- remove")),
        ("boundary edges", f"{holes:,}" + ("" if holes == 0 else "   <-- holes")),
        ("non-manifold edges", f"{nonmanifold:,}" + ("" if nonmanifold == 0 else "   <-- >2 faces share an edge")),
        ("shells", f"{shells}" + ("" if shells == 1 else "   <-- floating fragments")),
        ("watertight", "yes" if watertight else "NO"),
        ("signed volume", f"{volume / 1000:.2f} cm3 (units=mm)"
                          + ("" if volume > 0 else "   <-- normals inverted")),
    ])

    if not args.fix:
        if watertight and volume > 0 and degenerate == 0 and duplicates == 0 and shells == 1:
            print("\nNothing to fix. Check wall thickness and self-intersections in the slicer.")
        else:
            print("\nRe-run with --fix out.stl to repair"
                  + (" (add --fill-holes)" if holes else "")
                  + (" (add --drop-shells)" if shells > 1 else "")
                  + ".")
        return 0

    # ------------------------------------------------------------------ repair
    print("\nRepairing")
    keep = (areas > 1e-12)
    keep[np.setdiff1d(np.arange(len(faces)), unique_index)] = False
    removed = int((~keep).sum())
    faces = faces[keep]
    print(f"  removed {removed:,} degenerate/duplicate face(s)")

    if args.drop_shells:
        labels = components(faces, len(vertices))
        sizes = np.bincount(labels)
        if len(sizes) == 1:
            print("  single shell, nothing to drop")
        else:
            biggest = int(sizes.argmax())
            dropped = int((labels != biggest).sum())
            faces = faces[labels == biggest]
            print(f"  dropped {dropped:,} face(s) across {len(sizes) - 1} smaller shell(s)")

    if args.fill_holes:
        vertices, faces, filled, skipped = fill_holes(vertices, faces, args.max_hole_edges)
        print(f"  filled {filled} hole(s)" + (f", skipped {skipped} too large" if skipped else ""))

    faces, flipped = orient(faces)
    print(f"  reoriented {flipped:,} face(s)")

    volume = signed_volume(vertices, faces)
    if volume < 0:
        faces = faces[:, [0, 2, 1]]
        volume = -volume
        print("  flipped the whole mesh outward")

    # Drop unreferenced vertices first: a dropped shell must not skew the
    # bounding box that --height-mm is measured against.
    used, faces = np.unique(faces, return_inverse=True)
    vertices = vertices[used]
    faces = faces.reshape(-1, 3)

    if args.height_mm:
        current = (vertices.max(axis=0) - vertices.min(axis=0)).max()
        if current <= 0:
            print("  cannot scale a zero-size mesh", file=sys.stderr)
            return 1
        factor = args.height_mm / current
        vertices = vertices * factor
        volume *= factor ** 3
        print(f"  scaled by {factor:.4f} so the tallest axis is {args.height_mm} mm")

    _, _, counts = edge_table(faces)
    holes = int((counts == 1).sum())
    nonmanifold = int((counts > 2).sum())
    size = vertices.max(axis=0) - vertices.min(axis=0)

    write_stl(args.fix, vertices, faces)
    report(f"Wrote {args.fix}", [
        ("triangles", f"{len(faces):,}"),
        ("bounding box", f"{size[0]:.2f} x {size[1]:.2f} x {size[2]:.2f} mm"),
        ("boundary edges", f"{holes:,}"),
        ("non-manifold edges", f"{nonmanifold:,}"),
        ("watertight", "yes" if holes == 0 and nonmanifold == 0 else "NO — still needs work"),
        ("volume", f"{volume / 1000:.2f} cm3"),
        ("file", f"{args.fix.stat().st_size / 1e6:.1f} MB"),
    ])
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except BrokenPipeError:
        sys.stderr.close()
        raise SystemExit(0)
