# CampusFlow — Learning Note

Supplementary notes for the Engineering Understanding Check (`campus_flow/quiz.py`)
and the concepts it covers. Intended as a revision sheet and as mentor
discussion material.

Run the quiz in Python:

```python
from campus_flow.quiz import EngineeringQuiz
key = {n: q["answer"] for n, q in EngineeringQuiz.QUESTIONS.items()}
score, results = EngineeringQuiz.grade_quiz(key)
print(score, "/", EngineeringQuiz.total_questions())
```

Building the answers from the bank rather than typing them out is deliberate:
the letters in this file would otherwise be one more place for the key to drift
out of step with the questions.

The same check is available from the running application, as option 12 on the
main menu. There, a choice outside A–D is refused and re-prompted rather than
counted as a wrong answer, so the score distinguishes "did not know" from "typed
something that is not an option".

## Q1 — An unassigned ticket cannot start work

**Answer: B — the change is refused; a ticket must be assigned before work starts.**

An open, unassigned ticket has no legal target. `in_progress` is refused because
nobody owns it, and `resolved` is refused because the work has not started — and
even once assigned, `open` cannot jump straight to `resolved`. All of these
guards live in `TicketManager.update_workflow`, so they apply no matter how the
method is called, not only through the CLI.

*Discussion point:* why enforce this in the manager rather than the menu? If it
lived in the CLI, any other caller could bypass it.

## Q2 — An empty dataset reports 0.0, not an error

**Answer: C — 0.0.**

`TicketReports.resolution_percentage` returns `0.0` when there are no tickets at
all, before it divides anything. The guard is an early return rather than a
`try`/`except ZeroDivisionError`, so the empty case is a stated answer rather
than a caught accident.

*Discussion point:* is `0.0` the honest number for "nothing has happened yet"?
`None` would distinguish "no data" from "nothing resolved", at the cost of every
caller handling two types.

## Q3 — Every supplied filter must match

**Answer: B — nothing is returned; the filters combine with AND.**

`TicketSearch.matches` returns `False` as soon as any supplied filter fails, so
a title query the ticket matches cannot rescue it from a category it fails. The
filters are AND, never OR. An unrecognised filter *name* raises `ValueError`
instead of being ignored, so a typo is reported rather than silently returning
too many results.

*Discussion point:* which failure is worse for a search tool — too many results
or too few? Silent OR would give the first, silently ignoring a typo the second.

## Q4 — A resolved ticket accepts no new notes

**Answer: B — the call is refused.**

`add_note` accepts only `open` and `in_progress`. Once resolved, a ticket takes
no further notes and cannot be reassigned; it returns to work only through an
explicit reopen to `open`. The lock is what stops a record already reported as
finished from quietly changing afterwards.

*Discussion point:* the guard is on the status, not on the note's contents — why
is "this note is only a correction" not something the code can decide?

## Q5 — A duplicated ID rejects the whole file

**Answer: B — the file is rejected, so the manager starts empty.**

`load_tickets` returns `None` on the first problem and `TicketManager` then
starts from an empty list. It does not keep the first duplicate and drop the
second: a partially loaded file is harder to reason about than an explicit empty
start, and silently dropping a record would hide the corruption that caused it.
Because a rejected load starts empty, the next successful save writes that empty
list over the file — so a file worth keeping should be copied aside before
anything is changed.

*Discussion point:* the alternative is to load what is valid and report the
rest. What would that require of every caller?

## Q6 — A pull request with no failing test proves less than it appears to

**Answer: C — a suite that only covers the happy path cannot fail, so it cannot
show the feature is correct.**

A test that only asserts success passes whether the rule is implemented or not.
The negative case is what makes the rule observable: in this suite,
`assertFalse(update_workflow("T001", "in_progress"))` against an unassigned
ticket is what would fail if the unassigned guard were deleted. Remove the
assertion and the guard could be removed without the suite noticing — the same
shape as D4 and D8 in `baseline-check.md`, where tests passed while the feature
did not exist.

*Discussion point:* coverage percentages count lines executed, not outcomes
checked. Which of these two would you put in a review checklist, and why?

## Cross-cutting themes

- **Validate at the boundary.** Reject bad input at the edge, so bad data never
  reaches storage.
- **Enforce rules in the model.** The CLI is one caller among possible others.
- **A save can fail.** Mutations record the previous value and restore it when
  persistence fails, keeping memory consistent with disk.
- **Tests must call real code.** A test that re-implements the logic it claims
  to verify passes whether or not the feature exists. See D4 in
  `baseline-check.md`.
- **A test that grades a claim against itself cannot find the claim false.**
  The quiz key was originally the letters the fixture expected, so a question
  whose marked answer the system actually rejects still scored full marks. See
  D8.

## Mentor discussion questions

1. The two original `TicketManager` implementations had incompatible APIs — one
   returned `(bool, message)` tuples, the other raised exceptions. Which
   contract would you choose for a new project, and why?
2. Should a rejected note consume a note ID? What breaks in each design?
3. `resolution_percentage` returns `0.0` for an empty dataset. Is `0.0` or
   `None` the more honest value for "no tickets yet"?
4. What would change if two users ran CampusFlow against the same JSON file?
5. A rejected load starts empty, and the next save overwrites the file. Is that
   the right default, or should the application refuse to save until the file is
   dealt with?
6. Which of these rules belong in a database constraint rather than in Python?
