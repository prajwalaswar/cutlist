"""Human and machine readable reports."""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from .assets import AssetStatus
from .captions import Cue
from .checks import Diagnostic
from .model import Script
from .timing import TimingPlan


def _clock(seconds: float) -> str:
    total = int(seconds)
    minutes, secs = divmod(total, 60)
    return f"{minutes:02d}:{secs:02d}"


def plan_table(plan: TimingPlan) -> str:
    """Markdown timing table, one row per section then per beat."""
    rows = ["| Start | End | Dur | Words | Section |", "|---|---|---|---|---|"]
    for section in plan.sections:
        rows.append(
            f"| {_clock(section.start)} | {_clock(section.end)} | {section.duration:.1f}s "
            f"| {section.words} | **{section.title}** |"
        )
        section_beats = [beat for beat in plan.beats if beat.section_index == section.index]
        for beat in section_beats:
            preview = (beat.text[:54] + "...") if len(beat.text) > 57 else beat.text
            rows.append(
                f"| {_clock(beat.start)} | {_clock(beat.end)} | {beat.duration:.1f}s "
                f"| {beat.words} | {preview} |"
            )
    return "\n".join(rows)


def asset_table(statuses: list[AssetStatus]) -> str:
    if not statuses:
        return "_No media cues in this script._"
    rows = ["| Time | Asset | Section | Status |", "|---|---|---|---|"]
    for status in statuses:
        state = f"ok: {status.path}" if status.found else "MISSING"
        rows.append(
            f"| {_clock(status.request.start)} | `{status.request.name}` "
            f"| {status.request.section_title} | {state} |"
        )
    return "\n".join(rows)


def diagnostic_lines(diagnostics: list[Diagnostic]) -> str:
    if not diagnostics:
        return "No issues found."
    return "\n".join(f"- {item.as_line()}" for item in diagnostics)


def build_package_report(
    script: Script,
    plan: TimingPlan,
    cues: list[Cue],
    diagnostics: list[Diagnostic],
    asset_statuses: list[AssetStatus],
) -> str:
    """The markdown report written by `cutlist package`."""
    parts = [
        f"# Production package: {script.title}",
        "",
        f"- Total runtime: **{plan.total_duration:.1f}s** "
        f"({_clock(plan.total_duration)})",
        f"- Words: **{plan.words}** at **{plan.words_per_minute} wpm**",
        f"- Sections: **{len(plan.sections)}**, beats: **{len(plan.beats)}**",
        f"- Caption cues: **{len(cues)}**",
        "",
        "## Timing plan",
        "",
        plan_table(plan),
        "",
        "## Media cues",
        "",
        asset_table(asset_statuses),
        "",
        "## Checks",
        "",
        diagnostic_lines(diagnostics),
        "",
    ]
    return "\n".join(parts)


def as_json(payload: dict) -> str:
    """Stable JSON for piping into other tooling."""

    def default(value: object) -> object:
        if hasattr(value, "__dataclass_fields__"):
            return asdict(value)  # type: ignore[arg-type]
        raise TypeError(f"cannot serialise {type(value)!r}")

    return json.dumps(payload, indent=2, default=default, sort_keys=True)


def write_text(path: str | Path, content: str) -> Path:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")
    return target
