#!/usr/bin/env python3
"""Drain inbox/ into the collections: file images and models, inspect meshes.

One upload folder, one command. Files dropped in inbox/<collection>/ are
matched to their item by name, moved into place, and recorded in the set's
metadata.json. Meshes are additionally run through the print-fault inspector
and their report saved alongside.

    scripts/ingest.py                 everything waiting
    scripts/ingest.py --dry-run       show the plan, change nothing
    scripts/ingest.py statues         one collection only
    scripts/ingest.py --create        create pieces named by unmatched files

Routing lives in inbox/routes.json. See inbox/README.md.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from setlib import (  # noqa: E402
    SetError,
    write_notes,
    images_in,
    load_set,
    make_item_tree,
    match_by_slug,
    match_numbered,
    models_in,
    save_set,
)

ROOT = Path(__file__).resolve().parent.parent
INBOX = ROOT / "inbox"


def load_routes() -> dict[str, Path]:
    path = INBOX / "routes.json"
    if not path.is_file():
        raise SystemExit(f"error: {path} not found")
    return {name: ROOT / target for name, target in json.loads(path.read_text(encoding="utf-8")).items()}


def pair(files: list[Path], meta: dict, create: bool):
    """Match files to items, whichever kind of set this is."""
    if not files:
        return [], []
    if meta["numbered"]:
        if not meta["items"]:
            raise SetError("a numbered set must define its items in metadata.json first")
        return match_numbered(files, meta["items"]), []
    return match_by_slug(files, meta["items"], create)


def inspect(path: Path) -> str:
    """Run the mesh inspector and return its report."""
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "inspect_mesh.py"), str(path)],
        capture_output=True, text=True,
    )
    return (result.stdout + result.stderr).strip()


def place(source: Path, target: Path, dry_run: bool, force: bool) -> bool:
    if target.exists() and not force:
        print(f"    exists, skipped (use --force): {target.name}")
        return False
    if dry_run:
        return True
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(source), target)
    (target.parent / ".gitkeep").unlink(missing_ok=True)
    return True


def process(name: str, set_dir: Path, args) -> int:
    source_dir = INBOX / name
    images = images_in(source_dir)
    models = models_in(source_dir)
    if not images and not models:
        return 0

    print(f"\n{name}  ->  {set_dir.relative_to(ROOT)}")
    try:
        meta = load_set(set_dir)
    except SetError as exc:
        print(f"  error: {exc}", file=sys.stderr)
        return -1

    moved = 0
    for kind, files in (("image", images), ("model", models)):
        if not files:
            continue
        try:
            assignments, new_items = pair(files, meta, args.create)
        except SetError as exc:
            print(f"  error ({kind}s): {exc}", file=sys.stderr)
            return -1

        for path, item in assignments:
            flag = "  (new piece)" if item in new_items else ""
            if kind == "image":
                target = set_dir / meta["item_dir"] / item["id"] / "reference" / f"{item['id']}{path.suffix.lower()}"
            else:
                target = set_dir / meta["item_dir"] / item["id"] / "model" / "source" / f"{item['id']}{path.suffix.lower()}"
            print(f"  {path.name}  ->  {target.relative_to(set_dir)}{flag}")

            if not args.dry_run:
                make_item_tree(set_dir, meta, item)
            if not place(path, target, args.dry_run, args.force):
                continue
            moved += 1

            if args.dry_run:
                continue

            if kind == "image":
                item["reference_image"] = f"{meta['item_dir']}/{item['id']}/reference/{target.name}"
                if item.get("status") == "planned":
                    item["status"] = "reference-imported"
                write_notes(set_dir, meta, item, target.name)
            else:
                item["model_source"] = f"{meta['item_dir']}/{item['id']}/model/source/{target.name}"
                item["status"] = "model-imported"
                write_notes(set_dir, meta, item, None)
                if target.suffix.lower() == ".stl":
                    report = inspect(target)
                    report_path = target.parent / f"{target.stem}-inspection.txt"
                    report_path.write_text(report + "\n", encoding="utf-8")
                    for line in report.splitlines():
                        if any(k in line for k in ("watertight", "shells", "boundary edges",
                                                   "non-manifold", "triangles", "bounding box")):
                            print(f"      {line.strip()}")
                    print(f"      report: {report_path.relative_to(set_dir)}")
                    if "watertight             NO" in report:
                        fixed = target.parent.parent / "export" / f"{item['id']}-repaired.stl"
                        print(f"      to repair: scripts/inspect_mesh.py {target} \\\n"
                              f"                   --fix {fixed} --fill-holes --drop-shells")

        if not args.dry_run and new_items:
            meta["items"].extend(new_items)
            meta["items"].sort(key=lambda i: i["id"])

    if not args.dry_run and moved:
        save_set(set_dir, meta)
    return moved


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("collections", nargs="*", help="inbox subfolders to process (default: all)")
    p.add_argument("--dry-run", action="store_true", help="show the plan, change nothing")
    p.add_argument("--create", action="store_true", help="create pieces named by unmatched files")
    p.add_argument("--force", action="store_true", help="overwrite files already in place")
    args = p.parse_args()

    routes = load_routes()
    wanted = args.collections or list(routes)
    unknown = [c for c in wanted if c not in routes]
    if unknown:
        print(f"error: unknown collection(s): {', '.join(unknown)}", file=sys.stderr)
        print(f"known: {', '.join(routes)}", file=sys.stderr)
        return 1

    total = 0
    for name in wanted:
        result = process(name, routes[name], args)
        if result < 0:
            return 1
        total += result

    if total == 0:
        print("Nothing waiting in inbox/.")
    elif args.dry_run:
        print(f"\n{total} file(s) would be filed. (dry run — nothing moved)")
    else:
        print(f"\nFiled {total} file(s). inbox/ is clear.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except BrokenPipeError:
        sys.stderr.close()
        raise SystemExit(0)
