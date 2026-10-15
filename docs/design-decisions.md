# CampusFlow Design Decisions

## 1. Project structure

CampusFlow separates application code under `src/campus_flow/`,
automated tests under `tests/`, and project documentation under `docs/`.

## 2. Ticket workflow

Tickets follow this sequence:

`open -> in_progress -> resolved`

A ticket must be assigned before it enters `in_progress`, and must be
`in_progress` before it can be resolved. The transition from `open` straight to
`resolved` is rejected, so a ticket cannot be closed without ever being started.
A resolved ticket must be explicitly reopened before work resumes.

## 3. JSON persistence

Tickets are stored as JSON. Saving uses a temporary file followed by
replacement of the target file to reduce the risk of truncating existing
data during a failed save.

Loading validates the shape of the document before accepting it: the root must
be an array, each entry must be an object carrying all nine ticket fields, and
IDs must be present and unique. A document that fails any of these is rejected
whole. Rejecting the entire file rather than skipping bad records keeps the
in-memory list a faithful copy of the file, so no caller can observe a partial
load without knowing it.

This validates structure, not values. A record with a well-formed but illegal
`status` (say `"closed"`) loads successfully, because deciding which values are
legal belongs to `TicketManager`, not to the storage layer.

## 4. Automated tests

The suite is split by the module it exercises — `test_models.py`,
`test_storage.py`, `test_search_reports.py` and `test_quiz.py` — and covers the
16 required verification cases: 14 numbered cases plus two bug-hunter checks.
The case numbers in the test names are the contract, so they survive the split
unchanged even though the tests now live in four files.

`tests/test_cli.py` sits outside that contract. It covers the menu layer, which
the numbered cases never reached, by patching `input()` and capturing stdout.
`tests/test_main.py` covers the entry point the same way. Those tests are named
for what they check rather than numbered, so the distinction between required
coverage and added coverage stays visible.

`tests/base.py` holds what every test needs: the temporary directory and data
file, the manager built over it, and the import bootstrap. Discovery inserts
`tests/` but not the package directories, so the bootstrap puts both `src/` and
the repository root on `sys.path` — `src/` first, so the application package
resolves, and the root so `main.py` is importable. Discovery matches `test*.py`,
so `base.py` is imported by the test modules but never collected as one.

Each test uses its own temporary directory, so no test data is written into the
repository.

## 5. One canonical TicketManager

An earlier merge brought two different `TicketManager` implementations into the
package: a dict-record version returning `(bool, message)` tuples, and a
dataclass version raising `ValueError`. They were never reconciled, and neither
was importable after the `src/` layout refactor.

The dict-record version in `models.py` was kept, because the test matrix, the
storage layer, and the documentation were all written against it. The dataclass
version was removed. A single implementation avoids the two classes drifting
apart and removes the ambiguity about which error-handling contract applies.

## 6. Search and reporting kept separate

`search_reports.py` holds `TicketSearch` and `TicketReports`. Neither mutates
ticket data; both operate on the plain dict records produced by `TicketManager`.
Keeping them out of `models.py` keeps the manager focused on state transitions
and lets the search and report rules be tested in isolation.

## 7. AI assistance

Parts of this project were drafted with an AI assistant. The commit metadata
does not record that, so it is recorded here.

Assisted: first drafts of `search_reports.py`, `quiz.py`, the search and report
menus in `cli.py`, and parts of the test file and documentation. The decisions
in the sections above were reached by reviewing what the code actually did.

Every AI-produced artifact was verified by running it rather than by reading it:

| Claim | How it was checked |
|---|---|
| The package imports and runs | `python main.py` against a clean checkout |
| Behaviour matches the specification | the cases in `tests/test_models.py`, `test_storage.py`, `test_search_reports.py` and `test_quiz.py` |
| The reported defects were real | each reproduced in `baseline-check.md` before any fix |

Two limits are worth stating plainly. The quiz answer key was originally set to
the letters the grading fixture expected rather than derived from the rules, so
it verified the grader and not the questions — D8 is what that cost. `test_14`
now derives each letter from the behaviour the question asks about and fails if
the stored key disagrees, so a wrong key can no longer pass. The second limit
remains: search was exercised only at the scale of the test fixtures, not
against large ticket sets.

