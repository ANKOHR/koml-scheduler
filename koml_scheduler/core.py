"""Pure validation and deterministic greedy allocation of declared capacity."""
from datetime import date


class SchedulerError(ValueError):
    """Named input or workflow failure."""


def fail(field, message):
    raise SchedulerError(f"SchemaError: {field}: {message}")


def text(value, field):
    if not isinstance(value, str) or not value or len(value) > 10000:
        fail(field, "expected nonempty string of at most 10000 characters")
    if chr(0x2014) in value or any(ord(c) < 32 for c in value):
        fail(field, "control characters and em dash are forbidden")


def integer(value, field, minimum=0):
    if type(value) is not int or not minimum <= value <= 1000000:
        fail(field, f"expected integer between {minimum} and 1000000")


def validate(data):
    if not isinstance(data, dict):
        fail("root", "expected object")
    required = {"synthetic", "source", "as_of", "tasks", "agents", "tools"}
    if set(data) != required:
        fail("root", f"fields must be {sorted(required)}; offending fields {sorted(set(data) ^ required)}")
    if type(data["synthetic"]) is not bool:
        fail("synthetic", "expected boolean")
    text(data["source"], "source")
    try:
        as_of = date.fromisoformat(data["as_of"])
    except (ValueError, TypeError):
        fail("as_of", "expected ISO date")
    for collection in ("tasks", "agents", "tools"):
        rows = data[collection]
        if not isinstance(rows, list):
            fail(collection, "expected list")
        ids = set()
        fields = {"id", "capabilities", "capacity_minutes"} if collection != "tasks" else {"id", "capability", "minutes", "priority", "created"}
        for i, row in enumerate(rows):
            prefix = f"{collection}[{i}]"
            if not isinstance(row, dict) or set(row) != fields:
                fail(prefix, f"expected fields {sorted(fields)}; offending fields {sorted(set(row) ^ fields) if isinstance(row, dict) else prefix}")
            text(row["id"], prefix + ".id")
            if row["id"] in ids:
                fail(prefix + ".id", "duplicate id")
            ids.add(row["id"])
            if collection == "tasks":
                text(row["capability"], prefix + ".capability")
                integer(row["minutes"], prefix + ".minutes", 1)
                integer(row["priority"], prefix + ".priority")
                try:
                    created = date.fromisoformat(row["created"])
                except (ValueError, TypeError):
                    fail(prefix + ".created", "expected ISO date")
                if created > as_of:
                    fail(prefix + ".created", "future date relative to as_of")
            else:
                integer(row["capacity_minutes"], prefix + ".capacity_minutes")
                if not isinstance(row["capabilities"], list):
                    fail(prefix + ".capabilities", "expected list")
                for value in row["capabilities"]:
                    text(value, prefix + ".capabilities")
    return data


def schedule(data):
    validate(data)
    agents = sorted(data["agents"], key=lambda r: r["id"])
    tools = sorted(data["tools"], key=lambda r: r["id"])
    remaining_a = {r["id"]: r["capacity_minutes"] for r in agents}
    remaining_t = {r["id"]: r["capacity_minutes"] for r in tools}
    allocations = []
    for task in sorted(data["tasks"], key=lambda r: (-r["priority"], r["id"])):
        eligible_a = [a for a in agents if task["capability"] in a["capabilities"]]
        eligible_t = [t for t in tools if task["capability"] in t["capabilities"]]
        pairs = [(a, t) for a in eligible_a for t in eligible_t
                 if remaining_a[a["id"]] >= task["minutes"] and remaining_t[t["id"]] >= task["minutes"]]
        entry = {"task_id": task["id"], "minutes": task["minutes"]}
        if pairs:
            a, t = pairs[0]
            remaining_a[a["id"]] -= task["minutes"]
            remaining_t[t["id"]] -= task["minutes"]
            entry.update(status="assigned", agent_id=a["id"], tool_id=t["id"])
        else:
            entry.update(status="unassigned", reason="missing_capability" if not eligible_a or not eligible_t else "capacity_exhausted")
        allocations.append(entry)
    assigned = [r for r in allocations if r["status"] == "assigned"]
    counts = {reason: sum(r.get("reason") == reason for r in allocations) for reason in ("missing_capability", "capacity_exhausted")}
    return {"provenance": {"synthetic": data["synthetic"], "source": data["source"], "as_of": data["as_of"]},
            "summary": {"tasks": len(allocations), "assigned": len(assigned), "unassigned": len(allocations)-len(assigned),
                        "allocated_minutes": sum(r["minutes"] for r in assigned), **counts},
            "allocations": allocations, "remaining_agent_minutes": remaining_a, "remaining_tool_minutes": remaining_t,
            "honesty": "Allocations computed from declared inputs; completion, time saved and money saved are unmeasured and are not reported."}
