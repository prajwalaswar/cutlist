import pytest

from cutlist.parser import ScriptError, parse_file, parse_script

BASIC = """---
title: Demo
target_duration: 120
---

# Hook
First beat.

Second beat with a cue [[asset: broll/a.mp4]].

# Body
Only beat.
"""


def test_frontmatter_and_sections():
    script = parse_script(BASIC)
    assert script.title == "Demo"
    assert script.meta["target_duration"] == "120"
    assert [section.title for section in script.sections] == ["Hook", "Body"]


def test_beats_split_on_blank_lines():
    script = parse_script(BASIC)
    assert len(script.sections[0].beats) == 2
    assert script.sections[0].beats[0].text == "First beat."


def test_asset_tokens_are_stripped_from_spoken_text():
    script = parse_script(BASIC)
    beat = script.sections[0].beats[1]
    assert "[[asset" not in beat.text
    assert beat.text == "Second beat with a cue."
    assert [ref.name for ref in beat.assets] == ["broll/a.mp4"]


def test_words_count_excludes_asset_tokens():
    script = parse_script(BASIC)
    assert script.sections[0].beats[1].words == 5


def test_text_before_first_heading_raises():
    with pytest.raises(ScriptError) as exc:
        parse_script("loose text\n\n# Hook\nbeat")
    assert exc.value.line == 1


def test_no_headings_raises():
    with pytest.raises(ScriptError):
        parse_script("---\ntitle: x\n---\n\njust prose\n")


def test_unclosed_frontmatter_raises():
    with pytest.raises(ScriptError) as exc:
        parse_script("---\ntitle: x\n# Hook\nbeat")
    assert "not closed" in str(exc.value)


def test_empty_section_raises():
    with pytest.raises(ScriptError) as exc:
        parse_script("# Hook\n\n# Body\nreal words here")
    assert "no narration" in str(exc.value)


def test_h2_is_rejected():
    with pytest.raises(ScriptError):
        parse_script("# Hook\nbeat\n\n## Sub\nmore")


def test_title_falls_back_to_filename(tmp_path):
    path = tmp_path / "my-script.md"
    path.write_text("# Hook\nsome words\n", encoding="utf-8")
    assert parse_file(path).title == "my-script"


def test_crlf_input_is_normalised():
    script = parse_script("# Hook\r\nline one\r\n\r\nline two\r\n")
    assert len(script.sections[0].beats) == 2


def test_missing_file_raises():
    with pytest.raises(ScriptError):
        parse_file("/nonexistent/nope.md")
