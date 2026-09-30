# KOML Scheduler

`ks` automatically allocates local work across declared agents and tools. It uses exact capability matches and capacity budgets. It produces an auditable plan; it does not execute agents or invoke tools, models, networks, or GPUs.

## Quickstart

Python 3.10 or newer, setuptools and pip are required. Runtime has no dependencies. For a local installation without network access:

```powershell
python -m pip install --no-deps --no-build-isolation -e .
ks fixtures --out demo
ks run --input demo
ks report --format md
python -m pytest -q
```

On Windows, if pip warns that the Scripts directory is not on PATH, add the exact directory printed by pip to your current PowerShell session before running `ks`:

```powershell
$env:PATH = "<Scripts directory printed by pip>;$env:PATH"
```

You can also use `python -m koml_scheduler.cli` in place of `ks`.

The fixture demo has 200 synthetic tasks. Expected totals: 100 assigned, 100 unassigned, 100 allocated minutes, 50 missing capability, 50 capacity exhausted. These are computed allocation figures, not completed jobs or measured savings. A separate hand-written five-task example is available:

```powershell
ks run --input examples/five
ks report --format json
```

It assigns tasks a and b, consumes 3 declared minutes, rejects c and e for capacity, and rejects d for missing capability.

## Input format reference

An input directory contains exactly one `input.json`. Other files such as `expectations.json` are metadata and are not read by the scheduler. Only JSON input is supported. An entirely empty directory produces zero totals with a no-records provenance banner. A missing directory or a nonempty directory without input.json is an error.

The five-task example documents the complete schema. Root fields are required and no additional fields are accepted:

| Field | Rule |
| --- | --- |
| synthetic | Boolean, true for fixtures, false for operator-entered real data |
| source | Nonempty provenance description supplied by the operator |
| as_of | ISO date used as the explicit date boundary, never the machine clock |
| tasks | List of task objects |
| agents, tools | Lists of resource objects |

Task fields: `id`, `capability`, `minutes`, `priority`, `created`. Resource fields: `id`, `capabilities` (list of strings), `capacity_minutes`. IDs must be unique within each collection. Strings accept Unicode and Windows paths, up to 10000 characters, and reject control characters and the em dash character. JSON Windows paths need escaped backslashes. Minutes must be integers from 1 to 1000000. Priority and capacity must be integers from 0 to 1000000. Booleans are not integers. Negative values and fractional amounts are rejected. Created dates later than the supplied as_of date are rejected. Dates are compared to the explicit input boundary, not to today's date. No monetary input or savings field exists.

For real use Henry enters his own records manually, sets synthetic to false, and names the origin in source. The report states that this is operator-declared provenance, not independently verified authorship. Trial input and trial results remain local and are not shipped. Synthetic and real records must use separate input directories; mixed provenance is unsupported.

## Allocation rules

Tasks sort by descending priority, then ascending Unicode ID. Agents and tools sort by ascending ID. Each task requires one agent and one tool with the exact declared capability, each with enough remaining minutes. The first eligible pair is allocated and both budgets decrease by the task's declared minutes. No eligible agent or tool means `missing_capability`; eligible resources without a fitting pair means `capacity_exhausted`. Every task appears exactly once in the audit. Counts and allocated minutes reconcile with the audit and capacity decrements.

This greedy policy is deterministic and respects priority, but it does not guarantee maximum throughput. It has no concurrency, calendar, dependencies, duration prediction, resource health probing, or recovery execution. Declared capacity can be wrong; the scheduler cannot verify it. Worst-case work grows with tasks times agents times tools. The acceptance benchmark covers 200 tasks and three resources, not arbitrary fleet sizes.

## Subcommand catalogue

Every subcommand supports `--help` and gives an example.

```powershell
ks fixtures --out demo                 # labelled synthetic data and independent expectations
ks validate --input demo               # validate schema and provenance
ks capacity --input demo               # inspect declared budgets, not measured runtime
ks run --input demo                    # allocate and atomically save .ks/results.json
ks run --input demo --results local/results.json
ks report --format md                  # print latest saved result, does not rerun inputs
ks report --format json --output local/report.json
ks report --results local/results.json --format md
```

Run output is a JSON report with provenance. Reports read a saved result, so rerun after changing input. Runs overwrite the selected result file atomically. A failed run preserves any previous result; it remains an older result and must not be mistaken for a new successful run. No timestamps or random IDs are added. The same inputs yield byte-identical saved files and reports. There is no randomness and no seed is needed.

## Architecture

```text
input.json -> CLI load and schema validation -> pure core.schedule
                                              |
                                              v
                                      atomic saved results
                                              |
                                              v
                           report.render -> Markdown or JSON
fixtures.generate -> synthetic input + independent hand-computed expectations
```

Core has no I/O. CLI owns local reads, named errors, and atomic writes. Fixtures construct four labelled blocks of 50 tasks. Reports expose provenance, totals, and every task's reason or resource pair.

## Honesty boundary and fixture policy

All allocations are computed from explicit inputs. Resource minutes and task minutes are declared quantities, not measured execution durations. Time saved, money saved, completion rates, and predicted performance are unmeasured and are not reported. No hypothetical savings numbers are emitted. The benchmark duration is a measured local test result, not a claim about real production fleets.

JSON fixture files include `synthetic: true`; JSON does not allow header comments. Each fixture directory includes a Markdown file with a synthetic header comment. Hand-written examples follow the same policy. Every report carries a provenance banner. Hand-computed expectations are metadata, never imported into scheduling logic.

## Failure modes and acceptance evidence

Malformed JSON yields `ParseError` with file and parser line. Missing input yields `MissingInput` and a usage hint. Schema drift yields `SchemaError` identifying the field, file, and line 1 as a document-level location; nested schema errors name the collection index and field. Unsupported formats are named schema errors. I/O failures are named `InputError` or `WriteError`. Exit status is 2 for workflow errors. Report writes use a temporary sibling and atomic replacement, with cleanup on failure, preserving an existing target. No traceback is shown for these errors.

The pytest suite covers planted IDs and exact figures, zero false positives, corrupted task data changing output, empty input, malformed JSON, missing input, schema drift, negative and extreme values, future dates, duplicate IDs, Unicode and long strings, priority and budget reconciliation, provenance, unmeasured savings labels, byte determinism, all subcommands, and write failure cleanup. `EVIDENCE.md` records measured local tests and CLI timing. `BUILD-DONE.txt` records the tested implementation commit.

## Two-week improvement hook and verdict

The evidence window starts with Henry's first real use, not this synthetic build. Track real runs locally for 14 days: run date, tasks hand-checked, disagreements with the documented allocation rule, and whether the run was used. Primary metric is allocation error rate = disagreements / hand-checked tasks. With zero checked tasks the error rate is unmeasured, never zero. Capture manual review time if time savings will be claimed, with a measured baseline and comparable workload.

If measured error rate exceeds 10 percent, fix the largest observed failure cause and repeat the check, or kill with a recorded reason. If no real runs were used, kill with that reason. Record the final verdict in `VERDICT.md`: expand for daily use or revenue, integrate for substantial sibling overlap, commercialise for a buyer willing to pay as-is, maintain as portfolio evidence otherwise, kill for no use or failed acceptance. No final verdict is claimed before the two-week evidence window. Synthetic acceptance only demonstrates correct implementation of this allocation policy.
