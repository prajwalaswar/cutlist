"""Resolve [[asset: ...]] cues against a media folder."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .model import Script
from .timing import TimingPlan

MEDIA_SUFFIXES = {
    ".mp4",
    ".mov",
    ".mkv",
    ".webm",
    ".wav",
    ".mp3",
    ".m4a",
    ".png",
    ".jpg",
    ".jpeg",
    ".webp",
}


@dataclass(frozen=True)
class AssetRequest:
    name: str
    section_title: str
    beat_index: int
    start: float
    line: int


@dataclass(frozen=True)
class AssetStatus:
    request: AssetRequest
    found: bool
    path: str | None = None


def collect_requests(script: Script, plan: TimingPlan) -> list[AssetRequest]:
    """Pair every asset reference with the beat time it belongs to."""
    requests: list[AssetRequest] = []
    for beat_index, beat in enumerate(script.beats):
        if beat_index >= len(plan.beats):
            break
        timing = plan.beats[beat_index]
        for ref in beat.assets:
            requests.append(
                AssetRequest(
                    name=ref.name,
                    section_title=timing.section_title,
                    beat_index=beat_index,
                    start=timing.start,
                    line=ref.line,
                )
            )
    return requests


def _index_library(root: Path) -> dict[str, list[Path]]:
    by_name: dict[str, list[Path]] = {}
    for path in sorted(root.rglob("*")):
        if path.is_file() and path.suffix.lower() in MEDIA_SUFFIXES:
            by_name.setdefault(path.name.lower(), []).append(path)
            by_name.setdefault(path.stem.lower(), []).append(path)
    return by_name


def resolve(requests: list[AssetRequest], root: str | Path) -> list[AssetStatus]:
    """Match requests to files on disk, case-insensitively, by name or stem."""
    library_root = Path(root)
    index = _index_library(library_root) if library_root.is_dir() else {}
    statuses: list[AssetStatus] = []

    for request in requests:
        key = request.name.strip().lower()
        matches = index.get(key) or index.get(Path(key).stem)
        if matches:
            statuses.append(
                AssetStatus(
                    request=request,
                    found=True,
                    path=str(matches[0].relative_to(library_root)),
                )
            )
        else:
            statuses.append(AssetStatus(request=request, found=False))

    return statuses
