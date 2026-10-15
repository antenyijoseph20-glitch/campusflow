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

### Entry 1 — Automated Testing with unittest

**Topic:** Automated testing and regression prevention.

**What I learned:**

Automated tests check whether code behaves as expected. Regression tests help detect when a new change breaks previously working functionality.

Tests are particularly useful when changing validation rules, ticket workflows, and persistence logic.

**Practical application:**

CampusFlow has tests covering ticket models, workflow behavior, search, reporting, and JSON storage.

**Verification commands:**

```bash
python3 -m unittest discover -s tests -v
python3 -m unittest discover -s tests -q
```

**Lesson learned:**

A successful test run provides evidence that the tested behavior works under the tested conditions. It does not prove that every possible scenario is correct.

Where the expected values come from matters as much as the assertions. A test that takes its expectations from the code under test — by repeating the same fixture, or the same literal, on both sides — can only show that the code agrees with itself. The quiz test did exactly that: it graded the answer key using the answer key, so it passed while the key was wrong. Deriving each expected value from an independent source, such as the behavior of the system the question is about, is what gives a test the ability to fail.

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

- `models.py` — Ticket data, validation, workflow rules, and notes.
- `storage.py` — JSON loading and saving.
- `search_reports.py` — Search and aggregate reporting.
- `quiz.py` — The Engineering Understanding Check question bank and grader.
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

## Engineer Cycles

Each cycle records the original gap, the prompt used, how the result was
verified, and the decision taken.

### Engineer A — Cycle 1: Storage validation and atomic saves

**Original gap.** Ticket data was written straight over the JSON file. A failure
partway through a write could truncate the file, and corrupt data on disk was
loaded without complaint.

**Prompt.** Add schema validation on load and atomic replacement on save, and
reject malformed files instead of crashing.

**Verification.** Wrote corrupt files by hand (malformed JSON, a non-array root,
duplicated ticket IDs) and confirmed the manager starts empty rather than
raising or exposing bad records. Confirmed a save leaves the original file
intact when the write fails.

**Decision.** Kept `StorageManager` as the single persistence boundary, with
`load_tickets` returning `None` on rejection so the caller decides the fallback.
Rejected returning partial data, because a partially loaded file is harder to
reason about than an explicit empty start.

### Engineer A — Cycle 2: Note ID continuity and rollback

**Original gap.** Note IDs risked restarting at `N001` after a reload, and a
failed save left memory describing a change that was never persisted.

**Prompt.** Make note IDs survive a reload, and make the in-memory state agree
with disk when a save fails.

**Verification.** Created a ticket with a note, constructed a second manager over
the same file, added another note, and confirmed it received `N002`. Then
replaced `save_tickets` with a failing stub and confirmed each mutator restored
the value it had replaced.

**Decision.** Derive the note ID from the stored notes rather than keeping a
separate counter, so the counter cannot fall out of sync with the data. Roll
back by restoring the previous value in the mutator, which keeps the recovery
path next to the change it undoes.

### Engineer B — Cycle 1: Search and reporting

**Original gap.** The test matrix specified search and reporting tests, but
nothing implemented them. Three tests (`test_08`, `test_09`, `test_10`)
re-implemented the expected logic inline, so they passed without any feature
existing — the coverage claim was false.

**Prompt.** Implement case-insensitive substring search with strict AND filters,
and reporting that is safe on an empty dataset, then replace the inline
assertions with tests that call the real code.

**Verification.** Searched a known fixture with mixed-case queries, confirmed a
lowercase category filter matched the canonical stored value, confirmed that
adding a filter the ticket fails empties the result set, and confirmed an empty
dataset reports `0.0` without raising.

**Decision.** Kept search and reporting in `search_reports.py` rather than
`models.py`, so the manager stays focused on state transitions. Made an unknown
filter name raise `ValueError` instead of being ignored, so a typo is reported
rather than returning misleading results.

### Engineer B — Cycle 2: The Engineering Understanding Check

**Original gap.** `test_14` imported `EngineeringQuiz` from a module that no
longer existed after the package was renamed, so the whole test file failed to
collect.

**Prompt.** Implement the quiz with strict grading that rejects invalid choices
rather than counting them as wrong answers.

**Verification.** Derived each question's correct option by exercising the rule
it asks about — the unassigned guard, the priority boundary, the resolved lock,
note length, the boolean rejection, and the atomic save — then required the
stored answer key to match all six, rather than grading the key against itself.
Submitted an out-of-range choice and confirmed it was flagged invalid instead of
being counted as a wrong answer, and confirmed answers are accepted case- and
whitespace-insensitively.

**Decision.** Treat a choice outside A–D as invalid and record it separately
from an incorrect answer, so the result distinguishes "did not know" from "gave
a value that is not an option".

### Engineer A — Cycle 3: Validating values, not just field names

**Original gap.** Cycle 1's validation stopped at structure: nine field names
and a unique ID. A record with an illegal `status`, a boolean `affected_users`,
or a note with no author loaded cleanly and then behaved as a live ticket in a
state the application could neither produce nor leave. `design-decisions.md` §3
argued this was correct — that deciding legal values belongs to the manager, not
the storage layer.

**Prompt.** Validate the values inside each loaded record, and check the notes
inside each ticket.

**Verification.** Wrote records by hand with one field broken at a time — an
illegal status, an uncanonical category, a boolean user count, a note missing
its author, two notes sharing an ID — and confirmed each was rejected whole.
Then wrote the same record with a legitimate `priority` contradiction fixed and
confirmed it loaded, which is what shows the rejection came from the
contradiction rather than from a neighbouring field.

**Decision.** Reversed the §3 argument and rewrote the section to record the
reversal, because the old reasoning is why the gap survived the review that
found the related defect. The one rule that cannot be decided inside `storage`
is `priority`, which is derived; rather than copy the four-branch rule or import
`models` back into `storage` (a cycle), `StorageManager` takes an optional
`priority_rule` callable and `TicketManager` passes its own method in.

### Engineer B — Cycle 3: The queue, the report, and the quiz

**Original gap.** Three separate misses against the sprint brief. The work queue
included `in_progress` tickets although it is the Open Work Queue. The report
had no category breakdown and no resolved count, so two required numbers had no
method behind them. And the quiz's six questions were about different rules from
the six the brief names — four required questions had no question behind them.

**Prompt.** Filter the queue to open tickets, add the missing report figures,
and rewrite the question bank to the six required topics.

**Verification.** Built tickets through all three states and confirmed the queue
held only the open one while the list still showed all three. Checked the
category breakdown against a fixture with two categories and the resolved count
against a resolved-and-reopened pair. For the quiz, wrote the key first and then
made `test_14` derive each letter by exercising the rule the question asks
about, so the key is checked rather than confirmed.

**Decision.** Set the answer key to whichever option describes the enforced
rule, never to a letter sequence. The sequence is what went wrong in D8: the
letters were chosen to satisfy a fixture and the questions were written around
them, which is how a question came to mark a refused transition as correct.
Writing the question first and the key from it removes the opportunity.

Set the queue filter to `open` only rather than adding a second method for
in-progress work, and checked that nothing became unreachable: in-progress
tickets are still listed, still match a status search, and are still counted in
the status breakdown. Only the queue drops them.

## Current Verification Checklist

Use this checklist when performing a project review. Mark items only after running the corresponding checks. The marks below record the most recent full review; clear them when starting the next one.

- [x] Run the full test suite and record the actual result. — 51 tests, `OK`. The suite grew from 38 to 51 with the queue filter, the report figures, the load-time value checks and the new menus: 9 model cases, 7 storage, 7 search and reporting, 1 quiz, 26 CLI and 1 entry-point. This run was made on `feat/22-search-and-insights` after rebasing onto `main` with the validation work merged, so it is the first run in which both engineers' changes are present together.
- [ ] Compile the application and test files. — **Cleared.** The previous pass reported no errors, but that was against the revision before the queue filter, the report figures and the load-time checks landed. Re-run `python3 -m compileall -q src tests` and record it here before ticking.
- [ ] Check the Git diff for whitespace errors. — **Cleared** for the same reason; the earlier `git diff --check` run predates this revision.
- [x] Test invalid ticket input and workflow transitions. — cases 2, 4, 6 and 14, plus the CLI workflow cases.
- [x] Test storage failures and state rollback. — case 13, including a save stubbed to fail for every mutator.
- [x] Verify installation and execution instructions. — the suite passes both from an uninstalled checkout and against `pip install -e .`.
- [x] Review documentation for unsupported claims. — D7, D10, D11 and D13 corrected; D16 closed. The third review reversed two of those corrections: `design-decisions.md` §3 previously defended the validation gap recorded as D19, and the quiz bank did not ask the questions D20 describes. Both documents now follow the code.

One item is not covered by anything above: the exit status of the `python3 main.py` menu itself, which is exercised only through its handlers rather than as a subprocess.

Example commands:

```bash
python3 -m unittest discover -s tests -v
python3 -m compileall -q src tests
git diff --check
```

## Reflection

The development of CampusFlow provides practical experience in Python, modular design, validation, testing, workflow enforcement, persistence, error handling, and version control.

The most important lesson is that working software should be supported by understandable design, repeatable tests, and honest documentation.

Future entries should record specific problems encountered, the reasoning behind a solution, the tests used to verify it, and any advice that was changed or rejected after review.
