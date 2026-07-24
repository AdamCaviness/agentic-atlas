#!/usr/bin/env python3
"""Build the Explorer site and syntax-check its embedded JavaScript.

`scripts/build_site.py` runs only at deploy time (see `.github/workflows/static.yml`), so a
break in it, a Python error, or a syntax error in the large embedded JS string, would slip
past `make check`/CI and surface only after merge, at the deploy step. This gate runs the
build (the same entry point the deploy runs, catching any Python error) and, when Node is
available, runs `node --check` on the embedded script (catching JS syntax errors). Node is
present on CI runners; locally it is skipped with a note so the check never blocks a
contributor who has no Node installed.
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
BUILD_SITE = os.path.join(HERE, "build_site.py")


def _embedded_js() -> str:
    with open(BUILD_SITE) as fh:
        src = fh.read()
    m = re.search(r'JS = r"""(.*?)"""', src, re.DOTALL)
    if not m:
        raise SystemExit("check_site: could not locate the embedded JS block in build_site.py")
    return m.group(1)


def main() -> int:
    build = subprocess.run([sys.executable, BUILD_SITE], check=False)
    if build.returncode:
        return build.returncode
    node = shutil.which("node")
    if not node:
        print("check_site: node not found, skipping Explorer JS syntax check")
        return 0
    with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False) as fh:
        fh.write(_embedded_js())
        path = fh.name
    try:
        checked = subprocess.run([node, "--check", path], check=False)
    finally:
        os.unlink(path)
    if checked.returncode:
        print("check_site: embedded Explorer JS failed `node --check`", file=sys.stderr)
        return checked.returncode
    print("ok: Explorer site builds and its JavaScript parses")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
