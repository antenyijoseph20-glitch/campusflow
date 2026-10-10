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

Tests are separated by responsibility:

- `test_tickets.py`: ticket creation, validation, IDs, and reports.
- `test_workflow.py`: assignment, workflow transitions, and manager rollback.
- `test_storage.py`: JSON loading, saving, validation, and file protection.
