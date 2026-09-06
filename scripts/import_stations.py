#!/usr/bin/env python3
"""Import downloaded Stations of the Cross images into their station folders.

Files dropped in a set's ``_inbox/`` are matched to stations and copied to
``stations/<NN-slug>/reference/``, then ``metadata.json`` is updated.

Matching, in order:
  1. a station number in the filename (``station-07``, ``07_via.jpg``, ``IMG_07``)
  2. otherwise, position in the natural sort order of the inbox

Usage:
    scripts/import_stations.py collections/stations-of-the-cross/set-01
    scripts/import_stations.py <set-dir> --dry-run
    scripts/import_stations.py <set-dir> --by-order   # ignore filename numbers
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
from pathlib import Path

IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".webp", ".heic", ".tif", ".tiff"}


def natural_key(path: Path):
    return [int(p) if p.isdigit() else p.lower() for p in re.split(r"(\d+)", path.name)]


def number_in_name(name: str, limit: int) -> int | None:
    """First integer in ``name`` that is a valid station number, else None."""
    for match in re.findall(r"\d+", name):
        value = int(match)
        if 1 <= value <= limit:
            return value
    return None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("set_dir", type=Path, help="set directory containing metadata.json and _inbox/")
    parser.add_argument("--inbox", type=Path, help="source directory (default: <set-dir>/_inbox)")
    parser.add_argument("--by-order", action="store_true", help="assign by sort order, ignoring numbers in filenames")
    parser.add_argument("--dry-run", action="store_true", help="print what would happen and change nothing")
    parser.add_argument("--move", action="store_true", help="move instead of copy")
    args = parser.parse_args()

    set_dir: Path = args.set_dir
    meta_path = set_dir / "metadata.json"
    if not meta_path.is_file():
        print(f"error: {meta_path} not found", file=sys.stderr)
        return 1

    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    stations = meta["stations"]
    by_number = {s["number"]: s for s in stations}

    inbox = args.inbox or set_dir / "_inbox"
    files = sorted(
        (p for p in inbox.iterdir() if p.is_file() and p.suffix.lower() in IMAGE_SUFFIXES),
        key=natural_key,
    )
    if not files:
        print(f"No images found in {inbox}. Download the album there first.")
        return 1

    if len(files) != len(stations):
        print(f"warning: {len(files)} image(s) for {len(stations)} stations — check the mapping below", file=sys.stderr)

    assignments: list[tuple[Path, dict]] = []
    if args.by_order:
        for path, station in zip(files, stations):
            assignments.append((path, station))
    else:
        used: set[int] = set()
        leftovers: list[Path] = []
        for path in files:
            number = number_in_name(path.stem, len(stations))
            if number is not None and number not in used:
                used.add(number)
                assignments.append((path, by_number[number]))
            else:
                leftovers.append(path)
        free = [s for s in stations if s["number"] not in used]
        if len(leftovers) > len(free):
            print("error: more unmatched images than free stations; re-run with --by-order", file=sys.stderr)
            return 1
        assignments.extend(zip(leftovers, free))
        assignments.sort(key=lambda pair: pair[1]["number"])

    for path, station in assignments:
        target_dir = set_dir / "stations" / station["id"] / "reference"
        target = target_dir / f"{station['id']}{path.suffix.lower()}"
        rel = target.relative_to(set_dir)
        print(f"{path.name}  ->  {rel}")
        if args.dry_run:
            continue
        target_dir.mkdir(parents=True, exist_ok=True)
        if args.move:
            shutil.move(str(path), target)
        else:
            shutil.copy2(path, target)
        station["reference_image"] = str(Path("stations") / station["id"] / "reference" / target.name)
        if station["status"] == "planned":
            station["status"] = "reference-imported"

    if args.dry_run:
        print("\n(dry run — nothing written)")
        return 0

    meta["source"]["downloaded"] = True
    meta_path.write_text(json.dumps(meta, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"\nImported {len(assignments)} image(s); updated {meta_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
