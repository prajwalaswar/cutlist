"""Core data model for a narration script."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class AssetRef:
    """A reference to a media file, written in the script as [[asset: name]]."""

    name: str
    line: int


@dataclass
class Beat:
    """One spoken paragraph. Beats are the smallest timing unit."""

    text: str
    line: int
    assets: tuple[AssetRef, ...] = ()

    @property
    def words(self) -> int:
        return len(self.text.split())


@dataclass
class Section:
    """A heading plus its beats."""

    title: str
    line: int
    beats: list[Beat] = field(default_factory=list)

    @property
    def words(self) -> int:
        return sum(beat.words for beat in self.beats)

    @property
    def text(self) -> str:
        return " ".join(beat.text for beat in self.beats if beat.text).strip()


@dataclass
class Script:
    """A parsed script: metadata, sections, beats."""

    title: str
    sections: list[Section]
    meta: dict[str, str] = field(default_factory=dict)

    @property
    def words(self) -> int:
        return sum(section.words for section in self.sections)

    @property
    def beats(self) -> list[Beat]:
        return [beat for section in self.sections for beat in section.beats]

    @property
    def assets(self) -> list[AssetRef]:
        return [ref for beat in self.beats for ref in beat.assets]
