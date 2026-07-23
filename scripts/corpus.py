#!/usr/bin/env python3
"""Refresh the committed profile corpus from its source repositories.

Every ``profiles/<slug>.json`` is self-describing: it stamps the target's ``target_url``
and ``target_sha``, and it embeds the full classified answer set (each classified indicator
carries its ``answer``, ``evidence`` quote, and a single uniform ``source``). That makes the
corpus reproducible without a model: the answers a fresh engine run needs are reconstructed
straight from the committed JSON, and the engine validates and rescores them, exactly as it
does for the ``/agentic-atlas:run`` skill. No API key, no model call.

Three commands, layered on one clone-and-rescore core:

    python scripts/corpus.py fetch     [--slug S ...]
    python scripts/corpus.py rescore   [--slug S ...] [--write]
    python scripts/corpus.py refresh   [--slug S ...] [--write]

``fetch`` clones or pulls each source repo into ``.corpus/<slug>`` (a full clone, never
shallow: the Fresh vs Mature axis reads git-history facts that a ``--depth 1`` clone would
silently flatten). ``.corpus`` is git-ignored.

``rescore`` is the deterministic replay: it checks each clone out at the stored ``target_sha``,
reconstructs the classified answers from the committed JSON, and reruns the engine. Because the
tree is the exact one the answers were written against, every quote revalidates. The result
refreshes the ``engine_version`` and ``rubric_version`` stamps (and any score the current
rubric moves for the same evidence) while the evidence itself is unchanged. The one input that
is not pinned by the SHA is ``github_api`` (stars and the like), which the engine fetches live
by design and records verbatim, so a rescore also moves those point-in-time metrics to now.

``refresh`` is the true update: it pulls each clone to its origin's default-branch HEAD and
reruns the engine. Measured indicators move with the newer tree, and any classified quote that
the tool's authors have since reworded no longer validates, so that indicator goes unresolved.
Restoring it faithfully means rereading the repo, which is a model's job, not this script's, so
``refresh`` reports the ``(slug, indicator)`` pairs that went stale for a follow-up
``/agentic-atlas:run <url> --save`` rather than guessing.

Neither command writes anything without ``--write``; a bare run prints the report only. Because
``github_api`` and (for ``refresh``) the moving HEAD make the output time-dependent, these are
maintenance commands, not a CI gate. The CI gate stays ``profiles-check`` (HTML matches JSON).
After ``--write`` rewrites the JSON, run ``make profiles`` to re-render the HTML from it.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
from pathlib import Path

from agentic_atlas.classify import classified_questions
from agentic_atlas.evidence import Target
from agentic_atlas.profiler import profile_target
from agentic_atlas.spec import load_rubric

REPO = Path(__file__).resolve().parent.parent
PROFILES = REPO / "profiles"
CORPUS = REPO / ".corpus"
RUBRIC = REPO / "rubric" / "v1"


def _committed_profiles(slugs: list[str] | None) -> list[Path]:
    files = sorted(PROFILES.glob("*.json"))
    if slugs:
        want = set(slugs)
        files = [f for f in files if f.stem in want]
        missing = want - {f.stem for f in files}
        if missing:
            raise SystemExit(f"no committed profile for: {', '.join(sorted(missing))}")
    if not files:
        raise SystemExit(f"no profiles found in {PROFILES}")
    return files


def _git(*args: str, cwd: Path | None = None) -> str:
    """Run a git command, raising with captured stderr on failure."""
    out = subprocess.run(
        ["git", *args],
        cwd=str(cwd) if cwd else None,
        capture_output=True,
        text=True,
    )
    if out.returncode != 0:
        raise SystemExit(f"git {' '.join(args)} failed: {out.stderr.strip() or out.stdout.strip()}")
    return out.stdout.strip()


def _ensure_clone(url: str, dest: Path) -> None:
    """Clone ``url`` into ``dest`` if absent, else fetch the latest refs. Full clone always,
    so the git-history metrics the Fresh vs Mature axis reads stay honest."""
    if (dest / ".git").is_dir():
        _git("fetch", "--tags", "--prune", "origin", cwd=dest)
        return
    dest.parent.mkdir(parents=True, exist_ok=True)
    _git("clone", url, str(dest))


def _default_ref(dest: Path) -> str:
    """The origin default-branch ref (for example ``origin/main``), for the latest checkout."""
    try:
        head = _git("symbolic-ref", "refs/remotes/origin/HEAD", cwd=dest)
    except SystemExit:
        _git("remote", "set-head", "origin", "--auto", cwd=dest)
        head = _git("symbolic-ref", "refs/remotes/origin/HEAD", cwd=dest)
    return "origin/" + head.rsplit("/", 1)[-1]


def _checkout(dest: Path, ref: str) -> None:
    """Detach the clone at ``ref`` (a SHA or ``origin/<branch>``), discarding any local state."""
    _git("checkout", "--quiet", "--force", "--detach", ref, cwd=dest)


def _reconstruct_answers(profile: dict) -> tuple[dict[str, dict], str]:
    """Rebuild the ``--answers`` payload from a committed profile's resolved classified
    indicators. Returns ``(answers, source)`` in the shape the engine validates: a map from
    indicator id to ``{"answer", "evidence"}``, plus the single source stamped on them."""
    answers: dict[str, dict] = {}
    sources: set[str] = set()
    for axis in profile["axes"]:
        for ind in axis["indicators"]:
            if ind["kind"] != "classified" or not ind.get("resolved"):
                continue
            answers[ind["indicator_id"]] = {"answer": ind["answer"], "evidence": ind["evidence"]}
            if ind.get("source"):
                sources.add(ind["source"])
    if len(sources) > 1:
        # The answers file carries one source stamp; a profile whose classified indicators
        # disagree on provenance cannot round-trip through it without losing that distinction.
        raise SystemExit(f"profile has multiple classified sources, cannot replay: {sources}")
    return answers, (sources.pop() if sources else "corpus-replay")


def _classified_ids(rubric) -> set[str]:
    return {q["id"] for q in classified_questions(rubric)}


def _resolved_by_id(profile: dict) -> dict[str, bool]:
    return {
        ind["indicator_id"]: bool(ind.get("resolved"))
        for axis in profile["axes"]
        for ind in axis["indicators"]
    }


def _axis_scores(profile: dict) -> dict[str, tuple[float | None, float]]:
    return {ax["axis_id"]: (ax.get("score"), ax.get("coverage", 0.0)) for ax in profile["axes"]}


def _rescore_one(path: Path, mode: str, rubric, write: bool) -> dict:
    """Fetch, check out (pinned SHA for ``rescore``, latest HEAD for ``refresh``), replay the
    stored answers, and rescore. Returns a report dict; writes the new JSON only if ``write``."""
    slug = path.stem
    old = json.loads(path.read_text())
    url = old.get("target_url")
    if not url:
        return {"slug": slug, "skipped": "no target_url in profile"}

    dest = CORPUS / slug
    _ensure_clone(url, dest)
    ref = old["target_sha"] if mode == "rescore" else _default_ref(dest)
    if mode == "rescore" and not ref:
        return {"slug": slug, "skipped": "no target_sha to pin"}
    _checkout(dest, ref)

    answers, source = _reconstruct_answers(old)
    target = Target.from_path(dest)
    new_profile = profile_target(rubric, target, answers=answers, answers_source=source)
    new = new_profile.to_dict()
    # Strip the author's absolute checkout path from the stamp, keeping the basename so the
    # rendered display name (report uses the last path segment) is byte-identical.
    new["target"] = os.path.basename(str(old.get("target", slug)).rstrip("/")) or slug

    old_res, new_res = _resolved_by_id(old), _resolved_by_id(new)
    replayed = set(answers)
    went_stale = sorted(i for i in replayed if old_res.get(i) and not new_res.get(i))
    # Classified indicators the current rubric defines that this profile never carried:
    # the rubric grew since it was written, so they need a fresh answer, not a replay.
    new_indicators = sorted(_classified_ids(rubric) - set(old_res))

    old_ax, new_ax = _axis_scores(old), _axis_scores(new)
    axis_deltas = [
        {
            "axis": aid,
            "old_score": old_ax.get(aid, (None, 0.0))[0],
            "new_score": s,
            "old_cov": old_ax.get(aid, (None, 0.0))[1],
            "new_cov": c,
        }
        for aid, (s, c) in new_ax.items()
        if old_ax.get(aid, (None, 0.0)) != (s, c)
    ]

    if write:
        path.write_text(json.dumps(new, indent=2) + "\n")

    return {
        "slug": slug,
        "mode": mode,
        "wrote": write,
        "old": {
            "rubric": old["rubric_version"],
            "engine": old["engine_version"],
            "sha": old.get("target_sha"),
        },
        "new": {
            "rubric": new["rubric_version"],
            "engine": new["engine_version"],
            "sha": new.get("target_sha"),
        },
        "replayed": len(replayed),
        "went_stale": went_stale,
        "new_indicators": new_indicators,
        "axis_deltas": axis_deltas,
    }


def _fmt_sha(sha: str | None) -> str:
    return (sha or "local")[:12]


def _print_report(reports: list[dict], write: bool) -> int:
    stale_total = 0
    for r in reports:
        if r.get("skipped"):
            print(f"  {r['slug']:28} SKIPPED ({r['skipped']})")
            continue
        o, n = r["old"], r["new"]
        bump = []
        if o["engine"] != n["engine"]:
            bump.append(f"engine {o['engine']}->{n['engine']}")
        if o["rubric"] != n["rubric"]:
            bump.append(f"rubric {o['rubric']}->{n['rubric']}")
        if _fmt_sha(o["sha"]) != _fmt_sha(n["sha"]):
            bump.append(f"sha {_fmt_sha(o['sha'])}->{_fmt_sha(n['sha'])}")
        tag = "wrote" if r["wrote"] else "dry-run"
        print(f"  {r['slug']:28} {tag:8} {', '.join(bump) or 'no stamp change'}")
        if r["went_stale"]:
            stale_total += len(r["went_stale"])
            print(
                f"      stale quotes (re-answer via /agentic-atlas:run): {', '.join(r['went_stale'])}"
            )
        if r["new_indicators"]:
            print(f"      rubric added, never answered here: {', '.join(r['new_indicators'])}")
        if r["axis_deltas"]:
            for d in r["axis_deltas"]:
                os_, ns = d["old_score"], d["new_score"]
                print(
                    f"      axis {d['axis']}: score {os_}->{ns}  coverage {d['old_cov']}->{d['new_cov']}"
                )

    print()
    if stale_total:
        print(
            f"{stale_total} classified quote(s) went stale across the corpus. Their axes lost "
            "coverage. Re-run /agentic-atlas:run <url> --save on each affected repo to re-answer."
        )
    if not write:
        print(
            "dry run: nothing written. Re-run with --write, then `make profiles` to re-render HTML."
        )
    else:
        print("wrote profile JSON. Now run `make profiles` to re-render the HTML corpus.")
    return 0


def _cmd_fetch(args: argparse.Namespace) -> int:
    files = _committed_profiles(args.slug)
    for path in files:
        d = json.loads(path.read_text())
        url = d.get("target_url")
        if not url:
            print(f"  {path.stem:28} SKIPPED (no target_url)")
            continue
        dest = CORPUS / path.stem
        existed = (dest / ".git").is_dir()
        _ensure_clone(url, dest)
        print(f"  {path.stem:28} {'fetched' if existed else 'cloned':8} {url}")
    print(f"\ncorpus checkouts under {CORPUS}")
    return 0


def _run_rescore(mode: str, args: argparse.Namespace) -> int:
    rubric = load_rubric(str(RUBRIC), validate=True)
    files = _committed_profiles(args.slug)
    reports = []
    for path in files:
        try:
            reports.append(_rescore_one(path, mode, rubric, args.write))
        except SystemExit as exc:
            # One unreachable SHA or clone failure must not abort the whole corpus.
            reports.append({"slug": path.stem, "skipped": str(exc)})
    return _print_report(reports, args.write)


def _cmd_rescore(args: argparse.Namespace) -> int:
    return _run_rescore("rescore", args)


def _cmd_refresh(args: argparse.Namespace) -> int:
    return _run_rescore("refresh", args)


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="corpus", description=__doc__)
    sub = p.add_subparsers(dest="command", required=True)

    f = sub.add_parser("fetch", help="clone or pull each source repo into .corpus/")
    f.add_argument("--slug", action="append", help="limit to this slug (repeatable)")
    f.set_defaults(func=_cmd_fetch)

    r = sub.add_parser("rescore", help="deterministic replay at each pinned target_sha")
    r.add_argument("--slug", action="append", help="limit to this slug (repeatable)")
    r.add_argument("--write", action="store_true", help="rewrite profile JSON (default: dry run)")
    r.set_defaults(func=_cmd_rescore)

    u = sub.add_parser("refresh", help="pull to latest HEAD, rescore, report stale quotes")
    u.add_argument("--slug", action="append", help="limit to this slug (repeatable)")
    u.add_argument("--write", action="store_true", help="rewrite profile JSON (default: dry run)")
    u.set_defaults(func=_cmd_refresh)

    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
