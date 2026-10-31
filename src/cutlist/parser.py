"""Markdown script parser.

Format:

    ---
    title: The AI Signal
    target_duration: 540
    ---

    # Hook
    One paragraph is one beat.

    A blank line starts the next beat.

    # Segment one
    Text with an inline media cue [[asset: broll/keynote.mp4]].
"""

from __future__ import annotations

import re
from pathlib import Path

from .model import AssetRef, Beat, Script, Section

ASSET_PATTERN = re.compile(r"\[\[asset:\s*(?P<name>[^\[\]]+?)\s*\]\]")
FRONTMATTER_FENCE = "---"
NUMBER_KEYS = {"target_duration", "words_per_minute", "max_cps", "duration_tolerance"}


class ScriptError(ValueError):
    """Raised when a script cannot be parsed."""

    def __init__(self, message: str, line: int | None = None) -> None:
        self.line = line
        location = f"line {line}: " if line is not None else ""
        super().__init__(f"{location}{message}")


def _split_frontmatter(lines: list[str]) -> tuple[dict[str, str], int]:
    """Return frontmatter values and the line index where the body starts."""
    if not lines or lines[0].strip() != FRONTMATTER_FENCE:
        return {}, 0

    for index in range(1, len(lines)):
        if lines[index].strip() == FRONTMATTER_FENCE:
            return _parse_frontmatter(lines[1:index], start_line=2), index + 1

    raise ScriptError("frontmatter block is not closed", 1)


def _parse_frontmatter(body: list[str], start_line: int) -> dict[str, str]:
    values: dict[str, str] = {}
    for offset, raw in enumerate(body):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if ":" not in line:
            raise ScriptError(f"expected 'key: value', got {line!r}", start_line + offset)
        key, value = line.split(":", 1)
        key = key.strip().lower()
        if not key:
            raise ScriptError("empty key in frontmatter", start_line + offset)
        values[key] = value.strip()
    return values


def _clean_beat(raw_lines: list[str], line_no: int) -> tuple[str, tuple[AssetRef, ...]]:
    joined = " ".join(part.strip() for part in raw_lines if part.strip())
    assets = tuple(
        AssetRef(name=match.group("name").strip(), line=line_no)
        for match in ASSET_PATTERN.finditer(joined)
    )
    text = ASSET_PATTERN.sub(" ", joined)
    text = re.sub(r"\s+", " ", text)
    # A removed token can leave "word ." behind; close the gap before punctuation.
    text = re.sub(r"\s+([.,!?;:])", r"\1", text)
    return text.strip(), assets


def parse_script(source: str, *, origin: str = "<script>") -> Script:
    """Parse markdown text into a :class:`Script`."""
    lines = source.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    meta, body_start = _split_frontmatter(lines)

    sections: list[Section] = []
    buffer: list[str] = []
    buffer_line = 0

    def flush() -> None:
        nonlocal buffer, buffer_line
        if not sections:
            buffer = []
            return
        if buffer:
            text, assets = _clean_beat(buffer, buffer_line)
            if text:
                sections[-1].beats.append(Beat(text=text, line=buffer_line, assets=assets))
        buffer = []

    for index in range(body_start, len(lines)):
        raw = lines[index]
        line_no = index + 1
        stripped = raw.strip()

        if stripped.startswith("# "):
            flush()
            sections.append(Section(title=stripped[2:].strip(), line=line_no))
            buffer_line = line_no
            continue

        if stripped.startswith("#"):
            raise ScriptError(f"only '# ' headings define sections, got {stripped!r}", line_no)

        if not stripped:
            flush()
            buffer_line = line_no + 1
            continue

        if not sections:
            raise ScriptError("text before the first '# ' heading", line_no)

        if not buffer:
            buffer_line = line_no
        buffer.append(raw)

    flush()

    if not sections:
        raise ScriptError(f"{origin}: no '# ' section headings found")

    empty = [section.title for section in sections if not section.beats]
    if empty:
        raise ScriptError(f"sections with no narration: {', '.join(empty)}")

    script = Script(
        title=meta.get("title") or Path(origin).stem or "untitled",
        sections=sections,
        meta=meta,
    )
    return script


def parse_file(path: str | Path) -> Script:
    """Read and parse a script file."""
    file_path = Path(path)
    try:
        source = file_path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ScriptError(f"cannot read {file_path}: {exc.strerror}") from exc
    return parse_script(source, origin=str(file_path))
