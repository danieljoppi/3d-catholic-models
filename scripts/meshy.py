#!/usr/bin/env python3
"""Pull finished models from a Meshy account into inbox/.

Authentication comes from the MESHY_API_KEY environment variable, never from
an argument — arguments end up in shell history, process lists and CI logs.

    export MESHY_API_KEY=...          # locally
    scripts/meshy.py balance
    scripts/meshy.py list
    scripts/meshy.py fetch <task-id> --name sacred-heart-of-jesus
    scripts/meshy.py fetch-all --collection statues

In CI the key comes from a repository secret; see
.github/workflows/meshy-fetch.yml.

This sees API tasks only. Models generated in the Meshy web app live in a
workspace the API cannot read, so `list` reports nothing however full My Assets
looks — export those by hand into inbox/. See ADR-0010.

`probe` dumps the raw JSON of one page, to correct the field names below
against reality if the API ever drifts.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BASE = "https://api.meshy.ai"

# Verified against the live API on 2026-09-07. These two paths exist and
# answer 200 with a bare JSON list; /openapi/v1/text-to-3d and
# /openapi/v2/image-to-3d answer 404 NoMatchingRoute. Version numbers differ
# per task type on purpose — they are not a typo.
ENDPOINTS = [
    ("image-to-3d", "/openapi/v1/image-to-3d"),
    ("text-to-3d", "/openapi/v2/text-to-3d"),
]
BALANCE = "/openapi/v1/balance"          # -> {"balance": 75}

# Documented model_urls keys, printable formats first: this is a 3D printing
# project, so STL and 3MF matter and usdz is a courtesy.
FORMATS = ["stl", "3mf", "obj", "glb", "fbx", "usdz"]

# The API rejects a larger page; pagination walks pages instead.
PAGE_MAX = 50
DOWNLOADABLE = "SUCCEEDED"


class ApiError(Exception):
    """A non-2xx answer from Meshy, with its message unwrapped."""

    def __init__(self, code: int | None, message: str, url: str):
        super().__init__(message)
        self.code = code
        self.url = url

    def __str__(self) -> str:
        code = f"{self.code} " if self.code else ""
        return f"{code}from {self.url} — {super().__str__()}"


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
        raw = exc.read().decode("utf-8", errors="replace")
        # Request errors come back as {"message": "..."}; fall back to the body.
        try:
            message = json.loads(raw).get("message", raw)
        except json.JSONDecodeError:
            message = raw[:400]
        if exc.code in (401, 403):
            message += "\n  The key was rejected. Check it is current and has API access."
        elif exc.code == 402:
            message += "\n  Out of credits — check `scripts/meshy.py balance`."
        elif exc.code == 429:
            message += "\n  Rate limited. Wait and try again."
        raise ApiError(exc.code, message, url) from exc
    except urllib.error.URLError as exc:
        raise ApiError(None, f"cannot reach it — {exc.reason}", url) from exc


def get(path: str, key: str, **params) -> object:
    url = f"{BASE}{path}"
    if params:
        url += "?" + urllib.parse.urlencode(params)
    return json.loads(request(url, key))


def balance(key: str) -> int | None:
    payload = get(BALANCE, key)
    return payload.get("balance") if isinstance(payload, dict) else None


def page_of(payload: object) -> list[dict]:
    """The listings return a bare list; tolerate an envelope if that changes."""
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    if isinstance(payload, dict):
        items = payload.get("result") or payload.get("data") or []
        return [item for item in items if isinstance(item, dict)]
    return []


def list_tasks(key: str, page_size: int, max_pages: int = 20) -> list[dict]:
    page_size = max(1, min(page_size, PAGE_MAX))
    tasks: list[dict] = []
    for label, path in ENDPOINTS:
        for page in range(1, max_pages + 1):
            try:
                items = page_of(get(path, key, page_num=page, page_size=page_size,
                                    sort_by="-created_at"))
            except ApiError as exc:
                print(f"  {label}: {exc}", file=sys.stderr)
                break
            for item in items:
                item["_kind"] = label
                tasks.append(item)
            if len(items) < page_size:
                break
    return tasks


def retrieve(task_id: str, key: str) -> dict | None:
    """One task by id, asking each task type in turn."""
    for label, path in ENDPOINTS:
        try:
            task = get(f"{path}/{urllib.parse.quote(task_id)}", key)
        except ApiError as exc:
            if exc.code in (400, 404):
                continue
            raise
        if isinstance(task, dict) and task.get("id"):
            task["_kind"] = label
            return task
    return None


def model_urls(task: dict) -> dict:
    urls = task.get("model_urls")
    return {k: v for k, v in urls.items() if isinstance(v, str) and v} if isinstance(urls, dict) else {}


def label_of(task: dict) -> str:
    """Text tasks carry their prompt; image tasks carry no name at all."""
    return str(task.get("prompt") or task.get("texture_prompt") or "").strip()


def when(task: dict) -> str:
    stamp = task.get("created_at")
    if not isinstance(stamp, (int, float)):
        return "?"
    return time.strftime("%Y-%m-%d", time.gmtime(stamp / 1000))  # ms since epoch


def describe(task: dict) -> str:
    available = ",".join(k for k in FORMATS if k in model_urls(task)) or "none"
    status = str(task.get("status", "?"))
    if status not in (DOWNLOADABLE, "FAILED", "CANCELED") and task.get("progress") is not None:
        status = f"{status} {task['progress']}%"
    return (f"{str(task.get('id', '?')):<38} {status:<18} {task['_kind']:<12} "
            f"{when(task):<11} [{available:<20}] {label_of(task)[:44]}")


def no_tasks_note() -> str:
    return (
        "No tasks in this API account.\n"
        "\n"
        "  If My Assets in the Meshy web app is full, that is expected: the API and\n"
        "  the web workspace hold separate assets and neither can see the other's.\n"
        "  Export those models from the web app and drop them in inbox/ instead —\n"
        "  see docs/adr/0010-meshy-workspace-is-not-the-api.md.\n"
        "\n"
        "  `scripts/meshy.py probe` shows the raw response if you want to be sure."
    )


def download(url: str, target: Path) -> int:
    # A presigned URL: the Authorization header must not be sent with it.
    target.parent.mkdir(parents=True, exist_ok=True)
    partial = target.with_suffix(target.suffix + ".part")
    try:
        with urllib.request.urlopen(url, timeout=300) as response, open(partial, "wb") as out:
            size = 0
            while chunk := response.read(1 << 16):
                out.write(chunk)
                size += len(chunk)
    except urllib.error.HTTPError as exc:
        partial.unlink(missing_ok=True)
        hint = "\n      Download links expire; re-run `list` for fresh ones." if exc.code in (400, 403) else ""
        raise ApiError(exc.code, f"download refused{hint}", url) from exc
    except urllib.error.URLError as exc:
        partial.unlink(missing_ok=True)
        raise ApiError(None, f"download failed — {exc.reason}", url) from exc
    partial.replace(target)
    return size


def pick_format(urls: dict, wanted: str | None) -> tuple[str, str] | None:
    for fmt in [wanted] if wanted else FORMATS:
        if urls.get(fmt):
            return fmt, urls[fmt]
    return None


def fetch_one(task: dict, collection: str, name: str | None, fmt: str | None, dry_run: bool) -> bool:
    task_id = str(task.get("id", "?"))
    if task.get("status") != DOWNLOADABLE:
        print(f"  {task_id}: status {task.get('status')} — skipped")
        return False

    chosen = pick_format(model_urls(task), fmt)
    if not chosen:
        offered = ",".join(model_urls(task)) or "none"
        print(f"  {task_id}: no {fmt or 'usable'} model (has: {offered}) — skipped")
        return False

    extension, url = chosen
    sys.path.insert(0, str(ROOT / "scripts"))
    from setlib import slugify  # noqa: E402  (local import keeps startup cheap)

    stem = slugify(name or label_of(task) or task_id)
    target = ROOT / "inbox" / collection / f"{stem}.{extension}"

    if target.exists():
        print(f"  {stem}.{extension}: already in inbox — skipped")
        return False
    print(f"  {task_id}  ->  inbox/{collection}/{stem}.{extension}")
    if dry_run:
        return True
    size = download(url, target)
    print(f"      {size / 1e6:.1f} MB")
    return True


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="command", required=True)

    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--page-size", type=int, default=PAGE_MAX, help=f"1-{PAGE_MAX} (default {PAGE_MAX})")
    common.add_argument("--dry-run", action="store_true")

    sub.add_parser("balance", help="credits left in the account")
    sub.add_parser("list", parents=[common], help="show recent tasks")

    probe = sub.add_parser("probe", parents=[common], help="dump raw JSON, to correct field names")
    probe.add_argument("--endpoint", help="only this path, e.g. /openapi/v2/text-to-3d")

    one = sub.add_parser("fetch", parents=[common], help="download one task")
    one.add_argument("task_id")
    one.add_argument("--name", help="piece slug to save as (default: the task's prompt, else its id)")
    one.add_argument("--collection", default="statues")
    one.add_argument("--format", dest="fmt", choices=FORMATS)

    every = sub.add_parser("fetch-all", parents=[common], help="download every finished task")
    every.add_argument("--collection", default="statues")
    every.add_argument("--format", dest="fmt", choices=FORMATS)

    args = p.parse_args()
    key = api_key()

    if args.command == "balance":
        left = balance(key)
        print(f"{left} credit(s)." if left is not None else "The balance endpoint answered in an unexpected shape.")
        return 0

    if args.command == "probe":
        for path in [args.endpoint] if args.endpoint else [BALANCE] + [path for _, path in ENDPOINTS]:
            params = {} if path == BALANCE else {
                "page_num": 1, "page_size": min(args.page_size, 3), "sort_by": "-created_at"}
            print(f"\n--- {path} ---")
            try:
                print(json.dumps(get(path, key, **params), indent=2)[:4000])
            except ApiError as exc:
                print(f"error: {exc}", file=sys.stderr)
        return 0

    if args.command == "fetch":
        task = retrieve(args.task_id, key)
        if not task:
            print(f"error: no task {args.task_id} in this API account.\n\n{no_tasks_note()}", file=sys.stderr)
            return 1
        return 0 if fetch_one(task, args.collection, args.name, args.fmt, args.dry_run) else 1

    tasks = list_tasks(key, args.page_size)
    if not tasks:
        print(no_tasks_note())
        return 0

    if args.command == "list":
        print(f"{'task id':<38} {'status':<18} {'kind':<12} {'created':<11} "
              f"[{'formats':<20}] prompt")
        for task in tasks:
            print(describe(task))
        print(f"\n{len(tasks)} task(s).")
        return 0

    count = sum(fetch_one(t, args.collection, None, args.fmt, args.dry_run) for t in tasks)
    print(f"\n{count} model(s) {'would be ' if args.dry_run else ''}placed in inbox/{args.collection}/.")
    print("Then: scripts/ingest.py --create   (or just push)")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except ApiError as exc:
        raise SystemExit(f"error: {exc}")
    except BrokenPipeError:
        sys.stderr.close()
        raise SystemExit(0)
