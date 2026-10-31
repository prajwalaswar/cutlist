"""Constraint checks that turn a plan into actionable diagnostics."""

from __future__ import annotations

from dataclasses import dataclass

from .assets import AssetStatus
from .captions import Cue
from .config import Settings
from .model import Script
from .timing import TimingPlan

ERROR = "error"
WARNING = "warning"
INFO = "info"
SEVERITY_ORDER = {ERROR: 0, WARNING: 1, INFO: 2}


@dataclass(frozen=True)
class Diagnostic:
    code: str
    severity: str
    message: str
    where: str = ""

    def as_line(self) -> str:
        prefix = f"[{self.severity}] {self.code}"
        location = f" ({self.where})" if self.where else ""
        return f"{prefix}{location}: {self.message}"


def _fmt(seconds: float) -> str:
    return f"{seconds:.1f}s"


def run_checks(
    script: Script,
    plan: TimingPlan,
    cues: list[Cue],
    settings: Settings,
    asset_statuses: list[AssetStatus] | None = None,
) -> list[Diagnostic]:
    """Return every diagnostic, ordered by severity then by appearance."""
    found: list[Diagnostic] = []
    total = plan.total_duration
    low = settings.target_duration * (1 - settings.duration_tolerance)
    high = settings.target_duration * (1 + settings.duration_tolerance)

    if total <= 0:
        found.append(Diagnostic("EMPTY_SCRIPT", ERROR, "script produced no timed content"))
    elif not low <= total <= high:
        found.append(
            Diagnostic(
                "DURATION_OUT_OF_RANGE",
                ERROR,
                f"total {_fmt(total)} is outside {_fmt(low)} to {_fmt(high)} "
                f"for a {_fmt(settings.target_duration)} target",
            )
        )

    if settings.words_per_minute < settings.min_wpm or settings.words_per_minute > settings.max_wpm:
        found.append(
            Diagnostic(
                "WPM_OUT_OF_RANGE",
                WARNING,
                f"speaking rate {settings.words_per_minute} wpm is outside "
                f"{settings.min_wpm} to {settings.max_wpm}",
            )
        )

    if not script.title.strip() or script.title == "untitled":
        found.append(Diagnostic("MISSING_TITLE", WARNING, "no title in frontmatter", "frontmatter"))

    if len(script.sections) < settings.min_sections:
        found.append(
            Diagnostic(
                "TOO_FEW_SECTIONS",
                WARNING,
                f"{len(script.sections)} sections, expected at least {settings.min_sections}",
            )
        )

    if plan.sections:
        hook = plan.sections[0]
        if hook.duration > settings.hook_max_seconds:
            found.append(
                Diagnostic(
                    "HOOK_TOO_LONG",
                    WARNING,
                    f"first section runs {_fmt(hook.duration)}, keep it under "
                    f"{_fmt(settings.hook_max_seconds)}",
                    hook.title,
                )
            )
        if hook.duration < 3:
            found.append(
                Diagnostic(
                    "HOOK_TOO_SHORT",
                    WARNING,
                    f"first section runs {_fmt(hook.duration)}, too short to land",
                    hook.title,
                )
            )

    for section in plan.sections:
        if section.words == 0:
            found.append(Diagnostic("EMPTY_SECTION", ERROR, "section has no narration", section.title))

    for beat in plan.beats:
        if beat.duration > settings.max_beat_seconds:
            found.append(
                Diagnostic(
                    "BEAT_TOO_LONG",
                    INFO,
                    f"one paragraph runs {_fmt(beat.duration)}, consider splitting it",
                    beat.section_title,
                )
            )

    for cue in cues:
        if cue.duration <= 0:
            found.append(
                Diagnostic("CUE_ZERO_DURATION", ERROR, f"cue {cue.index} has no duration")
            )
            continue
        if cue.cps > settings.max_cps:
            found.append(
                Diagnostic(
                    "CAPTION_CPS_HIGH",
                    WARNING,
                    f"cue {cue.index} reads at {cue.cps} chars/sec, limit is {settings.max_cps}",
                )
            )
        if len(cue.lines) > settings.max_lines:
            found.append(
                Diagnostic(
                    "CAPTION_TOO_MANY_LINES",
                    WARNING,
                    f"cue {cue.index} has {len(cue.lines)} lines, limit is {settings.max_lines}",
                )
            )

    for phrase in settings.banned_phrases:
        haystack = " ".join(section.text.lower() for section in script.sections)
        if phrase in haystack:
            found.append(
                Diagnostic("BANNED_PHRASE", WARNING, f"script contains {phrase!r}")
            )

    if asset_statuses is not None:
        missing = [status for status in asset_statuses if not status.found]
        for status in missing:
            found.append(
                Diagnostic(
                    "ASSET_MISSING",
                    ERROR,
                    f"{status.request.name!r} is referenced at {_fmt(status.request.start)} "
                    f"but no file matches it",
                    status.request.section_title,
                )
            )

    return sorted(found, key=lambda item: (SEVERITY_ORDER[item.severity], item.code))


def has_errors(diagnostics: list[Diagnostic]) -> bool:
    return any(item.severity == ERROR for item in diagnostics)
