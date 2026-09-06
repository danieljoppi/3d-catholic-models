"""Shared helpers for reading and writing a collection set."""

from __future__ import annotations

import json
import re
from pathlib import Path

IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".webp", ".heic", ".tif", ".tiff"}

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
