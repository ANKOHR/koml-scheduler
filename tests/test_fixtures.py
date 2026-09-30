import json
from koml_scheduler.fixtures import generate
from koml_scheduler.core import schedule


def test_fixtures_labelled_synthetic(tmp_path):
    generate(tmp_path)
    for path in tmp_path.glob("*.json"):
        assert json.loads(path.read_text(encoding="utf-8"))["synthetic"] is True
    assert "<!-- synthetic: true -->" in (tmp_path / "SYNTHETIC.md").read_text()


def test_fixture_ground_truth_matches_hand_computed(tmp_path):
    generate(tmp_path)
    data = json.loads((tmp_path / "input.json").read_text())
    expected = json.loads((tmp_path / "expectations.json").read_text())
    result = schedule(data)
    assert len(data["tasks"]) == 200
    assert result["summary"] == expected["summary"]
    assert result["remaining_agent_minutes"] == {"agent-a": 0, "agent-b": 0}
    assert result["remaining_tool_minutes"] == {"editor": 0}
    for row in result["allocations"]:
        if row["status"] == "assigned":
            assert row["agent_id"] == ("agent-a" if row["task_id"] < "task-050" else "agent-b")
            assert row["tool_id"] == "editor"
