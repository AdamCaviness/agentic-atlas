"""Command line interface for the Agentic Atlas engine.

    agentic-atlas validate <rubric>
    agentic-atlas profile <target> [--rubric DIR] [--answers FILE] [--format text|md|json|html]
    agentic-atlas questions <target> [--rubric DIR]
    agentic-atlas render <profile.json> [--format text|md|json|html]

The engine is deterministic and needs no API key. A bare ``profile`` run resolves the
detected indicators only. The judged indicators are unlocked by supplying answers
(``--answers``) produced outside the engine, the intended producer being the
agentic-toolkit skill, whose host agent reads the repo and answers each question from
``questions``. The engine validates those answers, it never calls a model.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from . import docs
from .evidence import Target
from .judged import ANSWER_INSTRUCTIONS, judged_questions
from .models import Profile
from .profiler import profile_target
from .report import render_html, render_markdown, render_text
from .spec import load_rubric

_DEFAULT_RUBRIC = Path(__file__).resolve().parent.parent / "rubric" / "v1"


def _cmd_validate(args: argparse.Namespace) -> int:
    load_rubric(args.rubric, validate=True)
    print(f"ok: {args.rubric} is a valid rubric")
    return 0


def _cmd_docs(args: argparse.Namespace) -> int:
    changed = docs.sync(args.rubric, check=args.check)
    if args.check:
        if changed:
            print("stale axis READMEs (run `make docs`): " + ", ".join(changed))
            return 1
        print("ok: all axis READMEs are in sync")
        return 0
    print(f"updated: {', '.join(changed) if changed else 'none'}")
    return 0


def _cmd_questions(args: argparse.Namespace) -> int:
    rubric = load_rubric(args.rubric, validate=True)
    target = Target.from_path(args.target)
    print(
        json.dumps(
            {
                "rubric_version": rubric.rubric_version,
                "target": str(target.root),
                "instructions": ANSWER_INSTRUCTIONS,
                "questions": judged_questions(rubric),
            },
            indent=2,
        )
    )
    return 0


def _load_answers(path: str) -> tuple[dict, str]:
    """Read a supplied-answers file (or stdin, via '-'), returning (answers, source)."""
    try:
        # "-" reads stdin, so the skill can pipe answers straight in without a temp file.
        raw = sys.stdin.read() if path == "-" else Path(path).read_text()
        data = json.loads(raw)
    except (OSError, ValueError) as exc:
        raise SystemExit(f"cannot read answers file {path!r}: {exc}")
    answers = data.get("answers")
    if not isinstance(answers, dict):
        raise SystemExit(f"answers file {path!r} must have an object under key 'answers'")
    return answers, str(data.get("source") or "supplied")


def _emit(profile: Profile, fmt: str) -> None:
    """Print a profile in the requested format. Shared by `profile` and `render` so the two
    commands stay byte-for-byte consistent."""
    if fmt == "json":
        print(json.dumps(profile.to_dict(), indent=2))
    elif fmt == "md":
        print(render_markdown(profile))
    elif fmt == "html":
        print(render_html(profile))
    else:
        # Color only for an interactive terminal, and never when NO_COLOR is set
        # (https://no-color.org). Piped or redirected output stays plain ASCII.
        color = sys.stdout.isatty() and not os.environ.get("NO_COLOR")
        print(render_text(profile, color=color))


def _cmd_profile(args: argparse.Namespace) -> int:
    rubric = load_rubric(args.rubric, validate=True)
    target = Target.from_path(args.target)
    answers, source = _load_answers(args.answers) if args.answers else (None, "supplied")
    try:
        profile = profile_target(rubric, target, answers=answers, answers_source=source)
    except ValueError as exc:
        raise SystemExit(str(exc))
    _emit(profile, args.format)
    return 0


def _cmd_render(args: argparse.Namespace) -> int:
    """Re-render a saved profile JSON (from `profile --format json`) without re-running the
    engine or having the target on hand. Deterministic: byte-identical to the original render
    for the same JSON, which is what makes the committed corpus checkable for drift."""
    try:
        raw = sys.stdin.read() if args.profile == "-" else Path(args.profile).read_text()
        data = json.loads(raw)
    except (OSError, ValueError) as exc:
        raise SystemExit(f"cannot read profile file {args.profile!r}: {exc}")
    try:
        profile = Profile.from_dict(data)
    except (ValueError, KeyError, TypeError) as exc:
        # A profile saved under an older rubric MAJOR can use retired field values (for
        # example the pre-4.0 kinds "measured"/"classified"). It is not comparable to the
        # current rubric anyway, so say so instead of guessing a translation.
        raise SystemExit(
            f"cannot load profile {args.profile!r} (rubric {data.get('rubric_version')!r}): "
            f"{exc}. Re-run `agentic-atlas profile` to regenerate it under the current rubric."
        )
    _emit(profile, args.format)
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="agentic-atlas", description=__doc__)
    sub = p.add_subparsers(dest="command", required=True)

    v = sub.add_parser("validate", help="validate a rubric against the schema")
    v.add_argument("rubric", nargs="?", default=str(_DEFAULT_RUBRIC))
    v.set_defaults(func=_cmd_validate)

    d = sub.add_parser("docs", help="regenerate axis README scoring blocks from axis.yaml")
    d.add_argument("rubric", nargs="?", default=str(_DEFAULT_RUBRIC))
    d.add_argument("--check", action="store_true", help="report drift instead of writing")
    d.set_defaults(func=_cmd_docs)

    pr = sub.add_parser("profile", help="profile a target directory")
    pr.add_argument("target", help="path to the target methodology/framework directory")
    pr.add_argument("--rubric", default=str(_DEFAULT_RUBRIC))
    pr.add_argument(
        "--answers",
        help="JSON file of judged answers (from the agentic-toolkit skill) to "
        "validate and score, or '-' to read them from stdin; without it the profile "
        "is detected-only",
    )
    pr.add_argument("--format", choices=["text", "md", "json", "html"], default="text")
    pr.set_defaults(func=_cmd_profile)

    q = sub.add_parser("questions", help="emit the judged questions to answer for a target (JSON)")
    q.add_argument("target", help="path to the target methodology/framework directory")
    q.add_argument("--rubric", default=str(_DEFAULT_RUBRIC))
    q.set_defaults(func=_cmd_questions)

    rn = sub.add_parser(
        "render", help="re-render a saved profile JSON without re-running the engine"
    )
    rn.add_argument(
        "profile", help="path to a profile JSON (from `profile --format json`), or '-' for stdin"
    )
    rn.add_argument("--format", choices=["text", "md", "json", "html"], default="html")
    rn.set_defaults(func=_cmd_render)

    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
