import json
import os
import shutil
import tempfile
import unittest

from campus_flow.models import TicketManager


class TestCampusFlowNext(unittest.TestCase):
    """CampusFlow verification suite — validation, workflow, notes, and persistence."""

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

    # 2. Unassigned open -> in_progress rejected with unchanged data
    def test_02_unassigned_in_progress_guard(self):
        self.manager.create_ticket("Wi-Fi down", "Network", "high", 15)
        tickets_before = [dict(t) for t in self.manager.list_all_tickets()]

        success, _ = self.manager.update_workflow("T001", "in_progress")
        self.assertFalse(success)
        self.assertEqual(self.manager.get_ticket("T001")["status"], "open")
        self.assertEqual(self.manager.list_all_tickets(), tickets_before)

    # 3. Resolved ticket assignment mutation rejected
    def test_03_resolved_assignment_mutation_rejected(self):
        self.manager.create_ticket("Laptop fix", "Hardware", "medium", 2)
        self.manager.assign_ticket("T001", "Alice")
        self.manager.update_workflow("T001", "in_progress")
        self.manager.update_workflow("T001", "resolved")

        success, _ = self.manager.assign_ticket("T001", "Bob")
        self.assertFalse(success)
        self.assertEqual(self.manager.get_ticket("T001")["assigned_to"], "Alice")

    # 4. Invalid affected_users (0, negative, float, boolean) rejected
    def test_04_invalid_affected_users_rejection(self):
        for bad_val in [0, -5, 3.5, True, False, "ten"]:
            success, _ = self.manager.create_ticket("Test", "Software", "low", bad_val)
            self.assertFalse(success, f"Failed to reject invalid affected_users: {bad_val}")
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
        # consistent with what is on disk. Each mutator restores the value it
        # replaced.
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


if __name__ == "__main__":
    unittest.main()
