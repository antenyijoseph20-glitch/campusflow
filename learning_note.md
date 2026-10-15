# CampusFlow — Learning Note

Supplementary notes for the Engineering Understanding Check (`campus_flow/quiz.py`)
and the concepts it covers. Intended as a revision sheet and as mentor
discussion material.

Run the quiz in Python:

```python
from campus_flow.quiz import EngineeringQuiz
score, results = EngineeringQuiz.grade_quiz({1: "B", 2: "C", 3: "B", 4: "C", 5: "C", 6: "B"})
print(score, "/", EngineeringQuiz.total_questions())
```

## Q1 — Unassigned tickets cannot start work

**Answer: B — no status; the ticket cannot advance while unassigned.**

A ticket that nobody owns must not enter `in_progress`. The guard lives in
`TicketManager.update_workflow`, so it applies no matter how the method is
called — not only through the CLI. Rejecting at the model layer is what makes
the rule testable and consistent.

*Discussion point:* why enforce this in the manager rather than the menu? If it
lived in the CLI, any other caller could bypass it.

## Q2 — Priority precedence

**Answer: C — high.**

The rule in `calculate_priority` is ordered:

| Condition | Priority |
|---|---|
| urgency `high` **and** users ≥ 10 | critical |
| urgency `high` **or** users ≥ 10 | high |
| urgency `medium` **or** users ≥ 3 | medium |
| otherwise | low |

`high` with 5 users fails the `critical` test (needs both) but satisfies the
second rule on urgency alone.

*Discussion point:* the order of the branches is the whole rule. Swapping the
first two would make `critical` unreachable — a good example of precedence bugs.

## Q3 — Resolved tickets are locked

**Answer: B — it must be explicitly reopened first.**

Once resolved, a ticket accepts no further assignment or notes. It returns to
work only through an explicit reopen to `open`. This prevents a closed ticket
from silently drifting back into active work.

*Discussion point:* what would go wrong without the lock? A note added weeks
later would change a record already reported as finished.

## Q4 — Booleans are not integers here

**Answer: C — rejected as a boolean.**

In Python `bool` is a subclass of `int`, so `True == 1` and `isinstance(True, int)`
is `True`. A naive `int(value) > 0` check would silently accept `True` as one
affected user. `create_ticket` therefore tests `isinstance(affected_users, bool)`
**before** any numeric conversion.

*Discussion point:* this is a good illustration of why validation order matters,
and of a genuine Python footgun rather than a hypothetical one.

## Q5 — Note length bounds

**Answer: C — 5 characters.**

`add_note` requires a message of 5 to 300 characters after stripping
whitespace, and a non-blank author. A rejected note does not consume a note ID,
because IDs are derived from the stored notes rather than a separate counter.

*Discussion point:* deriving the ID means no counter can fall out of sync with
the data — the trade-off is that deleting a note would allow an ID to be reused.

## Q6 — Atomic saves

**Answer: B — write a temp file, then `os.replace()`.**

`StorageManager.save_tickets` writes the whole document to `<path>.tmp` and then
atomically replaces the target. If the write fails midway, the original file is
untouched; the temp file is cleaned up. Writing straight over the live file
would risk leaving it truncated.

*Discussion point:* `os.replace` is atomic on the same filesystem, which is why
the temp file is created beside the target rather than in `/tmp`.

## Cross-cutting themes

- **Validate at the boundary.** Reject bad input at the edge, so bad data never
  reaches storage.
- **Enforce rules in the model.** The CLI is one caller among possible others.
- **A save can fail.** Mutations record the previous value and restore it when
  persistence fails, keeping memory consistent with disk.
- **Tests must call real code.** A test that re-implements the logic it claims
  to verify passes whether or not the feature exists. See D4 in
  `baseline-check.md`.

## Mentor discussion questions

1. The two original `TicketManager` implementations had incompatible APIs — one
   returned `(bool, message)` tuples, the other raised exceptions. Which
   contract would you choose for a new project, and why?
2. Should a rejected note consume a note ID? What breaks in each design?
3. `resolution_percentage` returns `0.0` for an empty dataset. Is `0.0` or
   `None` the more honest value for "no tickets yet"?
4. What would change if two users ran CampusFlow against the same JSON file?
5. Which of these rules belong in a database constraint rather than in Python?
