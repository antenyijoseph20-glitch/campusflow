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
- **Workload management:** Organize tickets into work queues.
- **Reporting:** Review ticket and workload information.
- **JSON persistence:** Store ticket records locally between application runs.
- **Safer file updates:** Use atomic file replacement when saving data.
- **Failure handling:** Protect in-memory ticket state when supported operations fail to persist.
- **Automated tests:** Test models, validation, storage, persistence, and workflow behavior.

## Technology Stack

| Technology | Purpose |
|---|---|
| Python 3.12 | Application language |
| JSON | Local ticket data persistence |
| pytest | Automated testing |
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
│       ├── manager.py
│       ├── models.py
│       └── storage.py
├── tests/
│   ├── __init__.py
│   ├── test_storage.py
│   ├── test_tickets.py
│   └── test_workflow.py
├── main.py
├── pyproject.toml
├── tickets.json
└── README.md
```

### Module responsibilities

- `models.py` — Defines ticket data, validation rules, and priority-related logic.
- `manager.py` — Implements ticket-management operations and workflow rules.
- `storage.py` — Handles JSON persistence, data validation during loading, and safe file updates.
- `cli.py` — Provides the command-line interface for interacting with the application.
- `main.py` — Serves as the application entry point.
- `tests/` — Contains automated tests for ticket behavior, workflows, and persistence.
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

Follow the on-screen menu to select an available operation.

The application provides commands for managing tickets, assignments, workflows, queues, and reports. Available options depend on the current implementation.

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

CampusFlow uses a local JSON file for ticket persistence. The repository currently contains `tickets.json`.

The storage implementation is designed to validate ticket data and reduce the risk of corrupting existing data during saves.

Where supported by the management operations, a failed persistence operation triggers rollback of the affected in-memory change.

**Important:** JSON file persistence is appropriate for a learning project or a small local tool. It is not a substitute for a database with concurrency control, access management, backups, and operational monitoring in a multi-user production environment.

Before manually editing or deleting `tickets.json`, make a backup if its contents need to be preserved.

## Testing

Run the automated test suite from the repository root:

```bash
python -m pytest -v
```

Run the tests in quiet mode:

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

The test suite includes checks for:

- Ticket creation and field validation.
- Priority and ticket-data consistency.
- Invalid ticket data loaded from JSON.
- Storage behavior and persistence.
- Workflow transitions and assignment requirements.
- Handling of persistence failures.

Run the tests after making changes and before opening a pull request. Report the actual results rather than claiming that a check passed without running it.

## Design and Learning Documentation

CampusFlow includes documentation describing technical decisions and the development learning process:

- [`docs/design-decisions.md`](docs/design-decisions.md)
- [`docs/ai-learning-log.md`](docs/ai-learning-log.md)

These records help explain why design choices were made, how behavior was verified, and what was learned during implementation.

## Limitations

CampusFlow is currently a local command-line application.

- It uses local JSON storage rather than a database server.
- It does not currently provide a web interface.
- Multi-user access control and concurrent editing are not established production capabilities.
- Deployment, monitoring, backup automation, and production security hardening would require additional work.

These limitations are intentional areas for future development, not features that should be assumed to exist.

## Potential Future Enhancements

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
python -m pytest -v
python -m compileall -q src tests
git diff --check
```

Keep pull request descriptions accurate and identify any untested behavior.

## License

No license has been specified in this README. Before distributing the project for reuse, add a `LICENSE` file and document the chosen license here.