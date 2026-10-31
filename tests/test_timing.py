import pytest

from cutlist.parser import parse_script
from cutlist.timing import build_plan

SCRIPT = """# Hook
one two three four five six seven eight nine ten

# Body
one two three four five six seven eight nine ten
"""


def test_duration_is_words_over_wpm():
    plan = build_plan(parse_script(SCRIPT), 120)
    assert plan.words == 20
    assert plan.total_duration == pytest.approx(10.0)


def test_beats_are_contiguous():
    plan = build_plan(parse_script(SCRIPT), 120)
    first, second = plan.beats
    assert first.start == 0
    assert first.end == second.start
    assert second.end == pytest.approx(10.0)


def test_section_totals_match_beats():
    plan = build_plan(parse_script(SCRIPT), 120)
    for section in plan.sections:
        beats = [beat for beat in plan.beats if beat.section_index == section.index]
        assert section.words == sum(beat.words for beat in beats)
        assert section.duration == pytest.approx(sum(beat.duration for beat in beats))


def test_slower_rate_takes_longer():
    script = parse_script(SCRIPT)
    fast = build_plan(script, 180)
    slow = build_plan(script, 90)
    assert slow.total_duration > fast.total_duration


def test_zero_wpm_rejected():
    with pytest.raises(ValueError):
        build_plan(parse_script(SCRIPT), 0)
