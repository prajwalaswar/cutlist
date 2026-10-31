"""Caption cue generation and SRT output."""

from __future__ import annotations

import re
from dataclasses import dataclass

from .timing import TimingPlan

SENTENCE_END = re.compile(r"(?<=[.!?])\s+")


@dataclass(frozen=True)
class Cue:
    index: int
    start: float
    end: float
    lines: tuple[str, ...]

    @property
    def text(self) -> str:
        return "\n".join(self.lines)

    @property
    def characters(self) -> int:
        return len(" ".join(self.lines))

    @property
    def duration(self) -> float:
        return round(self.end - self.start, 3)

    @property
    def cps(self) -> float:
        return round(self.characters / self.duration, 2) if self.duration > 0 else float("inf")


def format_timestamp(seconds: float) -> str:
    """Format seconds as SRT time: HH:MM:SS,mmm."""
    if seconds < 0:
        raise ValueError("timestamp cannot be negative")
    total_ms = int(round(seconds * 1000))
    hours, rest = divmod(total_ms, 3_600_000)
    minutes, rest = divmod(rest, 60_000)
    secs, millis = divmod(rest, 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def wrap_line(text: str, max_chars: int) -> list[str]:
    """Greedy wrap that never splits a word."""
    words = text.split()
    if not words:
        return []
    lines: list[str] = []
    current = words[0]
    for word in words[1:]:
        candidate = f"{current} {word}"
        if len(candidate) <= max_chars:
            current = candidate
        else:
            lines.append(current)
            current = word
    lines.append(current)
    return lines


def split_sentences(text: str) -> list[str]:
    return [part.strip() for part in SENTENCE_END.split(text) if part.strip()]


def build_cues(
    plan: TimingPlan,
    *,
    max_chars: int = 42,
    max_lines: int = 2,
) -> list[Cue]:
    """Split each beat into cues while keeping cue times inside the beat."""
    if max_chars < 8:
        raise ValueError("max_chars must be at least 8")
    if max_lines < 1:
        raise ValueError("max_lines must be at least 1")

    cues: list[Cue] = []

    for beat in plan.beats:
        lines: list[tuple[str, int]] = []
        for sentence in split_sentences(beat.text):
            for line in wrap_line(sentence, max_chars):
                lines.append((line, len(line.split())))

        if not lines:
            continue

        # Time inside a beat is shared by characters, not words: reading speed
        # tracks how much text is on screen, so this keeps chars-per-second flat
        # instead of punishing long words.
        chunks = [
            lines[index : index + max_lines] for index in range(0, len(lines), max_lines)
        ]
        weights = [max(len(" ".join(line for line, _ in chunk)), 1) for chunk in chunks]
        total_weight = sum(weights)
        cursor = 0
        consumed = 0
        beat_duration = beat.end - beat.start

        for chunk, weight in zip(chunks, weights):
            start = beat.start + beat_duration * (consumed / total_weight)
            consumed += weight
            end = beat.start + beat_duration * (consumed / total_weight)
            cursor += 1
            cues.append(
                Cue(
                    index=cursor,
                    start=round(start, 3),
                    end=round(min(end, beat.end), 3),
                    lines=tuple(line for line, _ in chunk),
                )
            )

    return cues


def to_srt(cues: list[Cue]) -> str:
    """Render cues as an SRT document."""
    blocks = []
    for position, cue in enumerate(cues, start=1):
        blocks.append(
            f"{position}\n{format_timestamp(cue.start)} --> {format_timestamp(cue.end)}\n{cue.text}"
        )
    return "\n\n".join(blocks) + "\n" if blocks else ""
