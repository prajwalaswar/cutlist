"""Command line interface for cutlist."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import __version__
from .assets import collect_requests, resolve
from .captions import build_cues, to_srt
from .checks import Diagnostic, has_errors, run_checks
from .config import Settings, settings_from_script
from .parser import ScriptError, parse_file
from .report import (
    as_json,
    asset_table,
    build_package_report,
    diagnostic_lines,
    plan_table,
    write_text,
)
from .timing import TimingPlan, build_plan

EXAMPLE_SCRIPT = """---
title: My first package
target_duration: 16
words_per_minute: 150
banned_phrases: cheap, guaranteed
---

# Hook
Your hook goes here. Two short sentences beat one long one.

# Point one
Say the thing, then show the thing [[asset: broll/example.mp4]].

Keep one idea per beat so the timing stays honest.

# Close
One line that sends them to the next video.
"""


def _load(path: str, wpm: int | None) -> tuple[object, Settings]:
    script = parse_file(path)
    settings = settings_from_script(script)
    if wpm is not None:
        settings = settings.with_overrides(words_per_minute=wpm)
    return script, settings


def _pipeline(path: str, args: argparse.Namespace) -> dict:
    script, settings = _load(path, getattr(args, "wpm", None))
    plan: TimingPlan = build_plan(script, settings.words_per_minute)
    cues = build_cues(
        plan,
        max_chars=getattr(args, "max_chars", None) or settings.max_chars_per_line,
        max_lines=getattr(args, "max_lines", None) or settings.max_lines,
    )
    statuses = None
    if getattr(args, "assets", None):
        requests = collect_requests(script, plan)
        statuses = resolve(requests, args.assets)
    diagnostics: list[Diagnostic] = run_checks(script, plan, cues, settings, statuses)
    return {
        "script": script,
        "settings": settings,
        "plan": plan,
        "cues": cues,
        "diagnostics": diagnostics,
        "assets": statuses or [],
    }


def cmd_plan(args: argparse.Namespace) -> int:
    state = _pipeline(args.script, args)
    plan: TimingPlan = state["plan"]
    if args.json:
        print(
            as_json(
                {
                    "title": state["script"].title,
                    "total_duration": plan.total_duration,
                    "words": plan.words,
                    "words_per_minute": plan.words_per_minute,
                    "sections": plan.sections,
                    "beats": plan.beats,
                }
            )
        )
        return 0
    print(f"{state['script'].title}: {plan.total_duration:.1f}s, {plan.words} words")
    print()
    print(plan_table(plan))
    return 0


def cmd_captions(args: argparse.Namespace) -> int:
    state = _pipeline(args.script, args)
    document = to_srt(state["cues"])
    if args.output:
        write_text(args.output, document)
        print(f"wrote {len(state['cues'])} cues to {args.output}")
    else:
        sys.stdout.write(document)
    return 0


def cmd_check(args: argparse.Namespace) -> int:
    state = _pipeline(args.script, args)
    diagnostics: list[Diagnostic] = state["diagnostics"]
    if args.json:
        print(
            as_json(
                {
                    "title": state["script"].title,
                    "total_duration": state["plan"].total_duration,
                    "assets": state["assets"],
                    "diagnostics": diagnostics,
                }
            )
        )
    else:
        print(plan_table(state["plan"]))
        print()
        print(asset_table(state["assets"]))
        print()
        print(diagnostic_lines(diagnostics))
    if has_errors(diagnostics):
        return 1
    if args.strict and diagnostics:
        return 1
    return 0


def cmd_package(args: argparse.Namespace) -> int:
    state = _pipeline(args.script, args)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    report = build_package_report(
        state["script"], state["plan"], state["cues"], state["diagnostics"], state["assets"]
    )
    write_text(out / "report.md", report)
    write_text(out / "captions.srt", to_srt(state["cues"]))
    write_text(
        out / "timing.json",
        as_json(
            {
                "title": state["script"].title,
                "total_duration": state["plan"].total_duration,
                "sections": state["plan"].sections,
                "beats": state["plan"].beats,
            }
        ),
    )
    write_text(
        out / "assets.json",
        as_json({"assets": state["assets"]}),
    )
    errors = sum(1 for item in state["diagnostics"] if item.severity == "error")
    warnings = sum(1 for item in state["diagnostics"] if item.severity == "warning")
    print(f"package written to {out}/")
    print(f"  report.md, captions.srt, timing.json, assets.json")
    print(f"  {errors} errors, {warnings} warnings")
    return 1 if errors else 0


def cmd_init(args: argparse.Namespace) -> int:
    target = Path(args.target)
    script_path = target / "script.md"
    if script_path.exists() and not args.force:
        print(f"{script_path} already exists, use --force to overwrite", file=sys.stderr)
        return 1
    write_text(script_path, EXAMPLE_SCRIPT)
    (target / "assets" / "broll").mkdir(parents=True, exist_ok=True)
    print(f"created {script_path}")
    print(f"next: cutlist check {script_path}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="cutlist",
        description="Turn a narration script into a production package: timing, captions, assets, checks.",
    )
    parser.add_argument("--version", action="version", version=f"cutlist {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    def common(p: argparse.ArgumentParser) -> None:
        p.add_argument("script", help="markdown script file")
        p.add_argument("--wpm", type=int, default=None, help="override speaking rate")
        p.add_argument("--assets", default=None, help="media folder to resolve cues against")

    plan = sub.add_parser("plan", help="print the timing plan")
    common(plan)
    plan.add_argument("--json", action="store_true")
    plan.set_defaults(func=cmd_plan)

    captions = sub.add_parser("captions", help="print or write SRT captions")
    common(captions)
    captions.add_argument("-o", "--output", default=None, help="write SRT here instead of stdout")
    captions.add_argument("--max-chars", type=int, default=None, help="characters per caption line")
    captions.add_argument("--max-lines", type=int, default=None, help="lines per caption cue")
    captions.set_defaults(func=cmd_captions)

    check = sub.add_parser("check", help="run all constraint checks")
    common(check)
    check.add_argument("--json", action="store_true")
    check.add_argument("--strict", action="store_true", help="fail on warnings too")
    check.set_defaults(func=cmd_check)

    package = sub.add_parser("package", help="write report.md, captions.srt, timing.json, assets.json")
    common(package)
    package.add_argument("-o", "--out", required=True, help="output directory")
    package.set_defaults(func=cmd_package)

    init = sub.add_parser("init", help="scaffold a starter script and asset folder")
    init.add_argument("target", nargs="?", default=".", help="directory to scaffold into")
    init.add_argument("--force", action="store_true", help="overwrite an existing script.md")
    init.set_defaults(func=cmd_init, script=None)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return int(args.func(args))
    except ScriptError as exc:
        print(f"cutlist: {exc}", file=sys.stderr)
        return 2
    except ValueError as exc:
        print(f"cutlist: {exc}", file=sys.stderr)
        return 2
