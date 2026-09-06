#!/usr/bin/env python3
"""Import downloaded images into the item folders of a collection set.

Files dropped in a set's ``_inbox/`` are matched to items and copied to
``<item_dir>/<id>/reference/``, then ``metadata.json`` is updated.

Matching depends on the set:

* **Numbered sets** (Stations of the Cross) — a number in the filename
  (``station-07``, ``07_via.jpg``), falling back to position in sort order.
* **Unnumbered sets** (statues, nativity) — the item slug appearing in the
  filename (``sacred-heart-of-jesus.jpg`` → ``sacred-heart-of-jesus``).
  With ``--create``, a file matching no existing item creates one from its
  filename, so a new figure needs no set-up beforehand.

Usage:
    scripts/import_images.py collections/stations-of-the-cross/set-01
    scripts/import_images.py collections/statues/singles --create
    scripts/import_images.py <set-dir> --dry-run
"""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from setlib import (  # noqa: E402
    SetError,
    images_in,
    load_set,
    make_item_tree,
    match_by_slug,
    match_numbered,
    save_set,
    write_notes,
)

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("set_dir", type=Path, help="set directory containing metadata.json and _inbox/")
    parser.add_argument("--inbox", type=Path, help="source directory (default: <set-dir>/_inbox)")
    parser.add_argument("--by-order", action="store_true", help="numbered sets: assign by sort order")
    parser.add_argument("--create", action="store_true", help="unnumbered sets: create items for unmatched files")
    parser.add_argument("--dry-run", action="store_true", help="print what would happen and change nothing")
    parser.add_argument("--move", action="store_true", help="move instead of copy")
    args = parser.parse_args()

    set_dir: Path = args.set_dir
    try:
        meta = load_set(set_dir)
    except SetError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    items = meta["items"]
    inbox = args.inbox or set_dir / "_inbox"
    files = images_in(inbox)
    if not files:
        print(f"No images found in {inbox}.")
        return 1

    try:
        if meta["numbered"]:
            if not items:
                raise SetError("a numbered set must define its items in metadata.json first")
            if len(files) != len(items):
                print(f"warning: {len(files)} image(s) for {len(items)} items — check the mapping below",
                      file=sys.stderr)
            assignments = match_numbered(files, items, args.by_order)
            new_items = []
        else:
            assignments, new_items = match_by_slug(files, items, args.create)
    except SetError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    for path, item in assignments:
        target_dir = set_dir / meta["item_dir"] / item["id"] / "reference"
        target = target_dir / f"{item['id']}{path.suffix.lower()}"
        flag = "  (new)" if item in new_items else ""
        print(f"{path.name}  ->  {target.relative_to(set_dir)}{flag}")
        if args.dry_run:
            continue

        make_item_tree(set_dir, meta, item)
        if args.move:
            shutil.move(str(path), target)
        else:
            shutil.copy2(path, target)
        (target_dir / ".gitkeep").unlink(missing_ok=True)

        item["reference_image"] = f"{meta['item_dir']}/{item['id']}/reference/{target.name}"
        if item.get("status") == "planned":
            item["status"] = "reference-imported"

        write_notes(set_dir, meta, item, target.name)

    if args.dry_run:
        print("\n(dry run — nothing written)")
        return 0

    items.extend(new_items)
    if not meta["numbered"]:
        items.sort(key=lambda i: i["id"])
    meta.setdefault("source", {})["downloaded"] = True
    save_set(set_dir, meta)

    created = f", created {len(new_items)} new item(s)" if new_items else ""
    print(f"\nImported {len(assignments)} image(s){created}; updated {set_dir / 'metadata.json'}")
    return 0


if __name__ == "__main__":
    # Exit quietly when piped into head/grep rather than tracing back.
    try:
        raise SystemExit(main())
    except BrokenPipeError:
        sys.stderr.close()
        raise SystemExit(0)
