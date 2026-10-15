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
python3 -m unittest discover -s tests -v
python3 -m compileall -q src tests
git diff --check
```

Run `python3 -m pip install -e .` first so that the application can find the
`campus_flow` package under `src/`. The test command itself does not depend on
that install: `unittest` does not read the `pythonpath` setting in
`pyproject.toml`, so `tests/base.py` adds `src/` to the import path before any
test module imports the package, and the repository root alongside it so that
`main.py` is importable without an install either.

That setup cannot live in `tests/__init__.py`. Discovery with `-s tests` and no
`-t` takes `tests/` as its top-level directory, so it walks the folder as plain
modules and never imports the package — the first attempt at this fix did
exactly that and failed with `ModuleNotFoundError`.

Record the actual output. Do not mark an item verified without running it.

## 7. Follow-up review, after both features merged

A second audit was run against `main` after the reconciliation and the search,
reporting and quiz work were merged. It found defects of the same kind as
section 3, but in the documents rather than the code.

**D8 — The quiz marked a rejected transition as correct.** `quiz.py` Q1 asked
which status an open, unassigned ticket may move into, and marked `B`
("in_progress") correct — the one target `update_workflow` refuses. The answer
key had been set to satisfy the grading fixture at `B, C, B, C, C, B` rather
than derived from the rules, so the question contradicted the system it was
meant to test. `learning_note.md` described the rule correctly but labelled its
answer "B", which in the quiz meant something else.

**D9 — A ticket could skip `in_progress` entirely.** `update_workflow` rejected
`resolved -> anything but open` and `unassigned -> in_progress`, but nothing
required a ticket to be started before it was finished, so an unassigned ticket
could be resolved outright. The README diagram implies a single sequence and no
test covered the transition.

**D10 — Documentation still described files that no longer exist.**
`docs/ai-learning-log.md` Entry 3 listed `manager.py` as a live module months
after it was deleted. This is the D7 defect class, surviving the D7 fix.

**D11 — The test count was stated two ways.** `docs/design-decisions.md` read
"the 16 required verification cases plus two bug-hunter checks" (18), while
`README.md` read "14 numbered cases plus two bug-hunter checks" (16). The suite
runs 16.

**D12 — A malformed Markdown table.** The README technology table had no
delimiter row, so it rendered as literal text, and omitted Python.

**D13 — Stale runner instructions.** `baseline-check.md` and
`docs/ai-learning-log.md` still prescribed `python -m pytest`, although the
documented runner had changed to `unittest`.

**D14 — Non-string input raised instead of being rejected.** `create_ticket`,
`assign_ticket`, `update_workflow` and `add_note` called `.strip()` on their
arguments before type-checking, so an `int` title escaped as an
`AttributeError` rather than returning `(False, message)` like every other
invalid input.

**D15 — Load validated the ID but not the rest of the record.** `load_tickets`
checked that each entry was an object with a unique `id`, and nothing else. A
file whose record omitted `status` loaded without complaint, because the
duplicate-ID check passed, and then raised `KeyError` in `get_work_queue` and
in both report methods, which read `t["status"]` directly. The failure surfaced
at first use rather than at load, which is the point at which the storage layer
was supposed to have rejected it. D14 and D15 are the same defect in two
places: a validation gap that arrives as an exception instead of a message.

**D16 — `test_14` graded the quiz against its own fixture.** The test hardcoded
the letters `B, C, B, C, C, B` — the same letters stored as the answer key — and
asserted a full score. It could therefore confirm that the grader counts
correctly, but not that any question was right, because the expected values and
the values under test came from a single source. This is D4 one layer up: the
tautological tests asserted Python's own operators instead of the application's
behaviour, and `test_14` asserted the quiz's own key instead of the rules. It is
why D8 passed a green suite in precisely the form that made it wrong.

### Remediation

- D8: reworded Q1 so the marked option is the one the code actually permits.
- D9: added an explicit sequence guard to `update_workflow`, plus assertions in
  `test_02` covering both the rejection and the working path.
- D10–D13: corrected the affected documents.
- D14: added `isinstance` checks ahead of every `.strip()` call, with cases in
  `test_04`.
- D15: `load_tickets` now requires every record to carry all nine ticket fields,
  rejecting the file whole if any record is incomplete, with cases in `test_13`
  covering both a missing field and a non-object entry.
- D16: `test_14` now exercises the rule behind each question — the unassigned
  guard, the priority boundary, the resolved lock, note length, the boolean
  rejection, and the atomic save — locates the marked option by its wording
  rather than its position, and requires the stored key to agree with all six.
  A key that contradicts the code now fails the suite.
- Removed a bare `except:` in `storage.py`.

### What this review did not catch

Both audits were performed by reading and running the code. Neither compares the
documentation to the implementation automatically, which is why D10 and D11
survived a build whose test suite was fully green.

D16 is the same lesson stated as a test-design rule: a test whose expected values
are taken from the thing it is testing can only prove internal consistency, not
correctness. D8 and D16 were found by reading the quiz against the workflow
rules. No amount of re-running the suite would have surfaced either one, because
the suite was passing.
