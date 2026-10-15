# CampusFlow

**A Python command-line IT support ticket management system.**

CampusFlow helps IT support teams organize technical support requests, assign work to staff, prioritize tickets, manage ticket lifecycles, and review support workloads through reports.

The project emphasizes clear separation of responsibilities, input validation, reliable local JSON persistence, automated testing, and maintainable Python code.

## Table of Contents

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
- **Automated tests:** Test models, validation, storage, persistence, search, reporting, and workflow behavior.

## Technology Stack

| Technology | Purpose |
| JSON | Local ticket data persistence |
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
│   └── test_campusflow_next.py
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
- `tests/` — Contains the automated test suite.
- `baseline-check.md` — Records the initial audit, reproduced defects, and remediation.
- `learning_note.md` — Quiz explanations and mentor discussion points.
- `docs/design-decisions.md` — Records important technical decisions.
- `docs/ai-learning-log.md` — Documents learning, experimentation, and verification.

## Getting Started

### Prerequisites

- Python 3.12 or a compatible Python 3 version.
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
python -m pip install --upgrade pip
```

Install the project and its dependencies using the repository's packaging configuration:

```bash
python -m pip install -e .
```

If pytest is not included in the project's development dependencies, install it separately:

```bash
python -m pip install pytest
```

> If editable installation fails, check the build-system and dependency configuration in `pyproject.toml` before changing the installation instructions.

## Running the Application

From the project root, with the virtual environment activated, run:

```bash
python main.py
```

If the package has not been installed with `pip install -e .`, point Python at
the source directory instead:

```bash
PYTHONPATH=src python main.py
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
3. An in-progress ticket can move to `resolved`.
4. A resolved ticket must be explicitly reopened before further work.
5. Invalid transitions should be rejected rather than silently accepted.

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

On load, the file must parse as JSON and its root must be an array. Records
without an `id`, and duplicate IDs, cause the load to be rejected; the manager
then starts from an empty list rather than exposing corrupt data.

Saving writes the full document to a temporary file and then atomically replaces
the target, so a failed write cannot truncate existing data. If a save fails,
the in-memory change is rolled back to its previous value.

**Important:** JSON file persistence is appropriate for a learning project or a small local tool. It is not a substitute for a database with concurrency control, access management, backups, and operational monitoring in a multi-user production environment.

Before manually editing or deleting `tickets.json`, make a backup if its contents need to be preserved.

## Testing

Run the automated test suite from the repository root:

```bash
PYTHONPATH=src python -m unittest discover -s tests -v
```

`PYTHONPATH=src` is required because the package lives under `src/`: `unittest`
does not read the `pythonpath` setting in `pyproject.toml`. The prefix is
unnecessary once the package has been installed with `pip install -e .`.

Run the tests in quiet mode:

```bash
PYTHONPATH=src python -m unittest discover -s tests -q
```

The suite is written with `unittest` and also runs under `pytest`, which reads
the source path from `pyproject.toml` and therefore needs no prefix:

```bash
python -m pytest -q
```

Check the source and test files for compilation errors:

```bash
python -m compileall -q src tests
```

Check for whitespace errors in the Git diff:

```bash
git diff --check
```

### Test coverage areas

The suite contains the 16 required verification cases: 14 numbered cases plus
two bug-hunter checks.

- Priority rule precedence, including the `critical` boundary.
- The unassigned ticket guard and the resolved ticket lock.
- Strict validation of `affected_users` (zero, negative, decimal, boolean, text).
- Note addition, note ID assignment, and rejected notes not consuming an ID.
- Reopening a resolved ticket so that notes are accepted again.
- Case-insensitive substring search and multi-filter AND search.
- Empty-dataset reporting without a division-by-zero crash.
- Report counts staying in step with the ticket list after resolve/reopen.
- JSON round-trip of tickets, notes, and next IDs.
- Rejection of malformed JSON, a non-array root, and duplicate ticket IDs.
- Rollback of in-memory state when a save fails.
- Engineering Understanding Check scoring and rejection of invalid choices.

Run the tests after making changes and before opening a pull request. Report the
actual results rather than claiming that a check passed without running it.

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
- Add continuous integration and improve packaging and release workflows.
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
PYTHONPATH=src python -m unittest discover -s tests -v
python -m compileall -q src tests
git diff --check
```
Keep pull request descriptions accurate and identify any untested behavior.

## License

No license has been specified in this README. Before distributing the project for reuse, add a `LICENSE` file and document the chosen license here.
