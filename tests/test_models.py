"""Rules enforced by ``campus_flow.models.TicketManager``.

Covers required verification cases 1-7: priority precedence, the workflow
guards, field validation, and note handling.
"""

try:  # discovery run from tests/ (the documented command)
    from base import CampusFlowTestCase
except ImportError:  # discovery run from the repository root
    from tests.base import CampusFlowTestCase


class TestModels(CampusFlowTestCase):
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

    def test_work_queue_holds_only_open_tickets(self):
        """The queue is what still needs picking up, so in_progress has left it."""
        self.manager.create_ticket("Waiting", "Other", "low", 1)
        self.manager.create_ticket("Started", "Network", "high", 15)
        self.manager.create_ticket("Finished", "Hardware", "medium", 3)

        # T002 goes in_progress, T003 goes all the way to resolved.
        self.manager.assign_ticket("T002", "Alice")
        self.manager.update_workflow("T002", "in_progress")
        self.manager.assign_ticket("T003", "Bob")
        self.manager.update_workflow("T003", "in_progress")
        self.manager.update_workflow("T003", "resolved")

        queue = self.manager.get_work_queue()

        self.assertEqual([t["id"] for t in queue], ["T001"])
        self.assertEqual(queue[0]["status"], "open")
        # Both tickets still exist and are still reported; only the queue drops
        # them, so nothing became invisible.
        self.assertEqual(len(self.manager.list_all_tickets()), 3)

    def test_work_queue_orders_by_priority_then_numeric_id(self):
        """Numeric, not textual, ID order: T010 sorts after T009, not after T001."""
        for number in range(1, 11):
            # Urgency low and one user keeps every ticket at 'low' priority, so
            # the tie-break on ID is what is under test.
            self.manager.create_ticket(f"Ticket {number}", "Other", "low", 1)
        self.manager.create_ticket("Critical one", "Network", "high", 15)

        queue = self.manager.get_work_queue()

        # The critical ticket is first despite being created last.
        self.assertEqual(queue[0]["id"], "T011")
        self.assertEqual(
            [t["id"] for t in queue[1:]],
            [f"T{n:03d}" for n in range(1, 11)],
        )
