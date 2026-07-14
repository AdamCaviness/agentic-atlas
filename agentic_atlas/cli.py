"""Command line interface for the Agentic Atlas engine.

    agentic-atlas validate <rubric.yaml>
    agentic-atlas profile <target> [--rubric FILE] [--judge none|manual] [--answers FILE]
                                   [--format text|md|json]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import yaml

from . import docs
from .evidence import Target
from .judge import ManualJudge, NoneJudge
from .profiler import profile_target
from .report import render_markdown, render_text
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
    pr.add_argument("target", help="path to the target approach/framework directory")
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
