#!/usr/bin/env python3
"""Pull finished models from a Meshy account into inbox/.

Authentication comes from the MESHY_API_KEY environment variable, never from
an argument — arguments end up in shell history, process lists and CI logs.

    export MESHY_API_KEY=...          # locally
    scripts/meshy.py list
    scripts/meshy.py fetch <task-id> --name sacred-heart-of-jesus
    scripts/meshy.py fetch-all --collection statues

In CI the key comes from a repository secret; see
.github/workflows/meshy-fetch.yml.

If Meshy changes its API, `--probe` prints the raw JSON of one page so the
field names below can be corrected against reality rather than guessed.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BASE = "https://api.meshy.ai"

# Task-listing endpoints, newest API version first. Both shapes are tried so a
# version bump degrades to the next rather than failing outright.
ENDPOINTS = [
    ("image-to-3d", "/openapi/v1/image-to-3d"),
    ("text-to-3d", "/openapi/v2/text-to-3d"),
]

# Order of preference when a task offers several formats.
FORMATS = ["stl", "glb", "obj", "fbx", "usdz"]


def api_key() -> str:
    key = os.environ.get("MESHY_API_KEY", "").strip()
    if not key:
        raise SystemExit(
            "error: MESHY_API_KEY is not set.\n"
            "  locally:  export MESHY_API_KEY=...\n"
            "  in CI:    add it as a repository secret named MESHY_API_KEY"
        )
    return key


def request(url: str, key: str) -> bytes:
    req = urllib.request.Request(url, headers={
        "Authorization": f"Bearer {key}",
        "Accept": "application/json",
    })
    try:
        with urllib.request.urlopen(req, timeout=60) as response:
            return response.read()
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")[:400]
        hint = ""
        if exc.code in (401, 403):
            hint = "\n  The key was rejected. Check it is current and has API access."
        raise SystemExit(f"error: {exc.code} {exc.reason} from {url}\n  {body}{hint}")
    except urllib.error.URLError as exc:
        raise SystemExit(f"error: cannot reach {url} — {exc.reason}")


def list_tasks(key: str, page_size: int) -> list[dict]:
    tasks: list[dict] = []
    for label, path in ENDPOINTS:
        query = urllib.parse.urlencode({"page_num": 1, "page_size": page_size})
        try:
            payload = json.loads(request(f"{BASE}{path}?{query}", key))
        except SystemExit as exc:
            print(f"  {label}: {exc}", file=sys.stderr)
            continue
        # The API has returned both a bare list and {"result": [...]}.
        items = payload if isinstance(payload, list) else payload.get("result", payload.get("data", []))
        for item in items or []:
            item["_kind"] = label
            tasks.append(item)
    return tasks


def model_urls(task: dict) -> dict:
    urls = task.get("model_urls") or task.get("model_url") or {}
    return urls if isinstance(urls, dict) else {"glb": urls}


def describe(task: dict) -> str:
    name = task.get("name") or task.get("prompt") or task.get("object_prompt") or "(unnamed)"
    available = ",".join(k for k in model_urls(task) if model_urls(task).get(k)) or "none"
    return (f"{task.get('id', '?'):<40} {task.get('status', '?'):<10} "
            f"{task['_kind']:<12} [{available}]  {str(name)[:48]}")


def download(url: str, target: Path) -> int:
    target.parent.mkdir(parents=True, exist_ok=True)
    with urllib.request.urlopen(url, timeout=300) as response, open(target, "wb") as out:
        size = 0
        while chunk := response.read(1 << 16):
            out.write(chunk)
            size += len(chunk)
    return size


def pick_format(urls: dict, wanted: str | None) -> tuple[str, str] | None:
    order = [wanted] if wanted else FORMATS
    for fmt in order:
        if urls.get(fmt):
            return fmt, urls[fmt]
    return None


def fetch_one(task: dict, collection: str, name: str | None, fmt: str | None, dry_run: bool) -> bool:
    if task.get("status") not in (None, "SUCCEEDED", "SUCCESS", "succeeded"):
        print(f"  {task.get('id')}: status {task.get('status')} — skipped")
        return False

    chosen = pick_format(model_urls(task), fmt)
    if not chosen:
        print(f"  {task.get('id')}: no downloadable model — skipped")
        return False

    extension, url = chosen
    sys.path.insert(0, str(ROOT / "scripts"))
    from setlib import slugify  # noqa: E402  (local import keeps startup cheap)

    stem = slugify(name or task.get("name") or task.get("prompt") or task.get("id"))
    target = ROOT / "inbox" / collection / f"{stem}.{extension}"

    if target.exists():
        print(f"  {stem}.{extension}: already in inbox — skipped")
        return False
    print(f"  {task.get('id')}  ->  inbox/{collection}/{stem}.{extension}")
    if dry_run:
        return True
    size = download(url, target)
    print(f"      {size / 1e6:.1f} MB")
    return True


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="command", required=True)

    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--page-size", type=int, default=30)
    common.add_argument("--dry-run", action="store_true")

    sub.add_parser("list", parents=[common], help="show recent tasks")

    probe = sub.add_parser("probe", parents=[common], help="dump raw JSON, to correct field names")
    probe.add_argument("--endpoint", help="only this path, e.g. /openapi/v2/text-to-3d")

    one = sub.add_parser("fetch", parents=[common], help="download one task")
    one.add_argument("task_id")
    one.add_argument("--name", help="piece slug to save as (default: the task's name)")
    one.add_argument("--collection", default="statues")
    one.add_argument("--format", dest="fmt", choices=FORMATS)

    every = sub.add_parser("fetch-all", parents=[common], help="download every finished task")
    every.add_argument("--collection", default="statues")
    every.add_argument("--format", dest="fmt", choices=FORMATS)

    args = p.parse_args()
    key = api_key()

    if args.command == "probe":
        paths = [args.endpoint] if args.endpoint else [path for _, path in ENDPOINTS]
        for path in paths:
            query = urllib.parse.urlencode({"page_num": 1, "page_size": min(args.page_size, 3)})
            print(f"\n--- {path} ---")
            try:
                print(json.dumps(json.loads(request(f"{BASE}{path}?{query}", key)), indent=2)[:4000])
            except SystemExit as exc:
                print(exc, file=sys.stderr)
        return 0

    tasks = list_tasks(key, args.page_size)
    if not tasks:
        print("No tasks returned. Try `probe` to see what the API is sending.")
        return 1

    if args.command == "list":
        print(f"{'task id':<40} {'status':<10} {'kind':<12} formats     name")
        for task in tasks:
            print(describe(task))
        print(f"\n{len(tasks)} task(s).")
        return 0

    if args.command == "fetch":
        match = next((t for t in tasks if str(t.get("id")) == args.task_id), None)
        if not match:
            print(f"error: task {args.task_id} not in the most recent {args.page_size}", file=sys.stderr)
            return 1
        fetch_one(match, args.collection, args.name, args.fmt, args.dry_run)
        return 0

    count = sum(fetch_one(t, args.collection, None, args.fmt, args.dry_run) for t in tasks)
    print(f"\n{count} model(s) {'would be ' if args.dry_run else ''}placed in inbox/{args.collection}/.")
    print("Then: scripts/ingest.py --create   (or just push)")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except BrokenPipeError:
        sys.stderr.close()
        raise SystemExit(0)
