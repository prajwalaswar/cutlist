from pathlib import Path

from cutlist.assets import collect_requests, resolve
from cutlist.parser import parse_script
from cutlist.timing import build_plan

SCRIPT = """# Hook
Open on the phone [[asset: broll/phone.mp4]].

# Body
Now the card [[asset: Outro-Card]] and a missing one [[asset: nope.mp4]].
"""


def _plan():
    script = parse_script(SCRIPT)
    return script, build_plan(script, 150)


def test_requests_carry_timing_and_section():
    script, plan = _plan()
    requests = collect_requests(script, plan)
    assert [request.name for request in requests] == ["broll/phone.mp4", "Outro-Card", "nope.mp4"]
    assert requests[0].start == 0
    assert requests[1].section_title == "Body"
    assert requests[1].start > 0


def test_resolve_by_full_name_stem_and_miss(tmp_path: Path):
    (tmp_path / "broll").mkdir()
    (tmp_path / "broll" / "phone.mp4").write_bytes(b"x")
    (tmp_path / "outro-card.png").write_bytes(b"x")

    script, plan = _plan()
    statuses = resolve(collect_requests(script, plan), tmp_path)

    assert statuses[0].found and statuses[0].path.endswith("phone.mp4")
    assert statuses[1].found and "outro-card" in statuses[1].path
    assert not statuses[2].found


def test_resolve_is_case_insensitive(tmp_path: Path):
    (tmp_path / "Phone.MP4").write_bytes(b"x")
    script, plan = _plan()
    statuses = resolve(collect_requests(script, plan), tmp_path)
    assert statuses[0].found


def test_missing_root_is_not_an_exception(tmp_path: Path):
    script, plan = _plan()
    statuses = resolve(collect_requests(script, plan), tmp_path / "absent")
    assert all(not status.found for status in statuses)
