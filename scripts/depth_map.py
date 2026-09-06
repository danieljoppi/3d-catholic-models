#!/usr/bin/env python3
"""Estimate a depth map from a reference image (16-bit grayscale PNG, near=white).

Needs torch and transformers, which are heavy — this is meant to run in CI
(see .github/workflows/relief.yml) or on a machine set up for it, not as part
of the everyday repo tooling.

The estimators here all predict *inverse* depth, so nearer is brighter, which
is what scripts/relief_from_heightmap.py wants.

Usage:
    scripts/depth_map.py reference.jpg -o depth.png
    scripts/depth_map.py reference.jpg -o depth.png --model Intel/dpt-large
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
from PIL import Image

# Tried in order; the first that loads wins. Ids move around, hence the list.
FALLBACK_MODELS = [
    "depth-anything/Depth-Anything-V2-Small-hf",
    "LiheYoung/depth-anything-small-hf",
    "Intel/dpt-hybrid-midas",
    "Intel/dpt-large",
]


def estimate(image: Image.Image, model_ids: list[str]):
    import torch
    from transformers import pipeline

    last_error: Exception | None = None
    for model_id in model_ids:
        try:
            print(f"loading {model_id} ...", flush=True)
            pipe = pipeline("depth-estimation", model=model_id, device=-1)
        except Exception as exc:  # noqa: BLE001 - any load failure moves to the next id
            print(f"  unavailable: {type(exc).__name__}: {exc}", flush=True)
            last_error = exc
            continue

        result = pipe(image)
        depth = result["predicted_depth"]
        while depth.ndim < 4:
            depth = depth.unsqueeze(0)
        depth = torch.nn.functional.interpolate(
            depth, size=image.size[::-1], mode="bicubic", align_corners=False
        )
        return depth[0, 0].detach().cpu().numpy().astype(np.float64), model_id

    raise SystemExit(f"error: no depth model could be loaded (last: {last_error})")


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("image", type=Path)
    p.add_argument("-o", "--out", type=Path, required=True)
    p.add_argument("--model", help="force one model id instead of trying the fallback list")
    args = p.parse_args()

    if not args.image.is_file():
        print(f"error: {args.image} not found", file=sys.stderr)
        return 1

    image = Image.open(args.image).convert("RGB")
    depth, used = estimate(image, [args.model] if args.model else FALLBACK_MODELS)

    span = depth.max() - depth.min()
    norm = (depth - depth.min()) / span if span > 1e-9 else np.zeros_like(depth)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray((norm * 65535).astype(np.uint16)).save(args.out)

    print(f"{args.out}")
    print(f"  model       {used}")
    print(f"  size        {image.size[0]} x {image.size[1]}")
    print(f"  raw range   {depth.min():.3f} to {depth.max():.3f} (inverse depth)")
    print(f"  written     16-bit grayscale, near = white")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
