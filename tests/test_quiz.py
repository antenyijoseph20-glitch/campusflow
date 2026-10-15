"""The Engineering Understanding Check in ``campus_flow.quiz``.

Covers required verification case 14. The answer key is checked against the
behaviour the code enforces, not against itself -- see D8 and D16 in
baseline-check.md.
"""

try:  # discovery run from tests/ (the documented command)
    from base import CampusFlowTestCase
except ImportError:  # discovery run from the repository root
    from tests.base import CampusFlowTestCase

import json

from campus_flow.quiz import EngineeringQuiz
from campus_flow.search_reports import TicketReports, TicketSearch


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

        # Q1: an open, unassigned ticket cannot move to in_progress. The reason
        # is asserted too, so this cannot pass merely because the ticket was
        # missing.
        created, message = self.manager.create_ticket("Unassigned", "Network", "low", 1)
        self.assertTrue(created, message)
        advanced, reason = self.manager.update_workflow("T001", "in_progress")
        self.assertFalse(advanced)
        self.assertIn("assigned", reason.lower())

        # Q2: an empty dataset reports 0.0 rather than dividing by zero.
        empty_report = TicketReports([])
        self.assertEqual(empty_report.total, 0)
        self.assertEqual(empty_report.resolution_percentage(), 0.0)

        # Q3: filters combine with strict AND. A query the ticket matches plus a
        # category the ticket fails returns nothing, where an OR would return it.
        reportable = self.manager.list_all_tickets()
        self.assertEqual(
            len(TicketSearch.search(reportable, query="Unassigned")), 1
        )
        self.assertEqual(
            TicketSearch.search(reportable, query="Unassigned", category="Hardware"),
            [],
        )

        # Q4: a resolved ticket refuses a new note until it is reopened.
        assigned, reason = self.manager.assign_ticket("T001", "Dev")
        self.assertTrue(assigned, reason)
        started, reason = self.manager.update_workflow("T001", "in_progress")
        self.assertTrue(started, reason)
        closed, reason = self.manager.update_workflow("T001", "resolved")
        self.assertTrue(closed, reason)

        refused, reason = self.manager.add_note("T001", "Dev", "A new note.")
        self.assertFalse(refused)
        self.assertIn("resolved", reason.lower())

        # Q5: a file holding two records with the same ID is rejected whole, so
        # the manager starts empty rather than exposing the duplicates.
        duplicate = [
            {
                "id": "T001",
                "title": "First",
                "category": "Network",
                "urgency": "low",
                "affected_users": 1,
                "priority": "low",
                "status": "open",
                "assigned_to": None,
                "notes": [],
            },
            {
                "id": "T001",
                "title": "Second",
                "category": "Network",
                "urgency": "low",
                "affected_users": 1,
                "priority": "low",
                "status": "open",
                "assigned_to": None,
                "notes": [],
            },
        ]
        with open(self.test_file, "w", encoding="utf-8") as handle:
            json.dump(duplicate, handle)
        self.assertEqual(self.reload_manager().list_all_tickets(), [])

        # Q6 is about review practice rather than a code path, so it is grounded
        # in reasoning: the `assertFalse` above is what makes the unassigned
        # guard observable. Delete the guard and that assertion fails; delete
        # the assertion and the guard could be removed without the suite
        # noticing. A suite that only ever asserts success has the second shape.

        # Now translate those rules into the letters they are described by, and
        # require the stored key to agree with all six.
        derived = {
            1: self._letter_matching_text(1, lambda t: "before work can start" in t),
            2: self._letter_matching_text(2, lambda t: t == "0.0"),
            3: self._letter_matching_text(3, lambda t: "with and" in t),
            4: self._letter_matching_text(4, lambda t: "cannot accept new notes" in t),
            5: self._letter_matching_text(5, lambda t: "rejects the whole file" in t),
            6: self._letter_matching_text(6, lambda t: "cannot fail" in t),
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
