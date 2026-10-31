from cutlist.captions import build_cues
from cutlist.checks import ERROR, has_errors, run_checks
from cutlist.config import Settings, settings_from_script
from cutlist.parser import parse_script
from cutlist.timing import build_plan

SHORT = """---
title: Short
target_duration: 12
---

# Hook
Ten words is not very many and this is still short.

# Body
Another ten words here to fill the middle section out.

# Close
Final ten words that wrap the whole thing up here.
"""


def _run(text: str, settings: Settings | None = None):
    script = parse_script(text)
    resolved = settings or settings_from_script(script)
    plan = build_plan(script, resolved.words_per_minute)
    cues = build_cues(plan, max_chars=resolved.max_chars_per_line, max_lines=resolved.max_lines)
    return script, plan, run_checks(script, plan, cues, resolved)


def test_matching_duration_has_no_error():
    _, plan, diagnostics = _run(SHORT)
    assert plan.total_duration < 60
    assert not has_errors(diagnostics)


def test_duration_out_of_range_is_an_error():
    text = SHORT.replace("target_duration: 12", "target_duration: 600")
    _, _, diagnostics = _run(text)
    assert any(item.code == "DURATION_OUT_OF_RANGE" and item.severity == ERROR for item in diagnostics)
    assert has_errors(diagnostics)


def test_hook_too_long_is_flagged():
    text = """---
title: Long hook
target_duration: 120
---

# Hook
""" + " ".join(["word"] * 80) + """

# Body
short body text here now.

# Close
closing text here now.
"""
    _, _, diagnostics = _run(text)
    assert any(item.code == "HOOK_TOO_LONG" for item in diagnostics)


def test_too_few_sections_is_flagged():
    text = """---
title: One section
target_duration: 60
---

# Only
Some words in the only section of this script.
"""
    _, _, diagnostics = _run(text)
    assert any(item.code == "TOO_FEW_SECTIONS" for item in diagnostics)


def test_banned_phrase_from_frontmatter_is_flagged():
    text = SHORT.replace("target_duration: 12", "target_duration: 12\nbanned_phrases: very many, short")
    _, _, diagnostics = _run(text)
    codes = [item.code for item in diagnostics]
    assert codes.count("BANNED_PHRASE") == 2


def test_high_cps_is_a_warning():
    text = """---
title: Fast
target_duration: 12
words_per_minute: 300
---

# Hook
""" + " ".join(["word"] * 30) + """

# Body
more words here.
"""
    _, _, diagnostics = _run(text)
    assert any(item.code == "CAPTION_CPS_HIGH" for item in diagnostics)


def test_wpm_outside_band_is_a_warning():
    _, _, diagnostics = _run(SHORT, Settings(target_duration=20, words_per_minute=400))
    assert any(item.code == "WPM_OUT_OF_RANGE" for item in diagnostics)


def test_diagnostics_are_sorted_by_severity():
    _, _, diagnostics = _run(SHORT, Settings(target_duration=900))
    severities = [item.severity for item in diagnostics]
    assert severities == sorted(severities, key=lambda value: {"error": 0, "warning": 1, "info": 2}[value])


def test_missing_asset_is_an_error():
    from pathlib import Path

    from cutlist.assets import collect_requests, resolve

    text = """---
title: Assets
target_duration: 30
---

# Hook
Open on the phone [[asset: phone.mp4]].

# Body
Body copy here for the middle of the show.

# Close
And we are done with the show today.
"""
    script, plan, _ = _run(text)
    statuses = resolve(collect_requests(script, plan), Path("/nonexistent"))
    settings = settings_from_script(script)
    cues = build_cues(plan, max_chars=42, max_lines=2)
    diagnostics = run_checks(script, plan, cues, settings, statuses)
    assert any(item.code == "ASSET_MISSING" and item.severity == ERROR for item in diagnostics)
