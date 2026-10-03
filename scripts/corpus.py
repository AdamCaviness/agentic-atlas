#!/usr/bin/env python3
"""Refresh the committed profile corpus from its source repositories.

Every ``profiles/<slug>.json`` is self-describing: it stamps the target's ``target_url``
and ``target_sha``, and it embeds the full judged answer set (each judged indicator
carries its ``answer``, ``evidence`` quote, the ``path`` of the file that quote is in, and a
single uniform ``source``). That makes the
corpus reproducible without a model: the answers a fresh engine run needs are reconstructed
straight from the committed JSON, and the engine validates and rescores them, exactly as it
does for the ``/agentic-atlas:run`` skill. No API key, no model call.

Five commands, layered on one clone-and-rescore core:

    python scripts/corpus.py fetch     [--slug S ...]
    python scripts/corpus.py rescore   [--slug S ...] [--write]
    python scripts/corpus.py refresh   [--slug S ...] [--write]
    python scripts/corpus.py answer    --answers-dir DIR [--slug S ...] [--write]
    python scripts/corpus.py status    [--slug S ...]

``fetch`` clones or pulls each source repo into ``.corpus/<slug>`` (a full clone, never
shallow: the Fresh vs Mature axis reads git-history facts that a ``--depth 1`` clone would
silently flatten). ``.corpus`` is git-ignored.

``rescore`` is the deterministic replay: it checks each clone out at the stored ``target_sha``,
reconstructs the judged answers from the committed JSON, and reruns the engine. Because the
tree is the exact one the answers were written against, every quote revalidates. The result
refreshes the ``engine_version`` and ``rubric_version`` stamps (and any score the current
rubric moves for the same evidence) while the evidence itself is unchanged. The one input that
is not pinned by the SHA is ``github_api`` (stars and the like), which the engine fetches live
by design and records verbatim, so for a rubric that uses it a rescore also moves those
point-in-time metrics to now. The rubric uses no ``github_api`` indicator.
Use ``rescore`` after an engine or rubric bump when you intentionally keep the same pins.

``refresh`` is how the corpus stays current. It pulls each clone to its origin default-branch
HEAD (never onto an older Release tag, which would move pins backwards and drop judged
quotes). Detected indicators move with the newer tree; ``git describe`` at HEAD names the
nearest release so project version stamps track what GitHub shows as current. Any judged
quote the tool's authors have since reworded no longer validates, so that indicator goes
unresolved. Restoring it faithfully means rereading the repo, which is a model's job, not
this script's, so ``refresh`` reports the ``(slug, indicator)`` pairs that went stale, with the
engine's reason, for a re-answer applied with ``answer`` rather than guessing.

``answer`` is how a fresh answer set enters the corpus. It moves each clone to origin
default-branch HEAD, exactly as ``refresh`` does, but takes the judged answers from
``DIR/<slug>.json`` (an answers file in the ``/agentic-atlas:run`` shape, ``{"source",
"answers"}``) instead of the committed JSON. It reports every supplied answer the engine
rejected, with the reason, so a re-answer pass is checked before it is written. Use it after a
rubric MAJOR bump, when every profile is re-answered at HEAD.

``status`` compares each committed pin to origin default-branch HEAD (after a fetch). Exit 1
when any profile is behind, so automation can report drift before the Explorer shows a
stale project version.

A profile answered before rubric 5.0.0 has judged answers with no ``path``. The engine now
requires one, so replaying such a profile would leave every judged indicator unresolved and a
``--write`` would erase its judged positions. ``rescore`` and ``refresh`` therefore skip it with a
reason instead; the fix is to re-answer it and apply the answers with ``answer``.

``rescore``, ``refresh``, and ``answer`` write nothing without ``--write``; a bare run prints
the report only. ``answer --write`` also refuses to write a profile with any rejected answer and
exits 1, so a re-answer pass never commits reduced coverage. Because ``github_api`` (when a rubric uses it) and moving refs (for ``refresh``) make the output
time-dependent, these are maintenance commands, not a CI gate. The CI gate stays
``profiles-check`` (HTML matches JSON). After ``--write`` rewrites the JSON, run
``make profiles`` to re-render the HTML from it.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
from pathlib import Path

from agentic_atlas.cli import load_answers
from agentic_atlas.evidence import (
    Target,
    _fetch_github_latest_release_tag,
    _parse_github_slug,
)
from agentic_atlas.judged import judged_ids
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
        check=False,
    )
    if out.returncode != 0:
        raise SystemExit(f"git {' '.join(args)} failed: {out.stderr.strip() or out.stdout.strip()}")
    return out.stdout.strip()


def _ensure_clone(url: str, dest: Path) -> None:
    """Clone ``url`` into ``dest`` if absent, else fetch the latest refs. Full clone always,
    so the git-history metrics the Fresh vs Mature axis reads stay honest."""
    if (dest / ".git").is_dir():
        # The engine stamps target_url from the clone's origin, so a profile whose source moved
        # (a repository renamed or continued elsewhere) must repoint the existing clone.
        if _git("remote", "get-url", "origin", cwd=dest) != url:
            _git("remote", "set-url", "origin", url, cwd=dest)
            _git("remote", "set-head", "origin", "--auto", cwd=dest)
        _git("fetch", "--tags", "--prune", "origin", cwd=dest)
        return
    dest.parent.mkdir(parents=True, exist_ok=True)
    _git("clone", url, str(dest))
    # A fresh clone already has tags; fetch again so a partial mirror still gets them.
    _git("fetch", "--tags", "--prune", "origin", cwd=dest)


def _default_ref(dest: Path) -> str:
    """The origin default-branch ref (for example ``origin/main``), for the latest checkout."""
    try:
        head = _git("symbolic-ref", "refs/remotes/origin/HEAD", cwd=dest)
    except SystemExit:
        _git("remote", "set-head", "origin", "--auto", cwd=dest)
        head = _git("symbolic-ref", "refs/remotes/origin/HEAD", cwd=dest)
    return "origin/" + head.rsplit("/", 1)[-1]


def _tag_exists(dest: Path, tag: str) -> bool:
    out = subprocess.run(
        ["git", "rev-parse", "--verify", f"refs/tags/{tag}"],
        cwd=str(dest),
        capture_output=True,
        text=True,
        check=False,
    )
    return out.returncode == 0


def _refresh_ref(dest: Path, url: str) -> tuple[str, str]:
    """Choose the checkout ref for ``refresh`` / ``status``.

    Always the origin default-branch tip. That keeps the corpus on current methodology
    and never moves a pin *backwards* onto an older Release tag (which would drop
    judged quotes and understate the project). ``git describe`` at HEAD still
    names the nearest release, so stamps track what GitHub shows as current when the
    tip is at or near that release.

    Returns ``(ref, reason)``. When a newer published Release exists, reason notes it
    for the status/refresh report without changing the checkout.
    """
    head = _default_ref(dest)
    slug = _parse_github_slug(url)
    if slug:
        tag = _fetch_github_latest_release_tag(*slug)
        if tag and _tag_exists(dest, tag):
            return head, f"default-branch (latest release {tag})"
    return head, "default-branch"


def _checkout(dest: Path, ref: str) -> None:
    """Detach the clone at ``ref`` (a SHA, tag, or ``origin/<branch>``), discarding any local state."""
    _git("checkout", "--quiet", "--force", "--detach", ref, cwd=dest)


def _reconstruct_answers(profile: dict) -> tuple[dict[str, dict], str]:
    """Rebuild the ``--answers`` payload from a committed profile's resolved judged
    indicators. Returns ``(answers, source)`` in the shape the engine validates: a map from
    indicator id to ``{"answer", "evidence", "path"}``, plus the single source stamped on them.

    Raises SystemExit (the per-slug skip in ``_run_rescore``) when a resolved judged answer has
    no ``path``: the profile predates rubric 5.0.0 and cannot replay, only be re-answered."""
    answers: dict[str, dict] = {}
    sources: set[str] = set()
    pathless: list[str] = []
    for axis in profile["axes"]:
        for ind in axis["indicators"]:
            if ind["kind"] != "judged" or not ind.get("resolved"):
                continue
            if not ind.get("path"):
                pathless.append(ind["indicator_id"])
            answers[ind["indicator_id"]] = {
                "answer": ind["answer"],
                "evidence": ind["evidence"],
                "path": ind.get("path"),
            }
            if ind.get("source"):
                sources.add(ind["source"])
    if pathless:
        raise SystemExit(
            f"{len(pathless)} judged answer(s) have no evidence path (answered under rubric "
            f"{profile.get('rubric_version')}); replay would drop them. Re-answer with "
            "`scripts/corpus.py answer`"
        )
    if len(sources) > 1:
        # The answers file carries one source stamp; a profile whose judged indicators
        # disagree on provenance cannot round-trip through it without losing that distinction.
        raise SystemExit(f"profile has multiple judged sources, cannot replay: {sources}")
    return answers, (sources.pop() if sources else "corpus-replay")


def _resolved_by_id(profile: dict) -> dict[str, bool]:
    return {
        ind["indicator_id"]: bool(ind.get("resolved"))
        for axis in profile["axes"]
        for ind in axis["indicators"]
    }


def _axis_scores(profile: dict) -> dict[str, tuple[float | None, float]]:
    return {ax["axis_id"]: (ax.get("score"), ax.get("coverage", 0.0)) for ax in profile["axes"]}


def _load_answers_file(path: Path) -> tuple[dict[str, dict], str]:
    """Read an ``/agentic-atlas:run`` answers file, ``{"source", "answers"}``, with the CLI's
    loader. Raises SystemExit (the per-slug skip) when the file is missing, malformed, or has
    no answers."""
    if not path.is_file():
        raise SystemExit(f"no answers file at {path}")
    answers, source = load_answers(str(path))
    if not answers:
        raise SystemExit(f"{path} has no answers")
    return answers, source


def _rescore_one(
    path: Path, mode: str, rubric, write: bool, answers_file: Path | None = None
) -> dict:
    """Fetch, check out (pinned SHA for ``rescore``, origin default-branch HEAD for ``refresh``
    and ``answer``), then profile with the stored answers, or with ``answers_file`` in
    ``answer`` mode. Returns a report dict; writes the new JSON only if ``write``."""
    slug = path.stem
    old = json.loads(path.read_text())
    url = old.get("target_url")
    if not url:
        return {"slug": slug, "skipped": "no target_url in profile"}
    # Before any git work, so a profile that cannot replay is skipped without a fetch.
    if mode == "answer":
        answers, source = _load_answers_file(answers_file)
    else:
        answers, source = _reconstruct_answers(old)

    dest = CORPUS / slug
    _ensure_clone(url, dest)
    if mode == "rescore":
        ref = old.get("target_sha")
        ref_reason = "pinned-sha"
        if not ref:
            return {"slug": slug, "skipped": "no target_sha to pin"}
    else:
        ref, ref_reason = _refresh_ref(dest, url)
    _checkout(dest, ref)

    # The engine rejects unknown answer ids. A replayed id the rubric no longer defines was
    # removed by a rubric change, so drop and report it. A fresh answers file has no such
    # excuse: an unknown id there is a typo or an answer for another rubric, so it is rejected.
    unknown = sorted(set(answers) - judged_ids(rubric))
    for iid in unknown:
        del answers[iid]
    removed_indicators = [] if mode == "answer" else unknown
    target = Target.from_path(dest)
    new_profile = profile_target(rubric, target, answers=answers, answers_source=source)
    new = new_profile.to_dict()
    # Strip the author's absolute checkout path from the stamp, keeping the basename so the
    # rendered display name (report uses the last path segment) is byte-identical.
    new["target"] = os.path.basename(str(old.get("target", slug)).rstrip("/")) or slug

    old_res = _resolved_by_id(old)
    replayed = set(answers)
    # Every supplied answer the engine did not accept, with the reason it gives. In a replay
    # these are the quotes that went stale at the new checkout.
    rejected = {
        ind["indicator_id"]: ind.get("evidence")
        for axis in new["axes"]
        for ind in axis["indicators"]
        if ind["indicator_id"] in replayed and not ind.get("resolved")
    }
    if mode == "answer":
        rejected.update({iid: "not an indicator in this rubric" for iid in unknown})
    # Judged indicators with no answer in this run: in a replay, the ones the rubric added since
    # the profile was written; in answer mode, the ones the answers file left out.
    unanswered = judged_ids(rubric) - (replayed if mode == "answer" else set(old_res))
    new_indicators = sorted(unanswered)

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

    # A fresh answer set with a rejected answer would commit reduced coverage, so answer mode
    # writes only a fully accepted set; fix the answers file and run again.
    wrote = write and not (mode == "answer" and rejected)
    if wrote:
        path.write_text(json.dumps(new, indent=2) + "\n")

    return {
        "slug": slug,
        "mode": mode,
        "wrote": wrote,
        "ref": ref,
        "ref_reason": ref_reason,
        "old": {
            "rubric": old["rubric_version"],
            "engine": old["engine_version"],
            "sha": old.get("target_sha"),
            "version": old.get("target_version"),
        },
        "new": {
            "rubric": new["rubric_version"],
            "engine": new["engine_version"],
            "sha": new.get("target_sha"),
            "version": new.get("target_version"),
        },
        "replayed": len(replayed),
        "rejected": rejected,
        "new_indicators": new_indicators,
        "removed_indicators": removed_indicators,
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
        if (o.get("version") or None) != (n.get("version") or None):
            bump.append(f"version {o.get('version')!r}->{n.get('version')!r}")
        reason = r.get("ref_reason")
        if reason and r.get("mode") in ("refresh", "answer"):
            bump.append(f"via {reason}")
        tag = "wrote" if r["wrote"] else ("refused" if write else "dry-run")
        print(f"  {r['slug']:28} {tag:8} {', '.join(bump) or 'no stamp change'}")
        for iid, why in r["rejected"].items():
            stale_total += 1
            print(f"      rejected {iid}: {why}")
        if r["new_indicators"]:
            print(f"      judged, not answered in this run: {', '.join(r['new_indicators'])}")
        if r["removed_indicators"]:
            print(f"      rubric removed, answer dropped: {', '.join(r['removed_indicators'])}")
        if r["axis_deltas"]:
            for d in r["axis_deltas"]:
                os_, ns = d["old_score"], d["new_score"]
                print(
                    f"      axis {d['axis']}: score {os_}->{ns}  coverage {d['old_cov']}->{d['new_cov']}"
                )

    print()
    answer_mode = any(r.get("mode") == "answer" for r in reports)
    if stale_total and answer_mode:
        print(
            f"{stale_total} supplied answer(s) were rejected, and their profiles were not written. "
            "Fix the answers files and run `answer` again."
        )
    elif stale_total:
        print(
            f"{stale_total} judged quote(s) went stale across the corpus. Their axes lost "
            "coverage. Re-answer each affected tool at HEAD and apply with "
            "`make corpus-answer ANSWERS_DIR=<dir>`."
        )
    if not write:
        print(
            "dry run: nothing written. Re-run with --write, then `make profiles` to re-render HTML."
        )
    else:
        print("wrote profile JSON. Now run `make profiles` to re-render the HTML corpus.")
    # A rejected fresh answer is a failed run, so `make corpus-answer` stops before re-rendering.
    return 1 if stale_total and answer_mode else 0


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
        answers_file = Path(args.answers_dir) / f"{path.stem}.json" if mode == "answer" else None
        try:
            reports.append(_rescore_one(path, mode, rubric, args.write, answers_file))
        except SystemExit as exc:
            # One unreachable SHA or clone failure must not abort the whole corpus.
            reports.append({"slug": path.stem, "skipped": str(exc)})
    return _print_report(reports, args.write)


def _cmd_rescore(args: argparse.Namespace) -> int:
    return _run_rescore("rescore", args)


def _cmd_refresh(args: argparse.Namespace) -> int:
    return _run_rescore("refresh", args)


def _cmd_answer(args: argparse.Namespace) -> int:
    return _run_rescore("answer", args)


def _cmd_status(args: argparse.Namespace) -> int:
    """Exit 0 when every pin matches the current refresh ref; otherwise print drift and exit 1."""
    files = _committed_profiles(args.slug)
    drifted: list[tuple[str, str, str, str, str]] = []
    current: list[tuple[str, str]] = []
    for path in files:
        old = json.loads(path.read_text())
        url = old.get("target_url")
        if not url:
            print(f"  {path.stem:28} SKIPPED (no target_url)")
            continue
        dest = CORPUS / path.stem
        try:
            _ensure_clone(url, dest)
            ref, reason = _refresh_ref(dest, url)
            desired_sha = _git("rev-parse", ref, cwd=dest)
        except SystemExit as exc:
            print(f"  {path.stem:28} SKIPPED ({exc})")
            continue
        pinned = old.get("target_sha") or ""
        if pinned != desired_sha:
            drifted.append((path.stem, _fmt_sha(pinned), _fmt_sha(desired_sha), ref, reason))
        else:
            current.append((path.stem, reason))

    for slug, reason in current:
        print(f"  {slug:28} current  via {reason}")
    for slug, pin, want, ref, reason in drifted:
        print(f"  {slug:28} DRIFT    pin {pin} -> {want} ({ref}, via {reason})")

    print()
    if drifted:
        print(
            f"{len(drifted)} profile(s) behind origin default-branch HEAD. "
            "Re-answer them at HEAD and apply with `make corpus-answer ANSWERS_DIR=<dir>`."
        )
        return 1
    print(f"all {len(current)} profile(s) match origin default-branch HEAD.")
    return 0


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

    u = sub.add_parser(
        "refresh",
        help="move pins to origin default-branch HEAD, rescore, report stale quotes",
    )
    u.add_argument("--slug", action="append", help="limit to this slug (repeatable)")
    u.add_argument("--write", action="store_true", help="rewrite profile JSON (default: dry run)")
    u.set_defaults(func=_cmd_refresh)

    a = sub.add_parser(
        "answer",
        help="move pins to origin default-branch HEAD and profile with supplied answers files",
    )
    a.add_argument(
        "--answers-dir", required=True, help="directory holding one <slug>.json answers file"
    )
    a.add_argument("--slug", action="append", help="limit to this slug (repeatable)")
    a.add_argument("--write", action="store_true", help="rewrite profile JSON (default: dry run)")
    a.set_defaults(func=_cmd_answer)

    s = sub.add_parser(
        "status",
        help="exit 1 if any committed pin is behind the current refresh ref",
    )
    s.add_argument("--slug", action="append", help="limit to this slug (repeatable)")
    s.set_defaults(func=_cmd_status)

    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
