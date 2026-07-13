"""Command line interface for the Atlas engine.

    atlas validate <rubric.yaml>
    atlas profile <target> [--rubric FILE] [--judge none|manual] [--answers FILE]
                           [--format text|md|json]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import yaml

from .evidence import Target
from .judge import ManualJudge, NoneJudge
from .profiler import profile_target
from .report import render_markdown, render_text
from .spec import load_rubric

_DEFAULT_RUBRIC = Path(__file__).resolve().parent.parent / "rubric" / "v1.0.0.yaml"


def _cmd_validate(args: argparse.Namespace) -> int:
    load_rubric(args.rubric, validate=True)
    print(f"ok: {args.rubric} is a valid rubric")
    return 0


def _build_judge(args: argparse.Namespace):
    if args.judge == "none":
        return NoneJudge()
    if args.judge == "manual":
        if not args.answers:
            print("error: --judge manual requires --answers FILE", file=sys.stderr)
            raise SystemExit(2)
        data = yaml.safe_load(Path(args.answers).read_text()) or {}
        return ManualJudge(data.get("answers", data))
    # "anthropic" is available but kept out of the default CLI path so a plain run
    # never makes network calls. Import it explicitly when wiring the skill.
    raise SystemExit(f"unsupported judge: {args.judge}")


def _cmd_profile(args: argparse.Namespace) -> int:
    rubric = load_rubric(args.rubric, validate=True)
    target = Target.from_path(args.target)
    profile = profile_target(rubric, target, _build_judge(args))

    if args.format == "json":
        print(json.dumps(profile.to_dict(), indent=2))
    elif args.format == "md":
        print(render_markdown(profile))
    else:
        print(render_text(profile))
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="atlas", description=__doc__)
    sub = p.add_subparsers(dest="command", required=True)

    v = sub.add_parser("validate", help="validate a rubric file against the schema")
    v.add_argument("rubric", nargs="?", default=str(_DEFAULT_RUBRIC))
    v.set_defaults(func=_cmd_validate)

    pr = sub.add_parser("profile", help="profile a target directory")
    pr.add_argument("target", help="path to the target workflow/framework directory")
    pr.add_argument("--rubric", default=str(_DEFAULT_RUBRIC))
    pr.add_argument("--judge", choices=["none", "manual"], default="none")
    pr.add_argument("--answers", help="YAML file of prepared answers for manual judging")
    pr.add_argument("--format", choices=["text", "md", "json"], default="text")
    pr.set_defaults(func=_cmd_profile)

    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
