"""Settings resolution: defaults, frontmatter overrides, CLI overrides."""

from __future__ import annotations

from dataclasses import dataclass, field, replace

from .model import Script
from .parser import ScriptError


@dataclass(frozen=True)
class Settings:
    """Every tunable number in one place so checks and reports agree."""

    target_duration: float = 480.0
    words_per_minute: int = 150
    duration_tolerance: float = 0.15
    min_wpm: int = 120
    max_wpm: int = 180
    max_chars_per_line: int = 42
    max_lines: int = 2
    max_cps: float = 21.0
    max_beat_seconds: float = 25.0
    hook_max_seconds: float = 20.0
    min_sections: int = 3
    banned_phrases: tuple[str, ...] = field(default_factory=tuple)

    def with_overrides(self, **overrides: object) -> "Settings":
        clean = {key: value for key, value in overrides.items() if value is not None}
        return replace(self, **clean)


def _number(key: str, raw: str) -> float:
    try:
        return float(raw)
    except ValueError as exc:
        raise ScriptError(f"{key} must be a number, got {raw!r}") from exc


def _phrases(raw: str) -> tuple[str, ...]:
    return tuple(part.strip().lower() for part in raw.split(",") if part.strip())


def settings_from_script(script: Script, base: Settings | None = None) -> Settings:
    """Apply frontmatter values on top of ``base`` (or the defaults)."""
    settings = base or Settings()
    meta = script.meta
    overrides: dict[str, object] = {}

    if "target_duration" in meta:
        overrides["target_duration"] = _number("target_duration", meta["target_duration"])
    if "words_per_minute" in meta:
        overrides["words_per_minute"] = int(_number("words_per_minute", meta["words_per_minute"]))
    if "max_cps" in meta:
        overrides["max_cps"] = _number("max_cps", meta["max_cps"])
    if "duration_tolerance" in meta:
        overrides["duration_tolerance"] = _number("duration_tolerance", meta["duration_tolerance"])
    if "banned_phrases" in meta:
        overrides["banned_phrases"] = _phrases(meta["banned_phrases"])

    if overrides.get("words_per_minute", settings.words_per_minute) <= 0:
        raise ScriptError("words_per_minute must be greater than zero")
    if overrides.get("target_duration", settings.target_duration) <= 0:
        raise ScriptError("target_duration must be greater than zero")

    return settings.with_overrides(**overrides)
