# CampusFlow

**A Python command-line IT support ticket management system.**

CampusFlow helps IT support teams organize technical support requests, assign work to staff, prioritize tickets, manage ticket lifecycles, and review support workloads through reports.

The project emphasizes clear separation of responsibilities, input validation, reliable local JSON persistence, automated testing, and maintainable Python code.

## Table of Contents

- [Quick Start](#quick-start)
- [Overview](#overview)
- [Features](#features)
- [Technology Stack](#technology-stack)
- [Project Structure](#project-structure)
- [Getting Started](#getting-started)
- [Running the Application](#running-the-application)
- [Ticket Workflow](#ticket-workflow)
- [Data Storage](#data-storage)
- [Testing](#testing)
- [Design and Learning Documentation](#design-and-learning-documentation)
- [Limitations](#limitations)
- [Future Improvements](#future-improvements)
- [Contributing](#contributing)
- [License](#license)

## Quick Start

From a fresh clone, in four commands:

```bash
git clone https://github.com/antenyijoseph20-glitch/campusflow.git
cd campusflow
python3 -m pip install -e .
python3 -m unittest discover -s tests -v
```

The install step is what lets the *application* find the `campus_flow` package
under `src/`. The tests do not need it: the test module adds `src/` to the
import path itself, so the suite runs from a fresh clone even before it is
installed.

Run the application with:

```bash
python3 main.py
```

## Overview

IT support teams need a consistent way to record technical problems, assign responsibility, prioritize requests, and track progress.

CampusFlow provides a command-line solution for managing these activities. It is structured as a modular Python application, separating ticket models and validation, business logic, persistence, and the user interface.

The project is also a practical demonstration of Python application design, object-oriented programming, error handling, state transitions, JSON file operations, and automated testing.

## Features

- **Ticket management:** Create and view IT support tickets.
- **Input validation:** Validate ticket fields and reject invalid data.
- **Priority calculation:** Determine ticket priority from urgency and the number of affected users.
- **Staff assignment:** Assign tickets to responsible staff members.
- **Workflow management:** Control ticket status transitions.
- **Notes:** Attach follow-up notes to a ticket with per-ticket note IDs.
- **Search:** Case-insensitive substring search on titles, combined with category, status, urgency, and priority filters using strict logical AND.
- **Workload management:** Organize tickets into work queues.
- **Reporting:** Review ticket totals, status and priority breakdowns, and resolution percentage.
- **JSON persistence:** Store ticket records locally between application runs.
- **Safer file updates:** Use atomic file replacement when saving data.
- **Failure handling:** Roll back the in-memory change when a save fails, so memory never diverges from disk.
- **Engineering check:** A short multiple-choice quiz covering the rules the system enforces.
- **Automated tests:** Test models, validation, storage, persistence, search, reporting, workflow behavior, the CLI menu, and the entry point.

## Technology Stack

| Technology | Purpose |
|---|---|
| Python 3.8+ | Application language |
| JSON | Local ticket data persistence |
| `unittest` | Automated test suite (also runs under pytest) |
| Git and GitHub | Version control and collaboration |

## Project Structure

```text
campusflow/
├── docs/
│   ├── ai-learning-log.md
│   └── design-decisions.md
├── src/
│   └── campus_flow/
│       ├── __init__.py
│       ├── cli.py
│       ├── models.py
│       ├── quiz.py
│       ├── search_reports.py
│       └── storage.py
├── tests/
│   ├── __init__.py
│   ├── base.py
│   ├── test_cli.py
│   ├── test_main.py
│   ├── test_models.py
│   ├── test_quiz.py
│   ├── test_search_reports.py
│   └── test_storage.py
├── baseline-check.md
├── learning_note.md
├── main.py
├── pyproject.toml
└── README.md
```

`tickets.json` is created in the working directory on first use and is not
tracked by Git.

### Module responsibilities

- `models.py` — Defines `TicketManager`: ticket data, validation rules, workflow guards, notes, and priority logic.
- `storage.py` — Handles JSON persistence, data validation during loading, and atomic file updates.
- `search_reports.py` — Provides `TicketSearch` (case-insensitive multi-filter search) and `TicketReports` (aggregate reporting).
- `quiz.py` — Provides the Engineering Understanding Check question bank and grader.
- `cli.py` — Provides the command-line interface for interacting with the application.
- `main.py` — Serves as the application entry point.
- `tests/` — Contains the automated test suite, split by the module it exercises.
  `base.py` holds the shared per-test isolation and the import bootstrap that puts
  `src/` and the repository root on the path, and is not itself collected as a
  test module.
- `baseline-check.md` — Records the initial audit, reproduced defects, and remediation.
- `learning_note.md` — Quiz explanations and mentor discussion points.
- `docs/design-decisions.md` — Records important technical decisions.
- `docs/ai-learning-log.md` — Documents learning, experimentation, and verification.

## Getting Started

### Prerequisites

- Python 3.8 or newer. The project is developed and tested on Python 3.12, and
  declares `requires-python = ">=3.8"` in `pyproject.toml`.
- Git.
- A terminal or command-line environment.

Check your Python installation:

```bash
python3 --version
```

### 1. Clone the repository

```bash
git clone https://github.com/antenyijoseph20-glitch/campusflow.git
cd campusflow
```

### 2. Create a virtual environment

```bash
python3 -m venv venv
```

Activate it on Linux or macOS:

```bash
source venv/bin/activate
```

### 3. Install dependencies

Upgrade pip:

```bash
python3 -m pip install --upgrade pip
```

Install the project so that `campus_flow` is importable:

```bash
python3 -m pip install -e .
```

`pytest` is optional. The suite is written with `unittest` and runs without it;
install pytest only if you prefer that runner:

```bash
python3 -m pip install pytest
```

> If editable installation fails, check the build-system and dependency configuration in `pyproject.toml` before changing the installation instructions.

## Running the Application

From the project root, with the virtual environment activated, run:

```bash
python3 main.py
```

If the package has not been installed with `pip install -e .`, point Python at
the source directory instead:

```bash
PYTHONPATH=src python3 main.py
```

Follow the on-screen menu to select an available operation.

The application provides menus for creating and viewing tickets, assigning
staff, updating workflow status, adding notes, searching tickets, viewing the
work queue, and generating reports.

### Example session

```text
Select an option (1-10): 1
--- Create New Ticket ---
Enter ticket title: Wi-Fi down in Block A
Enter category: network
Enter urgency: high
Enter affected users (positive integer): 15
Success! Created ticket T001 with priority 'critical'.
```

Note that the category is accepted case-insensitively and stored in canonical
form as `Network`.

## Ticket Workflow

CampusFlow enforces a defined ticket lifecycle:

```text
Open → In Progress → Resolved
  ↑                       |
  └──── Explicit reopen ──┘
```

The intended rules are:

1. A ticket begins with an open status.
2. A ticket must be assigned before it can move to `in_progress`.
3. A ticket must be `in_progress` before it can move to `resolved`. An open
   ticket cannot skip straight to resolved.
4. A resolved ticket must be explicitly reopened before further work.
5. Invalid transitions are rejected with an error message rather than being
   silently accepted.

These rules help maintain consistent ticket state and make workflow behavior easier to test.

## Data Storage

CampusFlow uses a local JSON file for ticket persistence. The file is created at
the path passed to `TicketManager` (default `tickets.json`) and is excluded from
version control.

### JSON format

The file contains a single JSON array of ticket objects:

```json
[
    {
        "id": "T001",
        "title": "Wi-Fi down in Block A",
        "category": "Network",
        "urgency": "high",
        "affected_users": 15,
        "priority": "critical",
        "status": "open",
        "assigned_to": null,
        "notes": [
            {
                "note_id": "N001",
                "author": "Mentor A",
                "message": "Access point replaced and verified."
            }
        ]
    }
]
```

| Field | Type | Notes |
|---|---|---|
| `id` | string | Generated as `T` plus a zero-padded number. Must be unique. |
| `title` | string | Non-blank. |
| `category` | string | One of `Network`, `Hardware`, `Software`, `Other` (canonical form). |
| `urgency` | string | One of `low`, `medium`, `high`. |
| `affected_users` | integer | Positive; booleans and decimals are rejected. |
| `priority` | string | Derived: `critical`, `high`, `medium`, or `low`. |
| `status` | string | One of `open`, `in_progress`, `resolved`. |
| `assigned_to` | string or null | `null` while unassigned. |
| `notes` | array | Each entry has `note_id`, `author`, and `message`. |

### Loading and saving

On load, the file must parse as JSON and its root must be an array. Every record
must be an object carrying all nine ticket fields, with a present and unique
`id`. A record that is not an object, is missing a field, or repeats an ID
causes the load to be rejected, and the manager then starts from an empty list
rather than exposing corrupt data.

A rejected load therefore starts empty, and the next successful save writes that
empty list over the original file. If a file is rejected, copy it aside before
making any change, in case its contents are still recoverable by hand.

Saving writes the full document to a temporary file and then atomically replaces
the target, so a failed write cannot truncate existing data. If a save fails,
the in-memory change is rolled back to its previous value.

**Important:** JSON file persistence is appropriate for a learning project or a small local tool. It is not a substitute for a database with concurrency control, access management, backups, and operational monitoring in a multi-user production environment.

Before manually editing or deleting `tickets.json`, make a backup if its contents need to be preserved.

## Testing

Run the suite from the repository root:

```bash
python3 -m unittest discover -s tests -v
```

Quiet mode:

```bash
python3 -m unittest discover -s tests -q
```

This works from a fresh clone, with or without `pip install -e .`. `unittest`
does not read the `pythonpath` setting in `pyproject.toml`, and the `src/`
layout would otherwise leave `campus_flow` unimportable, so `tests/base.py` puts
`src/` and the repository root on the import path before any test module imports
the package. `src/` goes on first, so the suite always exercises the working tree
rather than an installed copy. The repository root goes on so that `main.py` is
importable the way `python3 main.py` reaches it. Discovery with `-s tests` and no
`-t` treats `tests/` as the top-level directory, which means `tests/__init__.py`
is never imported — the setup has to happen in a module discovery does load.

Installing the package remains the recommended setup and is what the application
needs; the bootstrap exists so the verification command is a single line with no
prerequisite.

The suite is written with `unittest`; `pytest` is not required. If it is
installed, the same tests also run under it, reading the source path from
`pyproject.toml`:

```bash
python3 -m pytest -q
```

Check the source and test files for compilation errors:

```bash
python3 -m compileall -q src tests
```

Check for whitespace errors in the Git diff:

```bash
git diff --check
```

### Test coverage areas

The suite contains the 16 required verification cases: 14 numbered cases plus
two bug-hunter checks.

- Priority rule precedence, including the `critical` boundary.
- The unassigned ticket guard, the resolved ticket lock, and the rule that a
  ticket must be `in_progress` before it can be resolved.
- Strict validation of `affected_users` (zero, negative, decimal, boolean, text)
  and of non-string `title`, `category`, and `urgency` values.
- Note addition, note ID assignment, and rejected notes not consuming an ID.
- Reopening a resolved ticket so that notes are accepted again.
- Case-insensitive substring search and multi-filter AND search.
- Empty-dataset reporting without a division-by-zero crash.
- Report counts staying in step with the ticket list after resolve/reopen.
- JSON round-trip of tickets, notes, and next IDs.
- Rejection of malformed JSON, a non-array root, duplicate ticket IDs, records
  missing required fields, and records that are not objects.
- Rollback of in-memory state when a save fails.
- Engineering Understanding Check scoring, rejection of invalid choices, and the
  answer key itself checked against the rules the code enforces.

Run the tests after making changes and before opening a pull request. Report the
actual results rather than claiming that a check passed without running it.

### Beyond the required cases

`tests/test_cli.py` covers the menu layer, which the 16 required cases do not
reach. It patches `input()` with a fixed sequence of answers and captures
stdout, so each handler runs its real code path: the input helpers, the table
renderer on an empty and a non-string row, every workflow branch (open,
resolved-and-declined, resolved-and-confirmed, missing ticket), the create,
view, list, search, report and work-queue handlers, and the menu loop's exit and
invalid-choice paths.

The workflow is checked at both layers on purpose. The menu offers only the legal
next status, and the model refuses an illegal one even when the user types it
anyway — the rule belongs to `TicketManager`, not to the prompt.

`tests/test_main.py` covers the entry point: that `main()` builds the CLI and
runs it, and that importing the module does not start the menu.

Every module under `src/campus_flow/` and the `main.py` entry point now has a
test file of its own. A prompt string is passed to `input()` rather than printed,
so it never appears in captured stdout — check one through the input mock, not
the output.

## Design and Learning Documentation

CampusFlow includes documentation describing technical decisions and the development learning process:

- [`docs/design-decisions.md`](docs/design-decisions.md)
- [`docs/ai-learning-log.md`](docs/ai-learning-log.md)
- [`baseline-check.md`](baseline-check.md) — the initial audit, reproduced defects, and remediation.
- [`learning_note.md`](learning_note.md) — quiz explanations and mentor discussion points.

These records help explain why design choices were made, how behavior was verified, and what was learned during implementation.

## Limitations

CampusFlow is currently a local command-line application.

- It uses local JSON storage rather than a database server.
- It does not currently provide a web interface.
- Multi-user access control and concurrent editing are not established production capabilities.
- Deployment, monitoring, backup automation, and production security hardening would require additional work.

These limitations are intentional areas for future development, not features that should be assumed to exist.

## Future Improvements

The following improvements may be considered as CampusFlow evolves. They are not requirements for the current implementation.

- Expand automated testing for edge cases and integration scenarios.
- Continue improving CLI validation and user feedback.
- Extend reporting and filtering where practical.
- Evaluate database storage if concurrent access or data volume justifies it.
- Consider authentication and role-based access control if multi-user support is introduced.
- Improve packaging and release workflows. Continuous integration is no longer on
  this list: `.github/workflows/checks.yml` runs the suite on Python 3.8 and 3.12,
  and once more against an editable install.
- Explore a web API or graphical interface if future requirements call for one.

Future changes should be driven by demonstrated needs and introduced incrementally, with appropriate tests and documentation.

## Contributing

Contributions, code reviews, and suggestions are welcome.

1. Fork the repository or create a feature branch.
2. Make a focused change.
3. Add or update tests for changed behavior.
4. Run the test suite and quality checks.
5. Review your changes before committing.
6. Open a pull request describing the change, implementation approach, test results, and known limitations.

Example validation commands:

```bash
python3 -m unittest discover -s tests -v
python3 -m compileall -q src tests
git diff --check
```
Keep pull request descriptions accurate and identify any untested behavior.

## License

No license has been specified in this README. Before distributing the project for reuse, add a `LICENSE` file and document the chosen license here.
