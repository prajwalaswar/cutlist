"""Turn word counts into a second-accurate timing plan."""

from __future__ import annotations

from dataclasses import dataclass

from .model import Script


@dataclass(frozen=True)
class BeatTiming:
    section_index: int
    beat_index: int
    section_title: str
    text: str
    words: int
    start: float
    end: float

    @property
    def duration(self) -> float:
        return round(self.end - self.start, 3)


@dataclass(frozen=True)
class SectionTiming:
    index: int
    title: str
    words: int
    start: float
    end: float

    @property
    def duration(self) -> float:
        return round(self.end - self.start, 3)


@dataclass(frozen=True)
class TimingPlan:
    beats: tuple[BeatTiming, ...]
    sections: tuple[SectionTiming, ...]
    words: int
    words_per_minute: int

    @property
    def total_duration(self) -> float:
        return round(self.beats[-1].end, 3) if self.beats else 0.0

    @property
    def seconds_per_word(self) -> float:
        return 60.0 / self.words_per_minute if self.words_per_minute else 0.0


def build_plan(script: Script, words_per_minute: int) -> TimingPlan:
    """Distribute the script over time at a fixed speaking rate.

    Timing is derived from cumulative words so rounding never drifts and beat
    boundaries line up exactly with the next beat's start.
    """
    if words_per_minute <= 0:
        raise ValueError("words_per_minute must be greater than zero")

    seconds_per_word = 60.0 / words_per_minute
    beats: list[BeatTiming] = []
    sections: list[SectionTiming] = []
    cumulative = 0

    for section_index, section in enumerate(script.sections):
        section_start = cumulative * seconds_per_word
        for beat_index, beat in enumerate(section.beats):
            start = cumulative * seconds_per_word
            cumulative += beat.words
            end = cumulative * seconds_per_word
            beats.append(
                BeatTiming(
                    section_index=section_index,
                    beat_index=beat_index,
                    section_title=section.title,
                    text=beat.text,
                    words=beat.words,
                    start=round(start, 3),
                    end=round(end, 3),
                )
            )
        section_end = cumulative * seconds_per_word
        sections.append(
            SectionTiming(
                index=section_index,
                title=section.title,
                words=section.words,
                start=round(section_start, 3),
                end=round(section_end, 3),
            )
        )

    return TimingPlan(
        beats=tuple(beats),
        sections=tuple(sections),
        words=script.words,
        words_per_minute=words_per_minute,
    )
