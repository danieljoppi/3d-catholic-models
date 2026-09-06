#!/usr/bin/env python3
"""Refuse to let a credential into the repository.

Cheap, specific patterns only — this is a tripwire, not a scanner. It exists
because an API key was once pasted into a conversation about this project, and
the cost of one slipping into a commit is far higher than the cost of this file.
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

PATTERNS = {
    "Meshy API key": re.compile(r"\bmsy_[A-Za-z0-9]{20,}"),
    "OpenAI key": re.compile(r"\bsk-[A-Za-z0-9]{20,}"),
    "GitHub token": re.compile(r"\bgh[pousr]_[A-Za-z0-9]{30,}"),
    "AWS access key": re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    "Hugging Face token": re.compile(r"\bhf_[A-Za-z0-9]{30,}"),
    "Generic bearer secret": re.compile(r"(?i)\b(api[_-]?key|secret|token)\s*[:=]\s*['\"][A-Za-z0-9_\-]{24,}['\"]"),
}

# This file necessarily contains the patterns it looks for.
SKIP = {Path("tests/check_no_secrets.py")}


def tracked_files() -> list[Path]:
    out = subprocess.run(["git", "ls-files"], cwd=ROOT, capture_output=True, text=True, check=True)
    return [Path(line) for line in out.stdout.splitlines() if line]


def main() -> int:
    findings: list[str] = []
    checked = 0
    for rel in tracked_files():
        if rel in SKIP:
            continue
        path = ROOT / rel
        if not path.is_file() or path.stat().st_size > 2_000_000:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue  # binary
        checked += 1
        for label, pattern in PATTERNS.items():
            for match in pattern.finditer(text):
                line = text[: match.start()].count("\n") + 1
                findings.append(f"{rel}:{line}: possible {label}")

    if findings:
        print("Possible credentials in tracked files:", file=sys.stderr)
        for f in findings:
            print(f"  {f}", file=sys.stderr)
        print("\nRemove it, rotate the credential, and use an environment "
              "variable or repository secret instead.", file=sys.stderr)
        return 1

    print(f"No credential patterns in {checked} tracked text file(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
