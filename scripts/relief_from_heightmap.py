#!/usr/bin/env python3
"""Turn a grayscale heightmap into a printable bas-relief panel (binary STL).

This is the deterministic half of the modelling pipeline. It does not invent
depth — it converts a heightmap you supply into a watertight solid:

    heightmap (grayscale)  ->  displaced front surface
                               + flat back plate
                               + side walls
                           ->  manifold STL

Where the heightmap comes from decides the quality of the result:

* A **depth map** from a monocular depth model (Depth Anything, Marigold, or
  any tool that outputs near=white) is the right input. Depth is what a relief
  encodes, so the mesh comes out reading correctly.
* A **luminance** conversion of the reference photo is a rough stand-in and
  will be wrong wherever tone and depth disagree — a dark robe in the
  foreground sinks, a bright wall behind pushes forward. Useful to preview the
  mechanics, not to print.
* A **hand-painted** heightmap gives full control and is how a careful relief
  is actually finished.

Usage:
    scripts/relief_from_heightmap.py depth.png -o panel.stl --width-mm 150
    scripts/relief_from_heightmap.py photo.jpg -o preview.stl --luminance
"""

from __future__ import annotations

import argparse
import struct
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter


def load_heightmap(path: Path, resolution: int, blur: float, gamma: float, invert: bool) -> np.ndarray:
    img = Image.open(path).convert("L")
    w, h = img.size
    nx = max(16, resolution)
    ny = max(16, round(nx * h / w))
    img = img.resize((nx, ny), Image.LANCZOS)
    if blur > 0:
        img = img.filter(ImageFilter.GaussianBlur(blur))

    a = np.asarray(img, dtype=np.float64) / 255.0
    if invert:
        a = 1.0 - a
    span = a.max() - a.min()
    a = (a - a.min()) / span if span > 1e-9 else np.zeros_like(a)
    if gamma != 1.0:
        a = a ** gamma
    return a


def build_relief(height: np.ndarray, width_mm: float, depth_mm: float, base_mm: float):
    """Front grid + fanned back plate + side walls. Returns (vertices, faces)."""
    ny, nx = height.shape
    pitch = width_mm / (nx - 1)

    xs = np.arange(nx) * pitch
    ys = np.arange(ny) * pitch
    gx, gy = np.meshgrid(xs, ys)
    gy = gy.max() - gy  # image row 0 is the top of the panel

    front = np.stack([gx.ravel(), gy.ravel(), (base_mm + height * depth_mm).ravel()], axis=1)

    def fid(x, y):
        return y * nx + x

    # Boundary ring, counter-clockwise seen from +z.
    ring = (
        [fid(x, ny - 1) for x in range(nx)]
        + [fid(nx - 1, y) for y in range(ny - 2, -1, -1)]
        + [fid(x, 0) for x in range(nx - 2, -1, -1)]
        + [fid(0, y) for y in range(1, ny - 1)]
    )
    n_ring = len(ring)

    back_ring = np.stack(
        [front[ring, 0], front[ring, 1], np.zeros(n_ring)], axis=1
    )
    centre = np.array([[front[:, 0].mean(), front[:, 1].mean(), 0.0]])

    vertices = np.vstack([front, back_ring, centre])
    off_back = len(front)
    off_centre = off_back + n_ring

    faces: list[tuple[int, int, int]] = []

    # Front surface, two triangles per cell, CCW from +z.
    x0, y0 = np.meshgrid(np.arange(nx - 1), np.arange(ny - 1))
    a = (y0 * nx + x0).ravel()
    b = a + 1
    c = a + nx
    d = c + 1
    faces.extend(zip(c.tolist(), b.tolist(), a.tolist()))
    faces.extend(zip(c.tolist(), d.tolist(), b.tolist()))

    # Side walls: each ring edge to its shadow on the back plane.
    for i in range(n_ring):
        j = (i + 1) % n_ring
        fa, fb = ring[i], ring[j]
        ba, bb = off_back + i, off_back + j
        faces.append((fa, bb, fb))
        faces.append((fa, ba, bb))

    # Back plate: fan from the centre, so no vertex is left T-junctioned.
    for i in range(n_ring):
        j = (i + 1) % n_ring
        faces.append((off_centre, off_back + j, off_back + i))

    return vertices, np.array(faces, dtype=np.int64)


def signed_volume(vertices: np.ndarray, faces: np.ndarray) -> float:
    """Volume in mm^3. Negative means the normals face inward."""
    tri = vertices[faces]
    return float(np.einsum("ij,ij->i", tri[:, 0], np.cross(tri[:, 1], tri[:, 2])).sum() / 6.0)


def is_manifold(faces: np.ndarray) -> tuple[bool, int]:
    """Every edge must be shared by exactly two triangles."""
    e = np.vstack([faces[:, [0, 1]], faces[:, [1, 2]], faces[:, [2, 0]]])
    e = np.sort(e, axis=1)
    _, counts = np.unique(e, axis=0, return_counts=True)
    bad = int((counts != 2).sum())
    return bad == 0, bad


def write_stl(path: Path, vertices: np.ndarray, faces: np.ndarray) -> None:
    tri = vertices[faces]
    n = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0])
    lengths = np.linalg.norm(n, axis=1, keepdims=True)
    n = np.divide(n, lengths, out=np.zeros_like(n), where=lengths > 1e-12)

    data = np.zeros((len(faces), 12), dtype=np.float32)
    data[:, 0:3] = n
    data[:, 3:12] = tri.reshape(len(faces), 9)

    with open(path, "wb") as f:
        f.write(b"\0" * 80)
        f.write(struct.pack("<I", len(faces)))
        buf = np.zeros(len(faces), dtype=[("d", "<f4", 12), ("attr", "<u2")])
        buf["d"] = data
        f.write(buf.tobytes())


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("heightmap", type=Path)
    p.add_argument("-o", "--out", type=Path, required=True, help="output .stl")
    p.add_argument("--width-mm", type=float, default=150.0, help="panel width (default 150)")
    p.add_argument("--depth-mm", type=float, default=12.0, help="relief depth above the base (default 12)")
    p.add_argument("--base-mm", type=float, default=3.0, help="backing plate thickness (default 3)")
    p.add_argument("--resolution", type=int, default=400, help="samples across the width (default 400)")
    p.add_argument("--blur", type=float, default=1.0, help="gaussian blur in pixels before displacing")
    p.add_argument("--gamma", type=float, default=1.0, help=">1 deepens shadows, <1 lifts them")
    p.add_argument("--invert", action="store_true", help="heightmap has near=black")
    p.add_argument("--luminance", action="store_true",
                   help="acknowledge the input is a photo, not a depth map (preview only)")
    args = p.parse_args()

    if not args.heightmap.is_file():
        print(f"error: {args.heightmap} not found", file=sys.stderr)
        return 1

    height = load_heightmap(args.heightmap, args.resolution, args.blur, args.gamma, args.invert)
    vertices, faces = build_relief(height, args.width_mm, args.depth_mm, args.base_mm)

    ok, bad = is_manifold(faces)
    if not ok:
        print(f"error: mesh is not manifold ({bad} bad edges) — not written", file=sys.stderr)
        return 1

    volume = signed_volume(vertices, faces)
    if volume <= 0:
        print("error: normals face inward — not written", file=sys.stderr)
        return 1

    args.out.parent.mkdir(parents=True, exist_ok=True)
    write_stl(args.out, vertices, faces)

    ny, nx = height.shape
    size = args.out.stat().st_size / 1e6
    print(f"{args.out}")
    print(f"  grid        {nx} x {ny}")
    print(f"  panel       {args.width_mm:.1f} x {args.width_mm * (ny - 1) / (nx - 1):.1f} mm")
    print(f"  thickness   {args.base_mm:.1f} to {args.base_mm + args.depth_mm:.1f} mm")
    print(f"  triangles   {len(faces):,}")
    print(f"  volume      {volume / 1000:.1f} cm3")
    print(f"  manifold    yes (closed, outward normals)")
    print(f"  file        {size:.1f} MB")
    if args.luminance:
        print("\n  NOTE: built from luminance, not depth — tone and depth disagree wherever\n"
              "  a dark object sits in front of a light one. Preview only.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
