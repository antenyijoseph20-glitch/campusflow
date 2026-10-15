from campus_flow.models import TicketManager
from campus_flow.quiz import EngineeringQuiz
from campus_flow.search_reports import TicketReports, TicketSearch, sort_by_priority


class CLI:
    """Command-line interface for CampusFlow.

    Talks to the dict-based TicketManager: mutations return ``(success, message)``
    tuples, and tickets are plain dicts.
    """

    def __init__(self, filepath="tickets.json"):
        self.manager = TicketManager(filepath)

    # ---------- helpers ----------

    @staticmethod
    def _ask(prompt):
        """Return stripped input, re-prompting until it is non-empty."""
        while True:
            value = input(prompt).strip()
            if value:
                return value
            print("Error: This field cannot be empty.")

    def _ask_optional(self, prompt):
        value = input(prompt).strip()
        return value or None

    def _report(self, result):
        """Print a (success, message) tuple and return the success flag."""
        success, message = result
        print(message)
        return success

    def _print_table(self, rows, headers):
        widths = [
            max(len(str(headers[i])), *(len(str(r[i])) for r in rows)) if rows else len(headers[i])
            for i in range(len(headers))
        ]
        line = " | ".join(str(h).ljust(widths[i]) for i, h in enumerate(headers))
        print(line)
        print("-" * len(line))
        for row in rows:
            print(" | ".join(str(c).ljust(widths[i]) for i, c in enumerate(row)))

    # ---------- menu ----------

    def run(self):
        print("=" * 42)
        print("          Welcome to CampusFlow")
        print("   IT Support Ticket & Workflow Manager")
        print("=" * 42)

        actions = {
            "1": self._handle_create,
            "2": self._handle_list,
            "3": self._handle_view,
            "4": self._handle_assign,
            "5": self._handle_workflow,
            "6": self._handle_add_note,
            "7": self._handle_view_notes,
            "8": self._handle_search,
            "9": self._handle_sorted_search,
            "10": self._handle_work_queue,
            "11": self._handle_reports,
            "12": self._handle_quiz,
        }

        while True:
            print("\n--- MAIN MENU ---")
            print("1. Create Ticket")
            print("2. List All Tickets")
            print("3. View Ticket Details")
            print("4. Assign Ticket")
            print("5. Update Ticket Status (Workflow)")
            print("6. Add Note to Ticket")
            print("7. View Ticket Notes")
            print("8. Search Tickets")
            print("9. Search Tickets Sorted by Priority")
            print("10. View Open Work Queue")
            print("11. Generate Reports")
            print("12. Engineering Understanding Check")
            print("13. Exit")

            choice = input("Select an option (1-13): ").strip()

            if choice == "13":
                print("Exiting CampusFlow. Goodbye!")
                return

            handler = actions.get(choice)
            if not handler:
                print("Error: Invalid choice. Please enter a number between 1 and 13.")
                continue

            try:
                handler()
            except (KeyboardInterrupt, EOFError):
                print("\nExiting CampusFlow. Goodbye!")
                return

    # ---------- handlers ----------

    def _handle_create(self):
        print("\n--- Create New Ticket ---")
        title = self._ask("Enter ticket title: ")
        print("Categories: Network, Hardware, Software, Other")
        category = self._ask("Enter category: ")
        print("Urgency levels: low, medium, high")
        urgency = self._ask("Enter urgency: ")
        affected_users = self._ask("Enter affected users (positive integer): ")

        self._report(
            self.manager.create_ticket(title, category, urgency, affected_users)
        )

    def _handle_list(self):
        tickets = self.manager.list_all_tickets()
        if not tickets:
            print("\nNo tickets found in the system.")
            return

        rows = [
            (t["id"], t["status"], t["priority"], t["category"], t["title"])
            for t in tickets
        ]
        print(f"\n--- All Tickets ({len(tickets)}) ---")
        self._print_table(rows, ("ID", "STATUS", "PRIORITY", "CATEGORY", "TITLE"))

    def _handle_view(self):
        ticket = self.manager.get_ticket(self._ask("Enter Ticket ID (e.g. T001): "))
        if not ticket:
            print("Error: Ticket not found.")
            return

        print(f"\n--- Ticket Details [{ticket['id']}] ---")
        print(f"Title          : {ticket['title']}")
        print(f"Category       : {ticket['category']}")
        print(f"Urgency        : {ticket['urgency']}")
        print(f"Affected Users : {ticket['affected_users']}")
        print(f"Priority       : {ticket['priority']}")
        print(f"Status         : {ticket['status']}")
        print(f"Assigned To    : {ticket['assigned_to'] or 'Unassigned'}")

        notes = ticket.get("notes", [])
        if notes:
            print(f"\nNotes ({len(notes)}):")
            for note in notes:
                print(f"  [{note['note_id']}] {note['author']}: {note['message']}")
        else:
            print("\nNotes          : none")

    def _handle_assign(self):
        ticket_id = self._ask("Enter Ticket ID to assign: ")
        staff = self._ask("Enter staff member name: ")
        self._report(self.manager.assign_ticket(ticket_id, staff))

    def _handle_workflow(self):
        ticket_id = self._ask("Enter Ticket ID: ")
        ticket = self.manager.get_ticket(ticket_id)
        if not ticket:
            print("Error: Ticket not found.")
            return

        print(f"Current Status: {ticket['status']}")

        if ticket["status"] == "resolved":
            if input("Ticket is resolved. Reopen it? (y/n): ").strip().lower() != "y":
                print("Operation cancelled.")
                return
            self._report(self.manager.update_workflow(ticket_id, "open"))
            return

        # The workflow only advances one step at a time: open -> in_progress ->
        # resolved. From open the only target is in_progress, and that requires
        # an assignee.
        allowed = ["in_progress"] if ticket["status"] == "open" else ["resolved"]
        if ticket["assigned_to"] is None:
            print("Note: this ticket is unassigned; assign it before moving to in_progress.")
        print(f"Allowed target statuses: {', '.join(allowed)}")
        self._report(self.manager.update_workflow(ticket_id, self._ask("Enter target status: ")))

    def _handle_add_note(self):
        ticket_id = self._ask("Enter Ticket ID: ")
        author = self._ask("Enter note author: ")
        message = self._ask("Enter note message: ")
        self._report(self.manager.add_note(ticket_id, author, message))

    def _handle_search(self):
        """Search with optional filters, presented in the order found."""
        results = self._search_interactively()
        if results is None:
            return
        self._print_tickets(results, "Match(es)")

    def _handle_sorted_search(self):
        """The same search, presented by priority weight then ticket ID."""
        results = self._search_interactively()
        if results is None:
            return
        self._print_tickets(
            sort_by_priority(results), "Match(es), sorted by priority then ID"
        )

    def _search_interactively(self):
        """Prompt for the optional filters. Returns matches, or None on error.

        Both search views share this so the filters they offer cannot drift
        apart, and so an unknown filter name is reported in one place.
        """
        print("\n--- Search Tickets ---")
        print("Press Enter to skip any filter.")
        query = self._ask_optional("Title contains: ")
        category = self._ask_optional("Category: ")
        status = self._ask_optional("Status (open/in_progress/resolved): ")
        priority = self._ask_optional("Priority (critical/high/medium/low): ")

        try:
            return TicketSearch.search(
                self.manager.list_all_tickets(),
                query=query,
                category=category,
                status=status,
                priority=priority,
            )
        except ValueError as error:
            print(f"Error: {error}")
            return None

    def _print_tickets(self, tickets, label):
        """Render a ticket list, or say so when there is nothing to render."""
        if not tickets:
            print("\nNo tickets matched those filters.")
            return

        rows = [
            (
                t["id"],
                t["status"],
                t["priority"],
                t["category"],
                t["assigned_to"] or "Unassigned",
                t["title"],
            )
            for t in tickets
        ]
        print(f"\n--- {len(tickets)} {label} ---")
        self._print_table(
            rows, ("ID", "STATUS", "PRIORITY", "CATEGORY", "ASSIGNED", "TITLE")
        )

    def _handle_view_notes(self):
        ticket = self.manager.get_ticket(self._ask("Enter Ticket ID (e.g. T001): "))
        if not ticket:
            print("Error: Ticket not found.")
            return

        notes = ticket.get("notes", [])
        print(f"\n--- Notes for {ticket['id']} ({len(notes)}) ---")
        if not notes:
            print("No notes recorded for this ticket.")
            return

        for note in notes:
            print(f"[{note['note_id']}] {note['author']}: {note['message']}")

    def _handle_work_queue(self):
        queue = self.manager.get_work_queue()
        if not queue:
            print("\nOpen Work Queue is empty (no tickets are waiting to be picked up).")
            return

        rows = [
            (t["id"], t["priority"], t["status"], t["assigned_to"] or "Unassigned", t["title"])
            for t in queue
        ]
        print(f"\n--- Open Work Queue ({len(queue)}) ---")
        self._print_table(rows, ("ID", "PRIORITY", "STATUS", "ASSIGNED", "TITLE"))

    def _handle_reports(self):
        report = TicketReports(self.manager.list_all_tickets()).generate()

        print("\n--- CampusFlow System Report ---")
        print(f"Total Tickets : {report['total']}")
        print(f"Resolved      : {report['resolved']}")
        print(f"Unresolved    : {report['unresolved']}")
        print(f"Resolution    : {report['resolution_percentage']:.1f}%")

        print("\nStatus Breakdown:")
        for status, count in report["status_breakdown"].items():
            print(f"  - {status}: {count}")

        print("\nCategory Breakdown:")
        for category, count in report["category_breakdown"].items():
            print(f"  - {category}: {count}")

        print("\nPriority Breakdown:")
        for priority, count in report["priority_breakdown"].items():
            print(f"  - {priority}: {count}")

    def _handle_quiz(self):
        """Run the Engineering Understanding Check interactively.

        A choice outside A-D is refused and re-prompted rather than counted as
        a wrong answer, so the score distinguishes "did not know" from "typed
        something that is not an option".
        """
        questions = EngineeringQuiz.QUESTIONS
        print("\n--- Engineering Understanding Check ---")
        print(f"{len(questions)} questions. Answer each with A, B, C or D.")

        answers = {}
        for number in sorted(questions):
            entry = questions[number]
            print(f"\nQ{number}. {entry['question']}")
            for letter, text in entry["options"].items():
                print(f"   {letter}) {text}")

            while True:
                raw = input("Your answer (A-D): ").strip().upper()
                if EngineeringQuiz.is_valid_choice(raw):
                    answers[number] = raw
                    break
                print("Error: Please enter A, B, C or D.")

        score, results = EngineeringQuiz.grade_quiz(answers)
        total = EngineeringQuiz.total_questions()
        percentage = (score / total * 100) if total else 0.0

        print(f"\nScore: {score}/{total} ({percentage:.0f}%)")
        for result in results:
            verdict = (
                "correct"
                if result["correct"]
                else f"incorrect (correct answer: {result['expected']})"
            )
            print(f"  Q{result['question']}: {result['choice']} - {verdict}")


def main():
    CLI().run()


if __name__ == "__main__":
    main()
