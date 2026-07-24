#!/usr/bin/env python3
"""Guard the committed profile corpus against drift.

Each ``profiles/<slug>.html`` must be exactly ``render_html(Profile.from_dict(<slug>.json))``.
The site deploy (``scripts/build_site.py``) copies those HTML files in verbatim, so a stale
one ships silently. This check, wired into ``make check`` as ``profiles-check``, fails when any
committed HTML no longer matches what the engine renders from its JSON, the same drift
discipline as ``agentic-atlas docs --check`` applies to the generated axis READMEs.

    python3 scripts/check_corpus.py            # report drift, exit 1 if any (CI mode)
    python3 scripts/check_corpus.py --write     # regenerate the HTML from JSON in place

Rendering is a pure, version-stable function of the JSON, so a mismatch means the committed
HTML is stale (the fix is ``make profiles``), not that the machine differs.
"""

from __future__ import annotations

import glob
import json
import os
import sys

from agentic_atlas.models import Profile
from agentic_atlas.report import render_html

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROFILES = os.path.join(REPO, "profiles")


def main(argv: list[str]) -> int:
    write = "--write" in argv
    files = sorted(glob.glob(os.path.join(PROFILES, "*.json")))
    if not files:
        print("no profiles found in", PROFILES)
        return 1

    drifted = []
    for f in files:
        slug = os.path.splitext(os.path.basename(f))[0]
        html_path = os.path.join(PROFILES, slug + ".html")
        with open(f) as fh:
            want = render_html(Profile.from_dict(json.load(fh)))
        have = None
        if os.path.exists(html_path):
            with open(html_path) as fh:
                have = fh.read()
        if want == have:
            continue
        if write:
            with open(html_path, "w") as fh:
                fh.write(want)
            print("regenerated", slug + ".html")
        else:
            drifted.append(slug)

    if write:
        return 0
    if drifted:
        print("stale profile HTML (run `make profiles`): " + ", ".join(drifted))
        return 1
    print(f"ok: all {len(files)} profile HTML files match their JSON")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
