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
import re
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from setlib import (  # noqa: E402
    SetError,
    images_in,
    load_set,
    make_item_tree,
    save_set,
    slugify,
    title_from_slug,
)

PIECE_TEMPLATE = """# {title}

| | |
|---|---|
| **Slug** | `{slug}` |
| **Português** | TODO |
| **Latina** | TODO |
| **Feast** | TODO |
| **Set** | {set_title} |

## Reference image

![{slug}](reference/{slug}{ext})

## Iconography

<!-- The attributes that make this figure recognisable — keys, lily, wounds,
     habit colour, what is held and in which hand. Getting these wrong is the
     one mistake a devotional model cannot survive. -->

- Attributes:
- Vesture:
- Posture:

## Modelling notes

- Figures:
- Focal point:
- Watch when printing:

## Print notes

- Recommended size:
- Orientation:
- Supports:
- Layer height:

## Status

- [x] Reference image imported
- [ ] Model sculpted
- [ ] Mesh checked (manifold, no self-intersections)
- [ ] Exported to `model/export/`
- [ ] Test printed
- [ ] Render made
"""


def number_in_name(name: str, limit: int) -> int | None:
    for match in re.findall(r"\d+", name):
        value = int(match)
        if 1 <= value <= limit:
            return value
    return None


def match_numbered(files: list[Path], items: list[dict], by_order: bool) -> list[tuple[Path, dict]]:
    by_number = {i["number"]: i for i in items}
    if by_order:
        return list(zip(files, items))

    assignments: list[tuple[Path, dict]] = []
    used: set[int] = set()
    leftovers: list[Path] = []
    for path in files:
        number = number_in_name(path.stem, len(items))
        if number is not None and number not in used:
            used.add(number)
            assignments.append((path, by_number[number]))
        else:
            leftovers.append(path)

    free = [i for i in items if i["number"] not in used]
    if len(leftovers) > len(free):
        raise SetError("more unmatched images than free items; re-run with --by-order")
    assignments.extend(zip(leftovers, free))
    assignments.sort(key=lambda pair: pair[1]["number"])
    return assignments


def match_by_slug(files: list[Path], items: list[dict], create: bool, set_title: str):
    """Return (assignments, new_items). Slug match, optionally creating items."""
    assignments: list[tuple[Path, dict]] = []
    new_items: list[dict] = []
    unmatched: list[Path] = []
    known = {i["id"]: i for i in items}

    for path in files:
        stem = slugify(path.stem)
        hit = known.get(stem)
        if hit is None:
            # allow a filename that contains the slug, e.g. "01-sacred-heart-of-jesus"
            candidates = [i for i in items if i["id"] in stem]
            hit = max(candidates, key=lambda i: len(i["id"])) if candidates else None
        if hit is not None:
            assignments.append((path, hit))
        elif create:
            item = {
                "id": stem,
                "title": {"en": title_from_slug(stem), "pt-BR": None, "la": None},
                "feast": None,
                "attributes": [],
                "reference_image": None,
                "status": "planned",
            }
            known[stem] = item
            new_items.append(item)
            assignments.append((path, item))
        else:
            unmatched.append(path)

    if unmatched:
        names = "\n  ".join(p.name for p in unmatched)
        raise SetError(
            f"no item matches these files:\n  {names}\n"
            "Name each file after its piece (sacred-heart-of-jesus.jpg), create the\n"
            "piece first with scripts/new_piece.py, or re-run with --create."
        )
    return assignments, new_items


def refresh_notes(notes: Path, slug: str, filename: str) -> None:
    """Point an existing notes file at the image that just landed."""
    text = notes.read_text(encoding="utf-8")
    text = text.replace(
        "_No reference image yet — drop one in `_inbox/` and run "
        "`scripts/import_images.py`._",
        f"![{slug}](reference/{filename})",
    )
    text = text.replace("- [ ] Reference image imported", "- [x] Reference image imported")
    notes.write_text(text, encoding="utf-8")


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
            assignments, new_items = match_by_slug(files, items, args.create, meta.get("title", ""))
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

        notes = set_dir / meta["item_dir"] / item["id"] / meta["item_file"]
        if notes.exists():
            refresh_notes(notes, item["id"], target.name)
        else:
            notes.write_text(
                PIECE_TEMPLATE.format(
                    title=item["title"]["en"],
                    slug=item["id"],
                    ext=target.suffix,
                    set_title=meta.get("title", ""),
                ),
                encoding="utf-8",
            )

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
