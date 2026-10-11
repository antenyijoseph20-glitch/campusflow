# CampusFlow — AI Learning Log

## Purpose

This document records the technical concepts, debugging lessons, design decisions, and practical experiments encountered while developing CampusFlow.

AI assistance is used as a learning aid, not as a substitute for understanding or verification. Suggestions should be reviewed, tested against the existing codebase, and accepted or rejected based on evidence.

The purpose of this log is to build practical software engineering skills and maintain a record of how the application evolves.

## Learning Principles

- Understand a proposed solution before adopting it.
- Preserve working functionality when making changes.
- Prefer small, focused changes over unnecessary rewrites.
- Verify behavior with tests and repeatable commands.
- Document failures and corrections honestly.
- Distinguish implemented features from proposed improvements.
- Update documentation when implementation decisions change.

## Learning Entries

### Entry 1 — Automated Testing with pytest

**Topic:** Automated testing and regression prevention.

**What I learned:**

Automated tests check whether code behaves as expected. Regression tests help detect when a new change breaks previously working functionality.

Tests are particularly useful when changing validation rules, ticket workflows, and persistence logic.

**Practical application:**

CampusFlow has tests covering ticket models, workflow behavior, and JSON storage.

**Verification commands:**

```bash
python -m pytest -v
python -m pytest -q
```

**Lesson learned:**

A successful test run provides evidence that the tested behavior works under the tested conditions. It does not prove that every possible scenario is correct.

**Next step:**

Continue adding tests for boundary values, malformed data, and failure scenarios.

### Entry 2 — Input Validation and Data Integrity

**Topic:** Validating data before accepting or storing it.

**What I learned:**

Applications should reject invalid input at appropriate boundaries rather than allowing incorrect values to spread through the system.

Validation should cover required fields, accepted values, numeric constraints, and consistency between related fields.

**Practical application:**

CampusFlow validates ticket information and checks ticket data loaded from JSON.

**Verification approach:**

Test valid tickets, invalid field values, missing required data, and inconsistent ticket records. Confirm that invalid data produces a clear error rather than being silently accepted.

**Lesson learned:**

Validation protects data integrity and makes application behavior more predictable.

**Next step:**

Review validation boundaries and ensure error messages remain clear and consistent.

### Entry 3 — Separation of Responsibilities

**Topic:** Modular application design.

**What I learned:**

Separating an application into modules makes it easier to understand, test, and maintain. Each module should have a clear responsibility and avoid unnecessary dependencies on unrelated parts of the application.

**Practical application:**

CampusFlow separates responsibilities across these modules:

- `models.py` — Ticket data and validation.
- `manager.py` — Ticket-management operations and workflow rules.
- `storage.py` — JSON loading and saving.
- `cli.py` — User interaction through the command line.
- `main.py` — Application entry point.

**Lesson learned:**

A modular structure makes individual components easier to reason about and helps prevent business logic from becoming tightly coupled to user input or file operations.

**Next step:**

Review module boundaries as the project grows and avoid duplicating validation or business rules.

### Entry 4 — Ticket State Machines

**Topic:** Controlled status transitions and business rules.

**What I learned:**

A state machine represents the valid states of an object and the transitions allowed between them. It prevents an application from accepting arbitrary state changes.

**Practical application:**

CampusFlow uses a ticket lifecycle:

```text
Open → In Progress → Resolved
  ↑                       |
  └──── Explicit reopen ──┘
```

A ticket must be assigned before moving into progress, and a resolved ticket must be explicitly reopened before further work.

**Verification approach:**

Test valid transitions, invalid transitions, assignment requirements, and reopening behavior.

**Lesson learned:**

Business rules should be enforced by the management logic, not only by the command-line interface. This makes the rules more consistent across different ways of using the application.

**Next step:**

Continue testing every permitted transition and important rejected transition.

### Entry 5 — JSON Persistence and Safe File Updates

**Topic:** Saving application data reliably.

**What I learned:**

Persistence allows application data to survive after a program exits. JSON is a convenient format for a small local application, but stored data must be validated when it is loaded.

Writing directly over an existing data file can risk leaving incomplete data if an operation fails at the wrong time.

**Practical application:**

CampusFlow's storage implementation uses temporary-file writing and atomic replacement to reduce the risk of damaging existing data during a save.

**Verification approach:**

Test normal saving and loading, malformed records, invalid JSON, and relevant file-operation failures.

**Lesson learned:**

Persistence is not just about writing data. A reliable implementation must also consider invalid input, failed writes, cleanup, and preservation of existing data.

**Next step:**

Continue reviewing failure handling and test that the original data remains intact when a save fails.

### Entry 6 — Rollback and Failure Handling

**Topic:** Keeping application state consistent when operations fail.

**What I learned:**

A management operation may modify an in-memory object before saving the change. If persistence then fails, the application can become inconsistent unless the change is rolled back or otherwise handled safely.

**Practical application:**

CampusFlow's management operations include rollback handling for supported changes when persistence fails.

**Verification approach:**

Simulate a persistence failure and verify that the affected ticket retains its previous state.

**Lesson learned:**

Error handling should protect both the user experience and the consistency of application data.

**Next step:**

Check that every operation that changes ticket state has appropriate failure handling and tests.

### Entry 7 — Git, Code Review, and Incremental Development

**Topic:** Version control and maintainable collaboration.

**What I learned:**

Git records project history and supports focused changes through branches and commits. Small, descriptive commits make it easier to understand why a change was made and to review its impact.

Code review helps identify incorrect assumptions, missing tests, and design problems before changes are integrated.

**Practical application:**

CampusFlow uses Git for source control and pull-request documentation to describe changes, implementation decisions, test results, and reviewer questions.

**Useful commands:**

```bash
git status
git diff --check
git diff
git log -5 --oneline
```

**Lesson learned:**

A clean working tree does not prove that the code is correct. Changes still need to be tested and reviewed before they are committed or merged.

**Next step:**

Keep commits focused and provide accurate test results in pull requests.

### Entry 8 — Documentation and Technical Communication

**Topic:** Writing documentation that matches the implementation.

**What I learned:**

Good documentation helps another developer understand a project's purpose, structure, setup, execution, testing, and limitations.

Documentation must describe existing behavior accurately. Planned features should be identified as future improvements rather than presented as completed functionality.

**Practical application:**

CampusFlow maintains a README, a design-decisions document, and this learning log.

**Lesson learned:**

Clear documentation is part of software quality. It reduces uncertainty for maintainers and helps reviewers verify the project's claims.

**Next step:**

Update documentation alongside meaningful code changes and verify all documented commands.

## Current Verification Checklist

Use this checklist when performing a project review. Mark items only after running the corresponding checks.

- [ ] Run the full pytest suite and record the actual result.
- [ ] Compile the application and test files.
- [ ] Check the Git diff for whitespace errors.
- [ ] Test invalid ticket input and workflow transitions.
- [ ] Test storage failures and state rollback.
- [ ] Verify installation and execution instructions.
- [ ] Review documentation for unsupported claims.

Example commands:

```bash
python -m pytest -v
python -m compileall -q src tests
git diff --check
```

## Reflection

The development of CampusFlow provides practical experience in Python, modular design, validation, testing, workflow enforcement, persistence, error handling, and version control.

The most important lesson is that working software should be supported by understandable design, repeatable tests, and honest documentation.

Future entries should record specific problems encountered, the reasoning behind a solution, the tests used to verify it, and any advice that was changed or rejected after review.