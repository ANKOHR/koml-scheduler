import json
import time
import pytest
from koml_scheduler.cli import main
from koml_scheduler.fixtures import fixture_data, encode


def test_run_completes_on_fixture(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    start = time.perf_counter()
    assert main(["fixtures", "--out", "demo"]) == 0
    assert main(["run", "--input", "demo"]) == 0
    capsys.readouterr()
    assert main(["report", "--format", "md"]) == 0
    assert "Data provenance: SYNTHETIC" in capsys.readouterr().out
    assert time.perf_counter() - start < 5


def test_empty_input_renders_without_traceback(tmp_path, capsys):
    empty = tmp_path / "empty"
    empty.mkdir()
    result = tmp_path / "results.json"
    assert main(["run", "--input", str(empty), "--results", str(result)]) == 0
    capsys.readouterr()
    assert main(["report", "--results", str(result), "--format", "json"]) == 0
    output = json.loads(capsys.readouterr().out)
    assert all(value == 0 for value in output["summary"].values())


def test_malformed_input_named_error(tmp_path, capsys):
    (tmp_path / "input.json").write_text('{\n bad json')
    assert main(["run", "--input", str(tmp_path)]) == 2
    err = capsys.readouterr().err
    assert "ParseError" in err and "input.json" in err and "line 2" in err
    assert "Traceback" not in err


def test_cli_smoke_all_subcommands(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    for name in ("fixtures", "run", "validate", "capacity", "report"):
        with pytest.raises(SystemExit) as exc:
            main([name, "--help"])
        assert exc.value.code == 0
    assert main(["fixtures", "--out", "demo"]) == 0
    for name in ("validate", "capacity", "run"):
        assert main([name, "--input", "demo"]) == 0
    assert main(["report", "--format", "json", "--output", "report.json"]) == 0
    first = (tmp_path / ".ks/results.json").read_bytes()
    assert main(["run", "--input", "demo"]) == 0
    assert first == (tmp_path / ".ks/results.json").read_bytes()
    assert chr(0x2014) not in capsys.readouterr().out


def test_missing_input_and_write_failure(tmp_path, capsys):
    assert main(["run", "--input", str(tmp_path / "missing")]) == 2
    assert "MissingInput" in capsys.readouterr().err
    (tmp_path / "input.json").write_text(encode(fixture_data(5)))
    blocked = tmp_path / "blocked"
    blocked.write_text("preserve")
    assert main(["run", "--input", str(tmp_path), "--results", str(blocked / "out.json")]) == 2
    assert "WriteError" in capsys.readouterr().err
    assert blocked.read_text() == "preserve"
    assert set(p.name for p in tmp_path.iterdir()) == {"input.json", "blocked"}


def test_five_record_hand_written_example(tmp_path):
    from pathlib import Path
    import shutil
    source = Path(__file__).resolve().parents[1] / "examples" / "five" / "input.json"
    shutil.copy(source, tmp_path / "input.json")
    result = tmp_path / "result.json"
    assert main(["run", "--input", str(tmp_path), "--results", str(result)]) == 0
    summary = json.loads(result.read_text())["summary"]
    assert summary == {"tasks": 5, "assigned": 2, "unassigned": 3, "allocated_minutes": 3, "missing_capability": 1, "capacity_exhausted": 2}
