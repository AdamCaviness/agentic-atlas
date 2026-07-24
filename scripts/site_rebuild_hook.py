#!/usr/bin/env python3
"""PostToolUse hook: rebuild the Explorer when ``scripts/build_site.py`` is edited.

The built site under ``dist/`` is a snapshot, so an edit to ``build_site.py`` is invisible
until the site is rebuilt. Wired as a Claude Code ``PostToolUse`` hook (see
``.claude/settings.json``), this reads the tool payload from stdin, and when the edited file
is ``scripts/build_site.py`` it rebuilds the site and prints the path to ``dist/index.html``
for a visual check. Any other edit is a no-op. Pure standard library, matching build_site.py.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        return 0
    path = (payload.get("tool_input") or {}).get("file_path") or ""
    if not path.replace("\\", "/").endswith("scripts/build_site.py"):
        return 0
    root = os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()
    build = subprocess.run(
        [sys.executable, os.path.join("scripts", "build_site.py")], cwd=root, check=False
    )
    if build.returncode:
        print(
            f"Explorer rebuild failed (exit {build.returncode}) after editing build_site.py",
            file=sys.stderr,
        )
        return build.returncode
    print(f"Explorer rebuilt. Open for a visual check: {os.path.join(root, 'dist', 'index.html')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
