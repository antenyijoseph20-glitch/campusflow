"""Command-line behaviour from ``campus_flow.cli``.

These cases sit outside the 16-case contract: they cover the menu layer, which
had no tests at all. The interactive surface is exercised by patching
``builtins.input`` with a fixed sequence of answers and capturing stdout, so
each handler runs its real code path rather than a stubbed one.

The workflow cases are deliberately paired. The menu advertises only the legal
next status, and the model refuses an illegal one regardless -- the same rule
tested twice, once at each layer, because the CLI is not where the rule lives.
"""

try:  # discovery run from tests/ (the documented command)
    from base import CampusFlowTestCase
except ImportError:  # discovery run from the repository root
    from tests.base import CampusFlowTestCase

import io
from contextlib import redirect_stdout
from unittest import mock

from campus_flow.cli import CLI
from campus_flow.quiz import EngineeringQuiz


class TestCLI(CampusFlowTestCase):
    def make_cli(self):
        """A CLI over this test's file. Use ``cli.manager`` for setup.

        The CLI builds its own manager, so state must be created through it --
        a manager built separately would hold a stale in-memory copy.
        """
        return CLI(filepath=self.test_file)

    def run_with_input(self, answers, func, *args):
        """Call ``func`` with ``input()`` fed from ``answers``; return stdout.

        ``side_effect`` raises StopIteration if the handler asks for more input
        than provided, so an unexpected extra prompt fails the test instead of
        silently reading an empty string.

        The input mock is left on ``self.input_mock`` afterwards. A prompt string
        is passed to ``input()``, not printed, so once input is patched it does
        not appear in the captured stdout -- check it through the mock instead.
        """
        buffer = io.StringIO()
        with mock.patch("builtins.input", side_effect=list(answers)) as fake_input:
            self.input_mock = fake_input
            with redirect_stdout(buffer):
                func(*args)
        return buffer.getvalue()

    # ---------- input helpers ----------

    def test_ask_reprompts_until_the_answer_is_non_empty(self):
        cli = self.make_cli()
        buffer = io.StringIO()
        with mock.patch("builtins.input", side_effect=["", "   ", "Wi-Fi down"]):
            with redirect_stdout(buffer):
                answer = cli._ask("Title: ")

        self.assertEqual(answer, "Wi-Fi down")
        # Two blanks were rejected before the usable answer arrived.
        self.assertEqual(buffer.getvalue().count("cannot be empty"), 2)

    def test_ask_returns_the_stripped_answer(self):
        cli = self.make_cli()
        with mock.patch("builtins.input", return_value="  spaced  "):
            self.assertEqual(cli._ask("prompt"), "spaced")

    def test_ask_optional_treats_blank_as_none(self):
        cli = self.make_cli()
        with mock.patch("builtins.input", return_value="   "):
            self.assertIsNone(cli._ask_optional("Category: "))
        with mock.patch("builtins.input", return_value=" Network "):
            self.assertEqual(cli._ask_optional("Category: "), "Network")

    def test_report_prints_the_message_and_returns_the_flag(self):
        cli = self.make_cli()
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            self.assertTrue(cli._report((True, "done")))
            self.assertFalse(cli._report((False, "rejected")))
        self.assertIn("done", buffer.getvalue())
        self.assertIn("rejected", buffer.getvalue())

    def test_print_table_survives_no_rows_and_non_string_cells(self):
        cli = self.make_cli()

        empty = self.run_with_input([], cli._print_table, [], ("ID", "TITLE"))
        self.assertIn("ID | TITLE", empty)

        # Widths are computed with len(str(cell)), so ints and None must not
        # raise -- a ticket's assigned_to is None until it is assigned.
        rows = self.run_with_input(
            [], cli._print_table, [(1, None), (22, "longer title")], ("ID", "TITLE")
        )
        self.assertIn("22", rows)
        self.assertIn("longer title", rows)

    # ---------- workflow ----------

    def test_workflow_on_open_ticket_offers_only_in_progress(self):
        cli = self.make_cli()
        cli.manager.create_ticket("Wi-Fi down", "Network", "high", 15)

        output = self.run_with_input(["T001", "in_progress"], cli._handle_workflow)

        self.assertIn("Current Status: open", output)
        self.assertIn("Allowed target statuses: in_progress", output)
        # Unassigned, so the menu says so and the model refuses the move.
        self.assertIn("unassigned", output)
        self.assertIn("Cannot move an unassigned ticket", output)
        self.assertEqual(cli.manager.get_ticket("T001")["status"], "open")

    def test_workflow_cannot_skip_to_resolved_even_if_the_user_types_it(self):
        cli = self.make_cli()
        cli.manager.create_ticket("Wi-Fi down", "Network", "high", 15)
        cli.manager.assign_ticket("T001", "Alice")

        # The menu offers in_progress only, but typing "resolved" anyway must
        # still be refused by the manager rather than by the menu.
        output = self.run_with_input(["T001", "resolved"], cli._handle_workflow)

        self.assertIn("must be in_progress before it can be resolved", output)
        self.assertEqual(cli.manager.get_ticket("T001")["status"], "open")

    def test_workflow_on_resolved_ticket_cancels_when_reopen_is_declined(self):
        cli = self.make_cli()
        cli.manager.create_ticket("Laptop", "Hardware", "medium", 2)
        cli.manager.assign_ticket("T001", "Alice")
        cli.manager.update_workflow("T001", "in_progress")
        cli.manager.update_workflow("T001", "resolved")

        output = self.run_with_input(["T001", "n"], cli._handle_workflow)

        self.assertIn("Current Status: resolved", output)
        self.assertIn("Operation cancelled.", output)
        # The prompt is passed to input() rather than printed, so it is absent
        # from the captured output. Assert it was shown by reading the mock.
        self.assertEqual(
            self.input_mock.call_args[0][0],
            "Ticket is resolved. Reopen it? (y/n): ",
        )
        self.assertEqual(cli.manager.get_ticket("T001")["status"], "resolved")

    def test_workflow_on_resolved_ticket_reopens_when_confirmed(self):
        cli = self.make_cli()
        cli.manager.create_ticket("Laptop", "Hardware", "medium", 2)
        cli.manager.assign_ticket("T001", "Alice")
        cli.manager.update_workflow("T001", "in_progress")
        cli.manager.update_workflow("T001", "resolved")

        output = self.run_with_input(["T001", "Y"], cli._handle_workflow)

        self.assertIn("updated to 'open'", output)
        self.assertEqual(cli.manager.get_ticket("T001")["status"], "open")

    def test_workflow_on_a_missing_ticket_reports_rather_than_raising(self):
        cli = self.make_cli()
        output = self.run_with_input(["T999"], cli._handle_workflow)
        self.assertIn("Error: Ticket not found.", output)

    # ---------- other handlers ----------

    def test_create_ticket_through_the_menu(self):
        cli = self.make_cli()
        answers = ["Wi-Fi down in Block A", "network", "high", "15"]

        output = self.run_with_input(answers, cli._handle_create)

        # Category is normalised and the priority rule applies to the count.
        self.assertIn("Created ticket T001 with priority 'critical'", output)
        ticket = cli.manager.get_ticket("T001")
        self.assertEqual(ticket["category"], "Network")
        self.assertEqual(ticket["affected_users"], 15)

    def test_create_ticket_rejects_a_bad_user_count_without_raising(self):
        cli = self.make_cli()
        answers = ["Bad count", "Network", "low", "ten"]

        output = self.run_with_input(answers, cli._handle_create)

        self.assertIn("positive integer", output)
        self.assertEqual(cli.manager.list_all_tickets(), [])

    def test_view_reports_a_missing_ticket(self):
        cli = self.make_cli()
        output = self.run_with_input(["T999"], cli._handle_view)
        self.assertIn("Error: Ticket not found.", output)

    def test_view_shows_notes_and_unassigned_state(self):
        cli = self.make_cli()
        cli.manager.create_ticket("Printer", "Hardware", "medium", 5)
        cli.manager.add_note("T001", "Mentor A", "Replaced paper tray.")

        output = self.run_with_input(["T001"], cli._handle_view)

        self.assertIn("Assigned To    : Unassigned", output)
        self.assertIn("Notes (1):", output)
        self.assertIn("[N001] Mentor A: Replaced paper tray.", output)

    def test_list_on_an_empty_dataset(self):
        cli = self.make_cli()
        output = self.run_with_input([], cli._handle_list)
        self.assertIn("No tickets found in the system.", output)

    def test_search_reports_when_nothing_matches(self):
        cli = self.make_cli()
        cli.manager.create_ticket("Printer jam", "Hardware", "medium", 2)

        # query, category, status, priority -- only the query is filled in.
        output = self.run_with_input(["zzz", "", "", ""], cli._handle_search)

        self.assertIn("No tickets matched those filters.", output)

    def test_reports_on_an_empty_dataset_do_not_divide_by_zero(self):
        cli = self.make_cli()
        output = self.run_with_input([], cli._handle_reports)
        self.assertIn("Total Tickets : 0", output)
        self.assertIn("Resolution    : 0.0%", output)

    def test_reports_break_down_by_category_and_count_resolved(self):
        cli = self.make_cli()
        cli.manager.create_ticket("Printer jam", "Hardware", "medium", 2)
        cli.manager.create_ticket("Wi-Fi down", "Network", "high", 15)
        cli.manager.assign_ticket("T001", "Alice")
        cli.manager.update_workflow("T001", "in_progress")
        cli.manager.update_workflow("T001", "resolved")

        output = self.run_with_input([], cli._handle_reports)

        self.assertIn("Resolved      : 1", output)
        self.assertIn("Unresolved    : 1", output)
        self.assertIn("Resolution    : 50.0%", output)
        self.assertIn("Category Breakdown:", output)
        self.assertIn("- Hardware: 1", output)
        self.assertIn("- Network: 1", output)

    def test_work_queue_on_an_empty_dataset(self):
        cli = self.make_cli()
        output = self.run_with_input([], cli._handle_work_queue)
        self.assertIn("Work Queue is empty", output)

    def test_search_shows_the_assignee_of_each_match(self):
        cli = self.make_cli()
        cli.manager.create_ticket("Printer jam", "Hardware", "medium", 2)
        cli.manager.assign_ticket("T001", "Alice")

        output = self.run_with_input(["jam", "", "", ""], cli._handle_search)

        self.assertIn("ASSIGNED", output)
        self.assertIn("Alice", output)

    def test_sorted_search_presents_by_priority_then_id(self):
        cli = self.make_cli()
        # Two tickets whose creation order is the reverse of priority order.
        cli.manager.create_ticket("Low one", "Other", "low", 1)
        cli.manager.create_ticket("Urgent one", "Network", "high", 15)

        output = self.run_with_input(["one", "", "", ""], cli._handle_sorted_search)

        self.assertIn("sorted by priority then ID", output)
        self.assertLess(
            output.index("Urgent one"), output.index("Low one"),
            "the critical ticket must be listed above the low one",
        )

    def test_view_notes_lists_each_note_or_says_there_are_none(self):
        cli = self.make_cli()
        cli.manager.create_ticket("Printer", "Hardware", "medium", 5)

        empty = self.run_with_input(["T001"], cli._handle_view_notes)
        self.assertIn("No notes recorded for this ticket.", empty)

        cli.manager.add_note("T001", "Mentor A", "Replaced paper tray.")
        listed = self.run_with_input(["T001"], cli._handle_view_notes)
        self.assertIn("Notes for T001 (1)", listed)
        self.assertIn("[N001] Mentor A: Replaced paper tray.", listed)

    def test_quiz_reprompts_on_an_invalid_choice_then_scores(self):
        cli = self.make_cli()
        # Six questions. Answer the first wrongly, then retry it; the rest use
        # the stored key. Scoring the handler is what is under test here -- that
        # the key itself is right is test_quiz.py's job, where each letter is
        # derived by exercising the rule the question asks about.
        key = [
            EngineeringQuiz.QUESTIONS[n]["answer"]
            for n in sorted(EngineeringQuiz.QUESTIONS)
        ]
        wrong_first = "A" if key[0] != "A" else "B"
        answers = ["Z", wrong_first] + key[1:]

        output = self.run_with_input(answers, cli._handle_quiz)

        self.assertIn("Please enter A, B, C or D.", output)
        self.assertIn(f"Score: 5/{len(key)} (83%)", output)

    # ---------- the menu loop ----------

    def test_run_exits_on_choice_thirteen(self):
        cli = self.make_cli()
        output = self.run_with_input(["13"], cli.run)
        self.assertIn("Welcome to CampusFlow", output)
        self.assertIn("Exiting CampusFlow. Goodbye!", output)

    def test_run_rejects_an_invalid_choice_and_keeps_going(self):
        cli = self.make_cli()
        output = self.run_with_input(["99", "13"], cli.run)

        self.assertIn("Invalid choice", output)
        self.assertIn("Exiting CampusFlow. Goodbye!", output)

    def test_run_dispatches_a_menu_option_to_its_handler(self):
        cli = self.make_cli()
        cli.manager.create_ticket("Printer jam", "Hardware", "medium", 2)

        # Choose 2 (list), then exit.
        output = self.run_with_input(["2", "13"], cli.run)

        self.assertIn("--- All Tickets (1) ---", output)
        self.assertIn("Printer jam", output)
