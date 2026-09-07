#!/usr/bin/env python3
"""Offline tests for scripts/meshy.py — its parsing, not the network.

The task objects here are written by hand from Meshy's documented response
fields, checked against the live API on 2026-09-07. They are a record of the
shape the client expects: if Meshy changes it, `scripts/meshy.py probe` shows
the new shape and these fixtures are what get corrected.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import meshy  # noqa: E402

# A finished image-to-3d task. Image tasks carry no name and no prompt.
IMAGE_TASK = {
    "id": "018a210d-8ba4-705c-b111-1b4a0c1c1f7f",
    "type": "image-to-3d",
    "status": "SUCCEEDED",
    "progress": 100,
    "created_at": 1788739200000,  # 2026-09-07T00:00:00Z, in milliseconds
    "model_urls": {
        "glb": "https://assets.meshy.ai/x/model.glb?token=1",
        "stl": "https://assets.meshy.ai/x/model.stl?token=1",
        "obj": "",  # offered but empty — must not be chosen
    },
    "thumbnail_url": "https://assets.meshy.ai/x/preview.png",
    "_kind": "image-to-3d",
}

# A running text-to-3d task: no model to download yet.
TEXT_TASK = {
    "id": "018a210d-8ba4-705c-b111-2c5b1d2d2a80",
    "type": "text-to-3d-preview",
    "status": "IN_PROGRESS",
    "progress": 42,
    "prompt": "Sacred Heart of Jesus statue",
    "created_at": 1788739200000,
    "model_urls": {},
    "_kind": "text-to-3d",
}

FAILURES: list[str] = []


def check(label: str, got, want) -> None:
    if got != want:
        FAILURES.append(f"{label}: got {got!r}, want {want!r}")


def main() -> int:
    # A bare list is what both listings return; an envelope is tolerated.
    check("page_of bare list", meshy.page_of([IMAGE_TASK]), [IMAGE_TASK])
    check("page_of result envelope", meshy.page_of({"result": [IMAGE_TASK]}), [IMAGE_TASK])
    check("page_of data envelope", meshy.page_of({"data": [IMAGE_TASK]}), [IMAGE_TASK])
    check("page_of empty account", meshy.page_of([]), [])
    check("page_of error body", meshy.page_of({"message": "NoMatchingRoute"}), [])

    # Empty URLs are dropped, so a format is never picked that cannot be fetched.
    check("model_urls drops empties", sorted(meshy.model_urls(IMAGE_TASK)), ["glb", "stl"])
    check("model_urls of unfinished", meshy.model_urls(TEXT_TASK), {})

    # STL wins by default: this repository prints its models.
    check("pick_format default", meshy.pick_format(meshy.model_urls(IMAGE_TASK), None)[0], "stl")
    check("pick_format explicit", meshy.pick_format(meshy.model_urls(IMAGE_TASK), "glb")[0], "glb")
    check("pick_format unavailable", meshy.pick_format(meshy.model_urls(IMAGE_TASK), "obj"), None)
    check("pick_format nothing", meshy.pick_format({}, None), None)

    # Naming: a text task has its prompt, an image task has only its id.
    check("label of text task", meshy.label_of(TEXT_TASK), "Sacred Heart of Jesus statue")
    check("label of image task", meshy.label_of(IMAGE_TASK), "")

    # created_at is milliseconds since the epoch, not seconds.
    check("created_at in ms", meshy.when(IMAGE_TASK), "2026-09-07")
    check("created_at missing", meshy.when({"id": "x"}), "?")

    # Only SUCCEEDED is downloadable; progress shows on anything in flight.
    check("describe shows progress", "IN_PROGRESS 42%" in meshy.describe(TEXT_TASK), True)
    check("describe lists formats", "[stl,glb" in meshy.describe(IMAGE_TASK), True)
    check("describe of unfinished", "[none" in meshy.describe(TEXT_TASK), True)

    check("downloadable status", meshy.DOWNLOADABLE, "SUCCEEDED")
    check("page size cap", meshy.PAGE_MAX, 50)

    for failure in FAILURES:
        print(f"  {failure}", file=sys.stderr)
    if FAILURES:
        print(f"{len(FAILURES)} meshy check(s) failed.", file=sys.stderr)
        return 1
    print("meshy.py parsing: all checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
