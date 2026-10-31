import pytest

from cutlist.captions import build_cues, format_timestamp, to_srt, wrap_line
from cutlist.parser import parse_script
from cutlist.timing import build_plan

SCRIPT = """# Hook
Short line here. Another short line follows now.

# Body
This paragraph is long enough to need more than one caption cue because it keeps going.
"""


@pytest.mark.parametrize(
    ("seconds", "expected"),
    [
        (0, "00:00:00,000"),
        (1.5, "00:00:01,500"),
        (61.25, "00:01:01,250"),
        (3661.007, "01:01:01,007"),
    ],
)
def test_timestamp_format(seconds, expected):
    assert format_timestamp(seconds) == expected


def test_negative_timestamp_rejected():
    with pytest.raises(ValueError):
        format_timestamp(-1)


def test_wrap_respects_width_without_splitting_words():
    lines = wrap_line("alpha beta gamma delta epsilon", 12)
    assert all(len(line) <= 12 for line in lines)
    assert " ".join(lines) == "alpha beta gamma delta epsilon"


def test_wrap_keeps_one_long_word():
    assert wrap_line("supercalifragilistic", 10) == ["supercalifragilistic"]


def test_cues_cover_the_script_in_order():
    plan = build_plan(parse_script(SCRIPT), 150)
    cues = build_cues(plan, max_chars=32, max_lines=2)
    assert len(cues) >= 2
    assert cues[0].start == 0
    for previous, current in zip(cues, cues[1:]):
        assert current.start >= previous.start
    assert cues[-1].end <= plan.total_duration + 0.001


def test_cue_lines_never_exceed_limit():
    plan = build_plan(parse_script(SCRIPT), 150)
    for cue in build_cues(plan, max_chars=24, max_lines=2):
        assert len(cue.lines) <= 2
        assert all(len(line) <= 24 for line in cue.lines)


def test_srt_structure():
    plan = build_plan(parse_script(SCRIPT), 150)
    document = to_srt(build_cues(plan, max_chars=40, max_lines=2))
    blocks = document.strip().split("\n\n")
    assert blocks[0].startswith("1\n")
    assert "-->" in blocks[0]
    assert document.endswith("\n")


def test_invalid_limits_rejected():
    plan = build_plan(parse_script(SCRIPT), 150)
    with pytest.raises(ValueError):
        build_cues(plan, max_chars=4)
    with pytest.raises(ValueError):
        build_cues(plan, max_lines=0)


def test_cue_time_is_shared_by_characters_not_words():
    """Long words must not get squeezed: cps stays close to flat inside a beat."""
    from cutlist.parser import parse_script

    text = "# Hook\n" + "a " * 0 + "incomprehensibilities are balanced by tiny words like a I\n"
    plan = build_plan(parse_script(text), 150)
    cues = build_cues(plan, max_chars=20, max_lines=2)
    rates = [cue.cps for cue in cues if cue.duration > 0]
    assert max(rates) / min(rates) < 1.35
