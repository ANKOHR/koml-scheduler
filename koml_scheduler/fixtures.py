"""Synthetic ground truth constructed in four blocks of 50; no randomness."""
import json
from pathlib import Path


def encode(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n"


def fixture_data(count=200):
    return {"synthetic": True, "source": "Labelled synthetic fixture, not real operator data", "as_of": "2026-09-30",
            "agents": [{"id": "agent-a", "capabilities": ["write"], "capacity_minutes": 50},
                       {"id": "agent-b", "capabilities": ["write"], "capacity_minutes": 50}],
            "tools": [{"id": "editor", "capabilities": ["write"], "capacity_minutes": 100}],
            "tasks": [{"id": f"task-{i:03}", "capability": "write" if i < 150 else "unknown", "minutes": 1,
                       "priority": 1, "created": "2026-09-29"} for i in range(count)]}


def generate(out):
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    expectations = {"synthetic": True, "method": "Hand computation: two agents x 50 minutes; editor 100 minutes; first 100 write tasks fit, next 50 do not, last 50 lack capability.",
                    "summary": {"tasks": 200, "assigned": 100, "unassigned": 100, "allocated_minutes": 100, "capacity_exhausted": 50, "missing_capability": 50},
                    "assigned_ids": [f"task-{i:03}" for i in range(100)],
                    "capacity_exhausted_ids": [f"task-{i:03}" for i in range(100, 150)],
                    "missing_capability_ids": [f"task-{i:03}" for i in range(150, 200)]}
    (out / "input.json").write_text(encode(fixture_data()), encoding="utf-8")
    (out / "expectations.json").write_text(encode(expectations), encoding="utf-8")
    (out / "SYNTHETIC.md").write_text("<!-- synthetic: true -->\n# Synthetic fixtures\nAll records are synthetic. No real outcomes or savings are measured.\n", encoding="utf-8")
