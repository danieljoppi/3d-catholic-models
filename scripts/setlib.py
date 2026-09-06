"""Shared helpers for reading and writing a collection set."""

from __future__ import annotations

import json
import re
from pathlib import Path

IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".webp", ".heic", ".tif", ".tiff"}
MODEL_SUFFIXES = {".stl", ".obj", ".glb", ".gltf", ".ply", ".3mf", ".fbx", ".blend", ".zip"}

# Words a slug keeps lowercase when a title is derived from it.
_MINOR = {"of", "the", "and", "in", "on", "at", "to", "de", "da", "do", "dos", "das"}


class SetError(Exception):
    """A set directory that cannot be used."""


def load_set(set_dir: Path) -> dict:
    meta_path = set_dir / "metadata.json"
    if not meta_path.is_file():
        raise SetError(f"{meta_path} not found — is this a set directory?")
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    meta.setdefault("item_dir", "pieces")
    meta.setdefault("item_file", "piece.md")
    meta.setdefault("numbered", False)
    meta.setdefault("items", [])
    return meta


def save_set(set_dir: Path, meta: dict) -> None:
    meta["item_count"] = len(meta["items"])
    path = set_dir / "metadata.json"
    path.write_text(json.dumps(meta, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def slugify(text: str) -> str:
    """A filesystem-safe slug: lowercase ASCII, hyphen separated."""
    replacements = {
        "á": "a", "à": "a", "â": "a", "ã": "a", "ä": "a",
        "é": "e", "ê": "e", "è": "e", "ë": "e",
        "í": "i", "ì": "i", "î": "i", "ï": "i",
        "ó": "o", "ò": "o", "ô": "o", "õ": "o", "ö": "o",
        "ú": "u", "ù": "u", "û": "u", "ü": "u",
        "ç": "c", "ñ": "n",
    }
    text = text.lower()
    for accented, plain in replacements.items():
        text = text.replace(accented, plain)
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return text.strip("-")


def title_from_slug(slug: str) -> str:
    """Best-effort human title for a slug, to be corrected by hand."""
    words = [w for w in slug.split("-") if w]
    out = []
    for i, w in enumerate(words):
        out.append(w if (i and w in _MINOR) else w.capitalize())
    return " ".join(out)


def natural_key(path: Path):
    return [int(p) if p.isdigit() else p.lower() for p in re.split(r"(\d+)", path.name)]


def images_in(directory: Path) -> list[Path]:
    if not directory.is_dir():
        return []
    return sorted(
        (p for p in directory.iterdir() if p.is_file() and p.suffix.lower() in IMAGE_SUFFIXES),
        key=natural_key,
    )


def models_in(directory: Path) -> list[Path]:
    if not directory.is_dir():
        return []
    return sorted(
        (p for p in directory.iterdir() if p.is_file() and p.suffix.lower() in MODEL_SUFFIXES),
        key=natural_key,
    )


def number_in_name(name: str, limit: int) -> int | None:
    """First integer in the name that could be an item number."""
    for match in re.findall(r"\d+", name):
        value = int(match)
        if 1 <= value <= limit:
            return value
    return None


def match_numbered(files: list[Path], items: list[dict], by_order: bool = False):
    """Pair files with numbered items by number in the filename, else sort order."""
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
        raise SetError("more unmatched files than free items; re-run with --by-order")
    assignments.extend(zip(leftovers, free))
    assignments.sort(key=lambda pair: pair[1]["number"])
    return assignments


def new_item(slug: str) -> dict:
    return {
        "id": slug,
        "title": {"en": title_from_slug(slug), "pt-BR": None, "la": None},
        "feast": None,
        "attributes": [],
        "reference_image": None,
        "status": "planned",
    }


def match_by_slug(files: list[Path], items: list[dict], create: bool):
    """Pair files with unnumbered items by slug. Returns (assignments, new_items)."""
    assignments: list[tuple[Path, dict]] = []
    new_items: list[dict] = []
    unmatched: list[Path] = []
    known = {i["id"]: i for i in items}

    for path in files:
        stem = slugify(path.stem)
        hit = known.get(stem)
        if hit is None:
            candidates = [i for i in items if i["id"] in stem]
            hit = max(candidates, key=lambda i: len(i["id"])) if candidates else None
        if hit is not None:
            assignments.append((path, hit))
        elif create:
            item = new_item(stem)
            known[stem] = item
            new_items.append(item)
            assignments.append((path, item))
        else:
            unmatched.append(path)

    if unmatched:
        names = "\n  ".join(p.name for p in unmatched)
        raise SetError(
            f"no item matches these files:\n  {names}\n"
            "Name each file after its piece (sacred-heart-of-jesus.stl), create the\n"
            "piece first with scripts/new_piece.py, or re-run with --create."
        )
    return assignments, new_items


def item_path(set_dir: Path, meta: dict, item: dict) -> Path:
    return set_dir / meta["item_dir"] / item["id"]


def make_item_tree(set_dir: Path, meta: dict, item: dict) -> Path:
    """Create the standard folder tree for one item and return its path."""
    base = item_path(set_dir, meta, item)
    for sub in ("reference", "model/source", "model/export", "renders"):
        (base / sub).mkdir(parents=True, exist_ok=True)
        keep = base / sub / ".gitkeep"
        if not any(p for p in (base / sub).iterdir() if p.name != ".gitkeep"):
            keep.touch()
    return base


PIECE_TEMPLATE = """# {title}

| | |
|---|---|
| **Slug** | `{slug}` |
| **Português** | TODO |
| **Latina** | TODO |
| **Feast** | TODO |
| **Set** | {set_title} |

## Reference image

{image_block}

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

{imported}
- [ ] Model sculpted
- [ ] Mesh checked (manifold, no self-intersections)
- [ ] Exported to `model/export/`
- [ ] Test printed
- [ ] Render made
"""


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


def write_notes(set_dir: Path, meta: dict, item: dict, image_name: str | None) -> Path:
    """Create the item's notes file if it has none; refresh it if it has."""
    notes = set_dir / meta["item_dir"] / item["id"] / meta["item_file"]
    if notes.exists():
        if image_name:
            refresh_notes(notes, item["id"], image_name)
        return notes

    if image_name:
        image_block = f"![{item['id']}](reference/{image_name})"
        imported = "- [x] Reference image imported"
    else:
        image_block = ("_No reference image yet — drop one in `inbox/` and run "
                       "`scripts/ingest.py`._")
        imported = "- [ ] Reference image imported"

    notes.parent.mkdir(parents=True, exist_ok=True)
    notes.write_text(
        PIECE_TEMPLATE.format(
            title=item["title"]["en"],
            slug=item["id"],
            set_title=meta.get("title", ""),
            image_block=image_block,
            imported=imported,
        ),
        encoding="utf-8",
    )
    return notes
