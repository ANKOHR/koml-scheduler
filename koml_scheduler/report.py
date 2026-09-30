"""Reports state provenance and distinguish allocation from measured outcomes."""
from .fixtures import encode


def banner(result):
    p = result["provenance"]
    kind = "SYNTHETIC fixtures" if p["synthetic"] else "REAL input declared by operator (authorship not independently verified)"
    return f"Data provenance: {kind}; source: {p['source']}; as_of: {p['as_of']}"


def render(result, format="md"):
    if format == "json":
        return encode({"banner": banner(result), **result})
    lines = ["# KOML Scheduler report", "", banner(result), "", result["honesty"], "", "## Computed allocation totals", ""]
    lines += [f"- {key}: {value}" for key, value in result["summary"].items()]
    lines += ["", "## Task audit", "", "Each task below traces to its input id. Declared minutes are capacity units, not measured runtime.", ""]
    for r in result["allocations"]:
        detail = f"agent={r['agent_id']}, tool={r['tool_id']}" if r["status"] == "assigned" else r["reason"]
        lines.append(f"- {r['task_id']}: {r['status']}, minutes={r['minutes']}, {detail}")
    return "\n".join(lines) + "\n"
