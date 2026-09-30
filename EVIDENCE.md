# Local acceptance evidence

Measured on 2026-09-30 using Python 3.12.10 on Windows, CPU only.

- pytest: 25 passed, 0.20 seconds reported by pytest.
- Installed CLI demo: fixtures, run, and Markdown report completed in 0.544850 seconds total wall time, including three process launches.
- Input: 200 labelled synthetic tasks, two agents and one tool.
- Computed totals exactly matched independent expectations: 100 assigned, 100 unassigned, 100 allocated minutes, 50 missing capability, 50 capacity exhausted.
- Tests checked exact assigned and unassigned task IDs, zero false positives, and resource pair choices.
- No measured real-use accuracy, completed work, time savings, monetary savings, or adoption results exist.

The test mutation changes one task capability to unavailable and produces 51 capability failures and 49 capacity failures. This demonstrates computation from input; the expectations file is never read by core or run.

This timing applies to the local synthetic acceptance workload only. It does not estimate production performance.
