# CampusFlow Design Decisions

## 1. Project structure

CampusFlow separates application code under `src/campus_flow/`,
automated tests under `tests/`, and project documentation under `docs/`.

## 2. Ticket workflow

Tickets follow this sequence:

`open -> in_progress -> resolved`

A ticket must be assigned before it enters `in_progress`.
A resolved ticket must be explicitly reopened before work resumes.

## 3. JSON persistence

Tickets are stored as JSON. Saving uses a temporary file followed by
replacement of the target file to reduce the risk of truncating existing
data during a failed save.

## 4. Automated tests

The suite lives in a single file, `tests/test_campusflow_next.py`, and covers
the 16 required verification cases plus two bug-hunter checks. Tests are grouped
in one file because they share a manager and a temporary data file per test.

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
