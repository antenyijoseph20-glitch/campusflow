"""Persistence behaviour from ``campus_flow.storage``.

Covers required verification case 12 (round-trip), case 13 (rejection of
malformed files and rollback when a save fails), plus bug-hunter check A, which
guards note ID continuity across a reload.
"""

try:  # discovery run from tests/ (the documented command)
    from base import CampusFlowTestCase
except ImportError:  # discovery run from the repository root
    from tests.base import CampusFlowTestCase

import json


class TestStorage(CampusFlowTestCase):
    # 12. Saving/loading preserves notes and next IDs
    def test_12_persistence_and_note_roundtrip(self):
        self.manager.create_ticket("Persist Notes", "Software", "medium", 5)
        self.manager.add_note("T001", "Bob", "Initial note recorded.")

        # Reload manager from same file
        manager_reloaded = self.reload_manager()
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

        manager_reload = self.reload_manager()
        # Should reject load due to duplicate ID, keeping active memory safe or empty rather than corrupting
        self.assertEqual(len(manager_reload.list_all_tickets()), 0)

        # Malformed JSON is rejected the same way.
        with open(self.test_file, "w", encoding="utf-8") as f:
            f.write("{not valid json")
        malformed = self.reload_manager()
        self.assertEqual(malformed.list_all_tickets(), [])

        # A JSON root that is not a list is rejected.
        with open(self.test_file, "w", encoding="utf-8") as f:
            json.dump({"id": "T001"}, f)
        wrong_root = self.reload_manager()
        self.assertEqual(wrong_root.list_all_tickets(), [])

        # A record missing required fields is rejected rather than loaded and
        # then raising KeyError the first time the work queue reads it.
        with open(self.test_file, "w", encoding="utf-8") as f:
            json.dump([{"id": "T001", "title": "Incomplete"}], f)
        incomplete = self.reload_manager()
        self.assertEqual(incomplete.list_all_tickets(), [])
        self.assertEqual(incomplete.get_work_queue(), [])

        # A record whose value is not an object is rejected too.
        with open(self.test_file, "w", encoding="utf-8") as f:
            json.dump(["not-a-ticket"], f)
        not_an_object = self.reload_manager()
        self.assertEqual(not_an_object.list_all_tickets(), [])

        # A failed save must roll the in-memory change back, leaving memory
        # consistent with what is on disk (README: rollback on persistence
        # failure). Each mutator restores the value it replaced.
        manager = self.fresh_manager()
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

        manager_2 = self.reload_manager()
        manager_2.add_note("T001", "Dev", "Note two.")
        ticket = manager_2.get_ticket("T001")
        self.assertEqual(ticket["notes"][1]["note_id"], "N002")

    def write_record(self, **overrides):
        """Write one otherwise-valid record with the given fields replaced."""
        record = {
            "id": "T001",
            "title": "Baseline",
            "category": "Network",
            "urgency": "low",
            "affected_users": 1,
            "priority": "low",
            "status": "open",
            "assigned_to": None,
            "notes": [],
        }
        record.update(overrides)
        with open(self.test_file, "w", encoding="utf-8") as handle:
            json.dump([record], handle)
        return record

    def test_load_accepts_a_record_the_application_could_have_written(self):
        """The baseline the rejection cases below are measured against."""
        self.write_record()
        self.assertEqual(len(self.reload_manager().list_all_tickets()), 1)

    def test_load_rejects_values_the_application_cannot_produce(self):
        """Structure was already checked; this is the values inside it."""
        cases = {
            "illegal status": {"status": "finished"},
            "illegal category": {"category": "Printing"},
            "uncanonical category": {"category": "network"},
            "illegal urgency": {"urgency": "urgent"},
            "illegal priority": {"priority": "blocker"},
            "uppercase urgency": {"urgency": "LOW"},
            "blank title": {"title": "   "},
            "non-string title": {"title": 42},
            "zero users": {"affected_users": 0},
            "boolean users": {"affected_users": True},
            "users as text": {"affected_users": "1"},
            "blank assignee": {"assigned_to": "  "},
            "assignee is a number": {"assigned_to": 7},
            "notes not a list": {"notes": {}},
            "note is not an object": {"notes": ["N001"]},
            "note missing author": {
                "notes": [{"note_id": "N001", "message": "Long enough message."}]
            },
            "note message too short": {
                "notes": [{"note_id": "N001", "author": "Dev", "message": "hi"}]
            },
            "blank note author": {
                "notes": [{"note_id": "N001", "author": " ", "message": "Long enough."}]
            },
            "duplicate note ID": {
                "notes": [
                    {"note_id": "N001", "author": "Dev", "message": "First message."},
                    {"note_id": "N001", "author": "Dev", "message": "Second message."},
                ]
            },
        }

        for label, overrides in cases.items():
            with self.subTest(case=label):
                self.write_record(**overrides)
                self.assertEqual(
                    self.reload_manager().list_all_tickets(),
                    [],
                    f"a record with an {label} was loaded",
                )

    def test_load_rejects_a_priority_that_contradicts_its_own_inputs(self):
        """Priority is derived, so a stored value that disagrees is corrupt.

        Urgency 'high' with 15 users derives 'critical'; the rest of the record
        is valid, so only the derivation can cause the rejection.
        """
        self.write_record(urgency="high", affected_users=15, priority="low")
        self.assertEqual(self.reload_manager().list_all_tickets(), [])

        # The same inputs with the derived priority load cleanly, which shows
        # the rejection above came from the contradiction and not from the
        # urgency or the count.
        self.write_record(urgency="high", affected_users=15, priority="critical")
        self.assertEqual(len(self.reload_manager().list_all_tickets()), 1)

    def test_a_rejected_load_leaves_a_usable_manager(self):
        """Rejection starts empty rather than raising, and writes still work."""
        self.write_record(status="finished")

        manager = self.reload_manager()
        self.assertEqual(manager.list_all_tickets(), [])

        created, message = manager.create_ticket("Fresh start", "Other", "low", 1)
        self.assertTrue(created, message)
        self.assertEqual(len(self.reload_manager().list_all_tickets()), 1)
