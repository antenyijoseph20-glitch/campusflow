# CampusFlow — Baseline Check

Initial audit of the repository, performed before the Engineer B feature work.
This records what was actually observed, not what was intended.

## 1. Test suite status at audit time

**Result: the suite could not be collected. Zero of the 16 tests executed.**

`tests/test_campusflow_next.py` failed at import time, so pytest reported a
collection error and ran nothing. Two independent causes were found:

| Line | Statement | Problem |
|---|---|---|
| 5 | `from campus_flow.search_reports import TicketSearch, TicketReports` | Module did not exist |
| 182 | `from campusflow import EngineeringQuiz` | Package renamed to `campus_flow`; class did not exist |

The `search_reports` reference was introduced by an uncommitted working-tree
edit. `test_14`'s reference to the pre-rename `campusflow` package was present
in the committed revision, so the suite was already failing to collect before
that edit.

## 2. Application status at audit time

**Result: no module in `src/campus_flow/` was importable.**

The package contained two different `TicketManager` implementations that were
merged from separate branches and never reconciled:

- `models.py` — dict-record manager returning `(bool, message)` tuples.
- `manager.py` — dataclass manager raising `ValueError`.

Both were broken by the `src/` layout refactor in commit `f052afe`:

| File | Statement | Problem |
|---|---|---|
| `models.py:1` | `from storage import StorageManager` | Bare import; `storage.py` moved under `campus_flow/` |
| `manager.py` | `from campus_flow.models import Ticket, TicketValidator, IDGenerator` | None of these names exist in `models.py` |
| `manager.py` | `from campus_flow.storage import StorageHandler` | The class is named `StorageManager` |

`main.py` and `cli.py` both import from `manager.py`, so the application entry
point was unreachable.

`__pycache__/campusflow.cpython-312.pyc` at the repository root confirmed a
flat, pre-`src/` module layout — the origin of both stale import styles.

## 3. Reproduced defects

**D1 — Suite does not run.** `python3 -m pytest -q` reports a collection error;
no test results are produced.

**D2 — Application does not start.** `python main.py` fails with
`ModuleNotFoundError`.

**D3 — Duplicate manager.** Two incompatible `TicketManager` classes coexist in
one package.

**D4 — Three tests were tautological.** `test_08`, `test_09` and `test_10`
re-implemented the logic inline instead of calling application code:

```python
# test_08 — asserts Python's `in` operator, not any search feature
self.assertTrue(query in ticket["title"].casefold())

# test_09 — a literal boolean expression, not any filter feature
match_1 = (t1["category"] == "Network" and t1["urgency"] == "high")

# test_10 — inline arithmetic over an empty list; 0.0 by construction
resolution_pct = (resolved / total * 100) if total > 0 else 0.0
```

These pass with zero implementation behind them, so they overstated coverage of
the search and reporting features. This contradicts the project's own stated
rule to distinguish implemented features from proposed ones.

**D5 — Documented rollback was not implemented.** `README.md` and
`docs/ai-learning-log.md` (Entry 6) both claim that a failed persistence
operation rolls back the in-memory change. Every mutator in `models.py` called
`self._sync()` and discarded its return value, so a failed save left memory
diverged from disk.

**D6 — Stale bytecode.** `tests/__pycache__/` retained `.pyc` files for
`test_storage`, `test_tickets` and `test_workflow`, deleted in `f052afe`.
`git status` reported the tree as clean.

**D7 — Documentation described files that do not exist.** `README.md` and
`docs/design-decisions.md` listed a three-file test suite and a `tickets.json`
that are not present.

## 4. Missing contract artifacts

| Artifact | Status at audit |
|---|---|
| `feat/22-search-and-insights` branch | Never created |
| `src/campus_flow/search_reports.py` | Missing |
| Engineering Understanding Check module | Missing |
| `baseline-check.md` | Missing (this file) |
| `learning_note.md` | Missing |
| README JSON format description | Missing |

## 5. Remediation applied

- Repaired the broken imports; confirmed the package imports cleanly.
- Kept the dict-based `models.py` API as canonical (the 16-test matrix, the
  storage layer and the docs all target it) and removed `manager.py`.
- Rewrote `cli.py` against the dict API and added note, search and report menus.
- Implemented `search_reports.py` (`TicketSearch`, `TicketReports`).
- Implemented the Engineering Understanding Check in `quiz.py`.
- Implemented and tested rollback (D5) in all four mutators.
- Replaced the three tautological tests with assertions that call real code.
- Removed stale bytecode (D6) and corrected the documentation (D7).

## 6. How to verify

```bash
python3 -m pytest -q
python3 -m compileall -q src tests
git diff --check
```

Record the actual output. Do not mark an item verified without running it.
