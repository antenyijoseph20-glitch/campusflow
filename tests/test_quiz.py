"""The Engineering Understanding Check in ``campus_flow.quiz``.

Covers required verification case 14. The answer key is checked against the
behaviour the code enforces, not against itself -- see D8 and D16 in
baseline-check.md.
"""

try:  # discovery run from tests/ (the documented command)
    from base import CampusFlowTestCase
except ImportError:  # discovery run from the repository root
    from tests.base import CampusFlowTestCase

import inspect

from campus_flow.quiz import EngineeringQuiz
from campus_flow.storage import StorageManager


class TestQuiz(CampusFlowTestCase):
    def _letter_matching_text(self, number, predicate):
        """Return the one option letter for a question whose text matches.

        Answers are located by the option's wording, never by its position, so
        reordering a question's options cannot silently invalidate the key.
        """
        options = EngineeringQuiz.QUESTIONS[number]["options"]
        matches = [
            letter for letter, text in options.items() if predicate(text.lower())
        ]
        self.assertEqual(
            len(matches),
            1,
            f"question {number}: expected exactly one option to describe the "
            f"enforced rule, got {matches}",
        )
        return matches[0]

    # 14. CLI understanding check scoring
    def test_14_cli_understanding_check_scoring(self):
        # The answer key is validated against the behaviour this codebase
        # actually enforces -- see the rule checks below -- instead of being
        # graded against itself. The earlier version of this test handed the
        # grader the same letters that are stored as the key and asserted a full
        # score, so a wrong key passed in exactly the form that made D8 wrong
        # (baseline-check.md). Grounding each letter in an observable rule is
        # what makes this test able to fail.

        # Q1: an open, unassigned ticket cannot advance to any status. Each
        # guard below also pins the reason, so it cannot pass merely because
        # the ticket was missing.
        created, message = self.manager.create_ticket("Unassigned", "Network", "low", 1)
        self.assertTrue(created, message)
        advanced, reason = self.manager.update_workflow("T001", "in_progress")
        self.assertFalse(advanced)
        self.assertIn("unassigned", reason.lower())
        jumped, reason = self.manager.update_workflow("T001", "resolved")
        self.assertFalse(jumped)
        self.assertIn("in_progress", reason.lower())

        # Q2: urgency 'high' with 5 users is 'high' -- the 'critical' branch
        # needs 10 or more users, so this pins the boundary.
        created, message = self.manager.create_ticket("Priority", "Network", "high", 5)
        self.assertTrue(created, message)
        self.assertEqual(self.manager.get_ticket("T002")["priority"], "high")

        # Q5: a note message needs at least 5 characters.
        too_short, reason = self.manager.add_note("T002", "Dev", "abcd")
        self.assertFalse(too_short)
        self.assertIn("5 and 300", reason)
        long_enough, reason = self.manager.add_note("T002", "Dev", "abcde")
        self.assertTrue(long_enough, reason)

        # Q3: a resolved ticket rejects assignment and notes until it is
        # explicitly reopened. The setup steps are asserted in order rather
        # than collected into one tuple, so a failure stops here instead of
        # letting the guards below pass against a ticket that never closed.
        assigned, reason = self.manager.assign_ticket("T002", "Dev")
        self.assertTrue(assigned, reason)
        started, reason = self.manager.update_workflow("T002", "in_progress")
        self.assertTrue(started, reason)
        closed, reason = self.manager.update_workflow("T002", "resolved")
        self.assertTrue(closed, reason)
        self.assertEqual(self.manager.get_ticket("T002")["status"], "resolved")

        locked_assign, reason = self.manager.assign_ticket("T002", "Other")
        self.assertFalse(locked_assign)
        self.assertIn("resolved", reason.lower())
        locked_note, reason = self.manager.add_note("T002", "Dev", "blocked")
        self.assertFalse(locked_note)
        self.assertIn("resolved", reason.lower())

        reopened, reason = self.manager.update_workflow("T002", "open")
        self.assertTrue(reopened, reason)

        # Q4: bool is a subclass of int, so True is rejected rather than
        # silently counted as one user.
        boolean_users, reason = self.manager.create_ticket(
            "Bool", "Network", "low", True
        )
        self.assertFalse(boolean_users)
        self.assertIn("boolean", reason.lower())

        # Q6: the save path is a temporary file followed by os.replace().
        self.assertIn("os.replace", inspect.getsource(StorageManager.save_tickets))

        # Now translate those rules into the letters they are described by, and
        # require the stored key to agree with all six.
        derived = {
            1: self._letter_matching_text(1, lambda t: t.startswith("no status")),
            2: self._letter_matching_text(2, lambda t: t == "high"),
            3: self._letter_matching_text(3, lambda t: "reopened" in t),
            4: self._letter_matching_text(4, lambda t: t.startswith("rejected")),
            5: self._letter_matching_text(5, lambda t: t.startswith("5")),
            6: self._letter_matching_text(6, lambda t: "os.replace" in t),
        }
        key = {n: q["answer"] for n, q in EngineeringQuiz.QUESTIONS.items()}
        self.assertEqual(
            key,
            derived,
            "the stored answer key disagrees with the rules the code enforces",
        )

        # Grading behaviour, checked against a key that the assertions above
        # have just verified rather than assumed.
        score, results = EngineeringQuiz.grade_quiz(dict(key))
        self.assertEqual(score, 6)
        self.assertEqual(len(results), 6)
        self.assertTrue(all(r["correct"] for r in results))

        # Invalid choices are rejected rather than counted as wrong answers.
        self.assertFalse(EngineeringQuiz.is_valid_choice("Z"))
        self.assertFalse(EngineeringQuiz.is_valid_choice(""))

        score, results = EngineeringQuiz.grade_quiz({**key, 1: "Z"})
        self.assertEqual(score, 5)
        invalid = [r for r in results if not r["valid_choice"]]
        self.assertEqual(len(invalid), 1)
        self.assertEqual(invalid[0]["question"], 1)
        self.assertIsNone(invalid[0]["choice"])

        # Answers are case- and whitespace-insensitive.
        messy = {n: f" {c.lower()} " for n, c in key.items()}
        score, _ = EngineeringQuiz.grade_quiz(messy)
        self.assertEqual(score, 6)
