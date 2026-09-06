#!/usr/bin/env python3
"""Create a new piece in a set: folder tree, notes file, metadata entry.

Statues and nativity figures arrive one at a time rather than as a fixed
series, so each gets added when its idea does — before any image exists.

Usage:
    scripts/new_piece.py collections/statues/singles "Sacred Heart of Jesus"
    scripts/new_piece.py <set-dir> "São José Operário" --pt "São José Operário" \
        --la "Sanctus Ioseph Opifex" --feast "1 May" --attributes "carpenter's square,lily"
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from setlib import SetError, load_set, make_item_tree, save_set, slugify  # noqa: E402

TEMPLATE = """# {title}

| | |
|---|---|
| **Slug** | `{slug}` |
| **Português** | {pt} |
| **Latina** | {la} |
| **Feast** | {feast} |
| **Set** | {set_title} |

## Reference image

{image}

## Iconography

<!-- The attributes that make this figure recognisable — keys, lily, wounds,
     habit colour, what is held and in which hand. Getting these wrong is the
     one mistake a devotional model cannot survive. -->

- Attributes: {attributes}
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

- [ ] Reference image imported
- [ ] Model sculpted
- [ ] Mesh checked (manifold, no self-intersections)
- [ ] Exported to `model/export/`
- [ ] Test printed
- [ ] Render made
"""


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("set_dir", type=Path)
    parser.add_argument("title", help="the piece's name in English")
    parser.add_argument("--slug", help="override the derived slug")
    parser.add_argument("--pt", default="TODO", help="Portuguese title")
    parser.add_argument("--la", default="TODO", help="Latin title")
    parser.add_argument("--feast", default="TODO", help="feast day")
    parser.add_argument("--attributes", default="", help="comma-separated iconographic attributes")
    args = parser.parse_args()

    set_dir: Path = args.set_dir
    try:
        meta = load_set(set_dir)
    except SetError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    if meta["numbered"]:
        print(f"error: {set_dir} is a numbered set — its items are fixed in metadata.json", file=sys.stderr)
        return 1

    slug = args.slug or slugify(args.title)
    if any(i["id"] == slug for i in meta["items"]):
        print(f"error: '{slug}' already exists in this set", file=sys.stderr)
        return 1

    attributes = [a.strip() for a in args.attributes.split(",") if a.strip()]
    item = {
        "id": slug,
        "title": {"en": args.title, "pt-BR": None if args.pt == "TODO" else args.pt,
                  "la": None if args.la == "TODO" else args.la},
        "feast": None if args.feast == "TODO" else args.feast,
        "attributes": attributes,
        "reference_image": None,
        "status": "planned",
    }

    base = make_item_tree(set_dir, meta, item)
    notes = base / meta["item_file"]
    notes.write_text(
        TEMPLATE.format(
            title=args.title, slug=slug, pt=args.pt, la=args.la, feast=args.feast,
            set_title=meta.get("title", ""),
            image="_No reference image yet — drop one in `_inbox/` and run "
                  "`scripts/import_images.py`._",
            attributes=", ".join(attributes) if attributes else "",
        ),
        encoding="utf-8",
    )

    meta["items"].append(item)
    meta["items"].sort(key=lambda i: i["id"])
    save_set(set_dir, meta)

    print(f"Created {base}")
    print(f"  notes: {notes}")
    print(f"  next:  put an image named {slug}.jpg in {set_dir / '_inbox'}, then scripts/import_images.py {set_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
