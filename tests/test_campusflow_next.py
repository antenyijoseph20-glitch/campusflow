import json
import os
import shutil
import tempfile
import unittest

from campus_flow.models import TicketManager
from campus_flow.quiz import EngineeringQuiz
from campus_flow.search_reports import TicketReports, TicketSearch


class TestCampusFlowNext(unittest.TestCase):
    """Unified test suite for CampusFlow Next covering all 16 required verification tests."""

    def setUp(self):
        # Each test gets an isolated directory so nothing lands in the repo root.
        self.tmpdir = tempfile.mkdtemp()
        self.test_file = os.path.join(self.tmpdir, "test_tickets.json")
        self.manager = TicketManager(filepath=self.test_file, silent_load=True)

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    # 1. Original priority calculation rule precedence
    def test_01_priority_rule_precedence(self):
        # critical: high urgency AND affected_users >= 10
        self.assertEqual(self.manager.calculate_priority("high", 10), "critical")
        # high: high urgency OR affected_users >= 10 (when not both)
        self.assertEqual(self.manager.calculate_priority("high", 5), "high")
        self.assertEqual(self.manager.calculate_priority("low", 12), "high")
        # medium: medium urgency OR affected_users >= 3
        self.assertEqual(self.manager.calculate_priority("medium", 2), "medium")
        self.assertEqual(self.manager.calculate_priority("low", 4), "medium")
        # low: otherwise
        self.assertEqual(self.manager.calculate_priority("low", 1), "low")

    # 2. Unassigned open -> in_progress rejected; a ticket cannot skip a step
    def test_02_unassigned_in_progress_guard(self):
        self.manager.create_ticket("Wi-Fi down", "Network", "high", 15)
        tickets_before = [dict(t) for t in self.manager.list_all_tickets()]

        success, _ = self.manager.update_workflow("T001", "in_progress")
        self.assertFalse(success)
        self.assertEqual(self.manager.get_ticket("T001")["status"], "open")
        self.assertEqual(self.manager.list_all_tickets(), tickets_before)

        # A ticket cannot jump straight to resolved: work must start first.
        success, _ = self.manager.update_workflow("T001", "resolved")
        self.assertFalse(success)
        self.assertEqual(self.manager.get_ticket("T001")["status"], "open")

        # Assigning removes the in_progress block but not the sequence rule.
        self.manager.assign_ticket("T001", "Alice")
        success, _ = self.manager.update_workflow("T001", "resolved")
        self.assertFalse(success)
        self.assertEqual(self.manager.get_ticket("T001")["status"], "open")

        # A non-string status is rejected, not raised.
        success, _ = self.manager.update_workflow("T001", None)
        self.assertFalse(success)

        # The one-step-at-a-time path still works end to end.
        success, _ = self.manager.update_workflow("T001", "in_progress")
        self.assertTrue(success)
        success, _ = self.manager.update_workflow("T001", "resolved")
        self.assertTrue(success)
        self.assertEqual(self.manager.get_ticket("T001")["status"], "resolved")

    # 3. Resolved ticket assignment mutation rejected
    def test_03_resolved_assignment_mutation_rejected(self):
        self.manager.create_ticket("Laptop fix", "Hardware", "medium", 2)
        self.manager.assign_ticket("T001", "Alice")
        self.manager.update_workflow("T001", "in_progress")
        self.manager.update_workflow("T001", "resolved")

        success, _ = self.manager.assign_ticket("T001", "Bob")
        self.assertFalse(success)
        self.assertEqual(self.manager.get_ticket("T001")["assigned_to"], "Alice")

    # 4. Invalid field values rejected, including non-string types
    def test_04_invalid_field_values_rejection(self):
        for bad_val in [0, -5, 3.5, True, False, "ten"]:
            success, _ = self.manager.create_ticket("Test", "Software", "low", bad_val)
            self.assertFalse(success, f"Failed to reject invalid affected_users: {bad_val}")

        # Non-string fields return a message rather than raising AttributeError.
        for bad_args in [
            (None, "Software", "low", 1),
            (123, "Software", "low", 1),
            ("Valid title", None, "low", 1),
            ("Valid title", "Software", None, 1),
        ]:
            success, _ = self.manager.create_ticket(*bad_args)
            self.assertFalse(success, f"Failed to reject non-string field: {bad_args}")

        # Nothing was created by any of the rejected attempts.
        self.assertEqual(self.manager.list_all_tickets(), [])

    # 5. Valid note added and note ID correct
    def test_05_valid_note_addition_and_id(self):
        self.manager.create_ticket("Printer broken", "Hardware", "medium", 5)
        success, _ = self.manager.add_note("T001", "Mentor A", "Replaced paper tray and tested.")
        self.assertTrue(success)

        ticket = self.manager.get_ticket("T001")
        self.assertEqual(len(ticket["notes"]), 1)
        self.assertEqual(ticket["notes"][0]["note_id"], "N001")
        self.assertEqual(ticket["notes"][0]["author"], "Mentor A")

    # 6. Blank/too-short note rejected without consuming ID
    def test_06_invalid_note_rejection_no_id_consumption(self):
        self.manager.create_ticket("App crash", "Software", "high", 8)
        # Too short (< 5 chars)
        success, _ = self.manager.add_note("T001", "Mentor B", "Fix")
        self.assertFalse(success)

        # Blank author
        success, _ = self.manager.add_note("T001", "", "Valid message length here.")
        self.assertFalse(success)

        # Blank/empty message
        success, _ = self.manager.add_note("T001", "Mentor B", "      ")
        self.assertFalse(success)

        # Verify no note ID was consumed
        ticket = self.manager.get_ticket("T001")
        self.assertEqual(len(ticket["notes"]), 0)

        # The next valid note still claims N001.
        self.manager.add_note("T001", "Mentor B", "This note is long enough.")
        self.assertEqual(self.manager.get_ticket("T001")["notes"][0]["note_id"], "N001")

    # 7. Note on resolved ticket rejected; note after reopen accepted
    def test_07_resolved_note_guard_and_reopen(self):
        self.manager.create_ticket("Key missing", "Hardware", "low", 1)
        self.manager.assign_ticket("T001", "Alice")
        self.manager.update_workflow("T001", "in_progress")
        self.manager.update_workflow("T001", "resolved")

        # Reject note on resolved ticket
        success, _ = self.manager.add_note("T001", "Alice", "Trying to add note after close.")
        self.assertFalse(success)

        # Reopen ticket
        self.manager.update_workflow("T001", "open")
        success, _ = self.manager.add_note("T001", "Alice", "Added note after reopening.")
        self.assertTrue(success)
        self.assertEqual(len(self.manager.get_ticket("T001")["notes"]), 1)

    # 8. Search title ignores case, matching substring
    def test_08_case_insensitive_substring_search(self):
        self.manager.create_ticket("Campus Wi-Fi Outage in Block A", "Network", "high", 20)
        self.manager.create_ticket("Printer jam in Library", "Hardware", "medium", 2)
        tickets = self.manager.list_all_tickets()

        # Lower-case query must match the mixed-case title.
        results = TicketSearch.search(tickets, query="wi-fi")
        self.assertEqual([t["id"] for t in results], ["T001"])

        # Upper-case query matches the same ticket.
        self.assertEqual(
            [t["id"] for t in TicketSearch.search(tickets, query="WI-FI")], ["T001"]
        )

        # A substring in the middle of the title also matches.
        self.assertEqual(
            [t["id"] for t in TicketSearch.search(tickets, query="outage")], ["T001"]
        )

        # A query matching nothing returns no results rather than raising.
        self.assertEqual(TicketSearch.search(tickets, query="nonexistent"), [])

    # 9. Combined search filters use AND
    def test_09_combined_search_filters_and(self):
        self.manager.create_ticket("Network switch error", "Network", "high", 15)
        self.manager.create_ticket("Network printer jam", "Hardware", "medium", 2)
        tickets = self.manager.list_all_tickets()

        # category=Network AND urgency=high -> only T001.
        results = TicketSearch.search(tickets, category="Network", urgency="high")
        self.assertEqual([t["id"] for t in results], ["T001"])

        # Adding a filter that T001 fails must empty the result set (strict AND).
        self.assertEqual(
            TicketSearch.search(tickets, category="Network", urgency="high", priority="low"),
            [],
        )

        # Category comparison is case-insensitive against the canonical value.
        # T002 is titled "Network printer jam" but its category is Hardware, so
        # only T001 matches the Network filter.
        self.assertEqual(
            [t["id"] for t in TicketSearch.search(tickets, category="network")],
            ["T001"],
        )

        # A title filter and a category filter combine with AND, not OR.
        self.assertEqual(
            TicketSearch.search(tickets, query="printer", category="Network"),
            [],
        )
        self.assertEqual(
            [t["id"] for t in TicketSearch.search(tickets, query="printer", category="Hardware")],
            ["T002"],
        )

        # An unknown filter name is reported, not silently ignored.
        with self.assertRaises(ValueError):
            TicketSearch.search(tickets, urgencyy="high")

    # 10. Empty report returns 0%, no crash
    def test_10_empty_report_safety(self):
        report = TicketReports(self.manager.list_all_tickets())

        self.assertEqual(report.total, 0)
        self.assertEqual(report.resolution_percentage(), 0.0)
        self.assertEqual(report.unresolved_count(), 0)

        # Every valid status is still reported, defaulting to zero.
        self.assertEqual(
            report.count_by_status(),
            {"open": 0, "in_progress": 0, "resolved": 0},
        )

        # generate() is safe on an empty fixture too.
        self.assertEqual(report.generate()["resolution_percentage"], 0.0)

    # 11. Report counts agree with known fixture after resolve/reopen
    def test_11_report_counts_fixture_sync(self):
        self.manager.create_ticket("T1", "Network", "high", 10)
        self.manager.create_ticket("T2", "Software", "low", 2)
        self.manager.assign_ticket("T001", "Alice")
        self.manager.update_workflow("T001", "in_progress")
        self.manager.update_workflow("T001", "resolved")

        report = TicketReports(self.manager.list_all_tickets())
        self.assertEqual(report.total, 2)
        self.assertEqual(report.count_by_status()["resolved"], 1)
        self.assertEqual(report.count_by_status()["open"], 1)
        self.assertEqual(report.resolution_percentage(), 50.0)

        # Reopening moves the ticket back and the report follows.
        self.manager.update_workflow("T001", "open")
        reopened = TicketReports(self.manager.list_all_tickets())
        self.assertEqual(reopened.count_by_status()["resolved"], 0)
        self.assertEqual(reopened.count_by_status()["open"], 2)
        self.assertEqual(reopened.resolution_percentage(), 0.0)

        # Report totals always agree with the live ticket list.
        self.assertEqual(reopened.total, len(self.manager.list_all_tickets()))

    # 12. Saving/loading preserves notes and next IDs
    def test_12_persistence_and_note_roundtrip(self):
        self.manager.create_ticket("Persist Notes", "Software", "medium", 5)
        self.manager.add_note("T001", "Bob", "Initial note recorded.")

        # Reload manager from same file
        manager_reloaded = TicketManager(filepath=self.test_file, silent_load=True)
        ticket = manager_reloaded.get_ticket("T001")
        self.assertEqual(len(ticket["notes"]), 1)
        self.assertEqual(ticket["notes"][0]["message"], "Initial note recorded.")

        # Test note ID continuity after reload
        manager_reloaded.add_note("T001", "Bob", "Second note recorded.")
        self.assertEqual(ticket["notes"][1]["note_id"], "N002")

        # Next ticket ID also continues after reload.
        manager_reloaded.create_ticket("Second ticket", "Network", "low", 1)
        self.assertIsNotNone(manager_reloaded.get_ticket("T002"))

    # 13. Corrupt JSON or duplicated ticket ID rejected without state loss
    def test_13_corrupt_json_or_duplicate_id_rejection(self):
        self.manager.create_ticket("Original", "Network", "low", 1)

        # Write duplicate ID JSON to file
        duplicate_data = [
            {"id": "T001", "title": "Dup 1", "category": "Network", "urgency": "low", "affected_users": 1, "priority": "low", "status": "open", "assigned_to": None, "notes": []},
            {"id": "T001", "title": "Dup 2", "category": "Network", "urgency": "low", "affected_users": 1, "priority": "low", "status": "open", "assigned_to": None, "notes": []}
        ]
        with open(self.test_file, "w", encoding="utf-8") as f:
            json.dump(duplicate_data, f)

        manager_reload = TicketManager(filepath=self.test_file, silent_load=True)
        # Should reject load due to duplicate ID, keeping active memory safe or empty rather than corrupting
        self.assertEqual(len(manager_reload.list_all_tickets()), 0)

        # Malformed JSON is rejected the same way.
        with open(self.test_file, "w", encoding="utf-8") as f:
            f.write("{not valid json")
        malformed = TicketManager(filepath=self.test_file, silent_load=True)
        self.assertEqual(malformed.list_all_tickets(), [])

        # A JSON root that is not a list is rejected.
        with open(self.test_file, "w", encoding="utf-8") as f:
            json.dump({"id": "T001"}, f)
        wrong_root = TicketManager(filepath=self.test_file, silent_load=True)
        self.assertEqual(wrong_root.list_all_tickets(), [])

        # A failed save must roll the in-memory change back, leaving memory
        # consistent with what is on disk (README: rollback on persistence
        # failure). Each mutator restores the value it replaced.
        manager = TicketManager(
            filepath=os.path.join(self.tmpdir, "fresh.json"), silent_load=True
        )
        manager.create_ticket("Keep me", "Network", "high", 15)
        manager.assign_ticket("T001", "Alice")

        # Persistence now fails for every subsequent write.
        manager.storage.save_tickets = lambda tickets: False

        # create_ticket removes the record it appended.
        success, _ = manager.create_ticket("Will not persist", "Network", "low", 1)
        self.assertFalse(success)
        self.assertEqual([t["id"] for t in manager.list_all_tickets()], ["T001"])

        # assign_ticket restores the previous assignee.
        success, _ = manager.assign_ticket("T001", "Bob")
        self.assertFalse(success)
        self.assertEqual(manager.get_ticket("T001")["assigned_to"], "Alice")

        # update_workflow restores the previous status.
        success, _ = manager.update_workflow("T001", "in_progress")
        self.assertFalse(success)
        self.assertEqual(manager.get_ticket("T001")["status"], "open")

        # add_note removes the note it appended.
        success, _ = manager.add_note("T001", "Alice", "This note will not persist.")
        self.assertFalse(success)
        self.assertEqual(manager.get_ticket("T001")["notes"], [])

    # 14. CLI understanding check scoring
    def test_14_cli_understanding_check_scoring(self):
        answers = {1: "B", 2: "C", 3: "B", 4: "C", 5: "C", 6: "B"}
        score, results = EngineeringQuiz.grade_quiz(answers)
        self.assertEqual(score, 6)
        self.assertEqual(len(results), 6)
        self.assertTrue(all(r["correct"] for r in results))

        # Invalid choices are rejected rather than counted as wrong answers.
        self.assertFalse(EngineeringQuiz.is_valid_choice("Z"))
        self.assertFalse(EngineeringQuiz.is_valid_choice(""))

        score, results = EngineeringQuiz.grade_quiz({1: "Z", 2: "C", 3: "B", 4: "C", 5: "C", 6: "B"})
        self.assertEqual(score, 5)
        invalid = [r for r in results if not r["valid_choice"]]
        self.assertEqual(len(invalid), 1)
        self.assertEqual(invalid[0]["question"], 1)
        self.assertIsNone(invalid[0]["choice"])

        # Answers are case- and whitespace-insensitive.
        score, _ = EngineeringQuiz.grade_quiz({1: " b ", 2: "c", 3: "B", 4: "C", 5: "C", 6: "B"})
        self.assertEqual(score, 6)

    # BUG-HUNTER A: Note ID continuity on reload
    def test_bug_hunter_a_note_id_continuity(self):
        self.manager.create_ticket("Bug A", "Hardware", "low", 2)
        self.manager.add_note("T001", "Dev", "Note one.")

        manager_2 = TicketManager(filepath=self.test_file, silent_load=True)
        manager_2.add_note("T001", "Dev", "Note two.")
        ticket = manager_2.get_ticket("T001")
        self.assertEqual(ticket["notes"][1]["note_id"], "N002")

    # BUG-HUNTER B: Filter case-normalization check
    def test_bug_hunter_b_category_case_normalization(self):
        self.manager.create_ticket("Case Test", "network", "high", 10)
        ticket = self.manager.get_ticket("T001")
        # Canonical normalization stores "Network" regardless of lowercase input "network"
        self.assertEqual(ticket["category"], "Network")

        # The stored canonical value is what search must match against.
        results = TicketSearch.search(self.manager.list_all_tickets(), category="NETWORK")
        self.assertEqual([t["id"] for t in results], ["T001"])


if __name__ == "__main__":
    unittest.main()
