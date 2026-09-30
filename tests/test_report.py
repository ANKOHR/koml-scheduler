import json
from koml_scheduler.core import schedule
from koml_scheduler.fixtures import fixture_data, generate
from koml_scheduler.report import render


def test_report_matches_ground_truth_exact(tmp_path):
    generate(tmp_path)
    expected = json.loads((tmp_path / "expectations.json").read_text())
    report = json.loads(render(schedule(fixture_data()), "json"))
    assert report["summary"] == expected["summary"]
    md = render(schedule(fixture_data()))
    for key, value in expected["summary"].items():
        assert f"- {key}: {value}\n" in md


def test_report_zero_false_positives(tmp_path):
    generate(tmp_path)
    expected = json.loads((tmp_path / "expectations.json").read_text())
    rows = json.loads(render(schedule(fixture_data()), "json"))["allocations"]
    assert [r["task_id"] for r in rows if r["status"] == "assigned"] == expected["assigned_ids"]
    for reason in ("missing_capability", "capacity_exhausted"):
        assert [r["task_id"] for r in rows if r.get("reason") == reason] == expected[reason + "_ids"]


def test_report_carries_provenance_banner():
    data = fixture_data(5)
    for fmt in ("md", "json"):
        assert "Data provenance: SYNTHETIC fixtures" in render(schedule(data), fmt)
        data["synthetic"] = False
        data["source"] = "Henry manually entered data"
        assert "REAL input declared by operator" in render(schedule(data), fmt)
        data["synthetic"] = True


def test_hypothetical_figures_labelled():
    for fmt in ("md", "json"):
        output = render(schedule(fixture_data()), fmt)
        assert "time saved and money saved are unmeasured and are not reported" in output


def test_no_em_dashes_in_outputs():
    for fmt in ("md", "json"):
        assert chr(0x2014) not in render(schedule(fixture_data()), fmt)
