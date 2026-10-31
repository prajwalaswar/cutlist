import json
from pathlib import Path

import pytest

from cutlist.cli import main

EXAMPLE = Path(__file__).resolve().parents[1] / "examples" / "ai-signal-ep42.md"


def test_plan_json(capsys):
    assert main(["plan", str(EXAMPLE), "--json"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["title"].startswith("The AI Signal 42")
    assert payload["total_duration"] > 0
    assert payload["sections"]


def test_plan_table(capsys):
    assert main(["plan", str(EXAMPLE)]) == 0
    out = capsys.readouterr().out
    assert "Timing plan" not in out
    assert "| Start |" in out


def test_captions_to_file(tmp_path, capsys):
    target = tmp_path / "captions.srt"
    assert main(["captions", str(EXAMPLE), "-o", str(target)]) == 0
    body = target.read_text(encoding="utf-8")
    assert "-->" in body
    assert "wrote" in capsys.readouterr().out


def test_captions_to_stdout(capsys):
    assert main(["captions", str(EXAMPLE)]) == 0
    assert "-->" in capsys.readouterr().out


def test_check_passes_clean_example(tmp_path, capsys):
    assets = tmp_path / "assets"
    (assets / "broll").mkdir(parents=True)
    (assets / "broll" / "phone-demo.mp4").write_bytes(b"x")
    (assets / "broll" / "outro-card.png").write_bytes(b"x")
    code = main(["check", str(EXAMPLE), "--assets", str(assets)])
    out = capsys.readouterr().out
    assert "No issues found." in out
    assert code == 0


def test_check_reports_missing_assets(tmp_path, capsys):
    code = main(["check", str(EXAMPLE), "--assets", str(tmp_path / "empty")])
    out = capsys.readouterr().out
    assert "ASSET_MISSING" in out
    assert code == 1


def test_check_json_output(capsys):
    assert main(["check", str(EXAMPLE), "--json"]) in (0, 1)
    payload = json.loads(capsys.readouterr().out)
    assert "diagnostics" in payload


def test_package_writes_all_files(tmp_path, capsys):
    out = tmp_path / "pkg"
    code = main(["package", str(EXAMPLE), "-o", str(out)])
    capsys.readouterr()
    assert (out / "report.md").exists()
    assert (out / "captions.srt").exists()
    assert (out / "timing.json").exists()
    assert (out / "assets.json").exists()
    assert "Production package" in (out / "report.md").read_text(encoding="utf-8")
    assert code == 0


def test_parse_error_exit_code(tmp_path, capsys):
    bad = tmp_path / "bad.md"
    bad.write_text("no headings here", encoding="utf-8")
    assert main(["plan", str(bad)]) == 2
    assert "cutlist:" in capsys.readouterr().err


def test_init_scaffolds(tmp_path, capsys):
    assert main(["init", str(tmp_path)]) == 0
    capsys.readouterr()
    assert (tmp_path / "script.md").exists()
    assert (tmp_path / "assets" / "broll").is_dir()


def test_init_refuses_overwrite(tmp_path, capsys):
    main(["init", str(tmp_path)])
    capsys.readouterr()
    assert main(["init", str(tmp_path)]) == 1
    assert "already exists" in capsys.readouterr().err
