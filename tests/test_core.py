import copy
import pytest
from koml_scheduler.core import schedule, SchedulerError
from koml_scheduler.fixtures import fixture_data, encode


def test_determinism_byte_identical():
    data = fixture_data()
    original = copy.deepcopy(data)
    assert encode(schedule(data)) == encode(schedule(data))
    assert data == original
    data["tasks"].reverse()
    assert schedule(data) == schedule(original)


@pytest.mark.parametrize("field,value", [("minutes", -1), ("minutes", True), ("minutes", 1000001), ("created", "2027-01-01"), ("id", "x" * 10001), ("priority", -1), ("capability", chr(0x2014))])
def test_rejects_adversarial_values(field, value):
    data = fixture_data(5)
    data["tasks"][0][field] = value
    with pytest.raises(SchedulerError, match=field):
        schedule(data)


def test_duplicate_ids_and_schema_drift():
    data = fixture_data(5)
    data["tasks"][1]["id"] = data["tasks"][0]["id"]
    with pytest.raises(SchedulerError, match="duplicate"):
        schedule(data)
    data = fixture_data(5)
    data["unexpected"] = 1
    with pytest.raises(SchedulerError, match="unexpected"):
        schedule(data)


def test_handles_unicode_and_long_inputs():
    data = fixture_data(5)
    data["tasks"][0]["id"] = "日本語 café C:\\work\\" + "x" * 9000
    assert schedule(data)["summary"]["assigned"] == 5


def test_capacity_never_overcommitted_and_priority_wins():
    data = fixture_data(5)
    data["agents"] = data["agents"][:1]
    data["agents"][0]["capacity_minutes"] = 1
    data["tasks"][4]["priority"] = 2
    result = schedule(data)
    assert result["allocations"][0]["task_id"] == "task-004"
    assert result["summary"]["assigned"] == 1
    assert result["remaining_agent_minutes"] == {"agent-a": 0}


def test_corrupted_ground_truth_changes_computed_figures():
    data = fixture_data()
    data["tasks"][0]["capability"] = "unknown"
    result = schedule(data)
    assert result["summary"]["missing_capability"] == 51
    assert result["summary"]["capacity_exhausted"] == 49
    assert result["allocations"][0]["status"] == "unassigned"
