#!/usr/bin/env python3
"""Build the Explorer site and syntax-check its embedded JavaScript.

`scripts/build_site.py` runs only at deploy time (see `.github/workflows/static.yml`), so a
break in it, a Python error, or a syntax error in the large embedded JS string, would slip
past `make check`/CI and surface only after merge, at the deploy step. This gate builds the
site (catching any Python error) and, when Node is available, runs `node --check` on the
embedded script (catching JS syntax errors). Node is present on CI runners; locally it is
skipped with a note so the check never blocks a contributor who has no Node installed.
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import build_site  # noqa: E402  sibling script, reachable via the path insert above


def _embedded_js() -> str:
    with open(os.path.join(HERE, "build_site.py")) as fh:
        src = fh.read()
    m = re.search(r'JS = r"""(.*?)"""', src, re.S)
    if not m:
        raise SystemExit("check_site: could not locate the embedded JS block in build_site.py")
    return m.group(1)


def main() -> int:
    rc = build_site.build()
    if rc:
        return rc
    node = shutil.which("node")
    if not node:
        print("check_site: node not found, skipping Explorer JS syntax check")
        return 0
    with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False) as fh:
        fh.write(_embedded_js())
        path = fh.name
    try:
        result = subprocess.run([node, "--check", path])  # noqa: S603 controlled inputs
    finally:
        os.unlink(path)
    if result.returncode:
        print("check_site: embedded Explorer JS failed `node --check`", file=sys.stderr)
        return result.returncode
    print("ok: Explorer site builds and its JavaScript parses")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
