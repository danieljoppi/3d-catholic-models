#!/usr/bin/env python3
"""Check every set's metadata.json against what is actually on disk.

Catches the drift that breaks the tooling: an item in metadata with no folder,
a folder with no metadata entry, a reference_image path that does not resolve,
a stale item_count, or a numbered set whose numbers are not 1..N.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def check_set(meta_path: Path) -> list[str]:
    problems: list[str] = []
    where = meta_path.relative_to(ROOT)
    try:
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return [f"{where}: invalid JSON — {exc}"]

    for key in ("collection", "set", "item_dir", "item_file", "numbered", "items"):
        if key not in meta:
            problems.append(f"{where}: missing key '{key}'")
    if problems:
        return problems

    set_dir = meta_path.parent
    items = meta["items"]

    if meta.get("item_count") != len(items):
        problems.append(f"{where}: item_count is {meta.get('item_count')}, items has {len(items)}")

    ids = [i["id"] for i in items]
    if len(set(ids)) != len(ids):
        problems.append(f"{where}: duplicate item ids")

    if meta["numbered"]:
        numbers = sorted(i.get("number") for i in items)
        if numbers != list(range(1, len(items) + 1)):
            problems.append(f"{where}: numbered set is not 1..{len(items)}")

    # A companion is an item that ships with the set but is not part of the
    # canonical sequence — the Resurrection alongside the fourteen stations.
    # It keeps its number so file matching by number still works; what it does
    # not count toward is traditional_count. See ADR-0012.
    if "traditional_count" in meta:
        traditional = [i for i in items if not i.get("companion")]
        if meta["traditional_count"] != len(traditional):
            problems.append(
                f"{where}: traditional_count is {meta['traditional_count']}, "
                f"{len(traditional)} item(s) are not marked companion"
            )

    item_root = set_dir / meta["item_dir"]
    on_disk = {p.name for p in item_root.iterdir() if p.is_dir()} if item_root.is_dir() else set()

    for missing in sorted(set(ids) - on_disk):
        problems.append(f"{where}: '{missing}' in metadata has no folder")
    for orphan in sorted(on_disk - set(ids)):
        problems.append(f"{where}: folder '{orphan}' is not in metadata")

    for item in items:
        for key in ("reference_image", "model_source"):
            rel = item.get(key)
            if rel and not (set_dir / rel).is_file():
                problems.append(f"{where}: {item['id']}.{key} -> {rel} does not exist")

    return problems


def main() -> int:
    metas = sorted((ROOT / "collections").rglob("metadata.json"))
    if not metas:
        print("No sets found.", file=sys.stderr)
        return 1

    all_problems: list[str] = []
    for meta_path in metas:
        problems = check_set(meta_path)
        status = "ok" if not problems else f"{len(problems)} problem(s)"
        print(f"  {status:<16} {meta_path.parent.relative_to(ROOT)}")
        all_problems.extend(problems)

    if all_problems:
        print("\nProblems:", file=sys.stderr)
        for p in all_problems:
            print(f"  {p}", file=sys.stderr)
        return 1
    print(f"\n{len(metas)} set(s) consistent with the filesystem.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
