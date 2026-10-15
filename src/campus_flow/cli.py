from campus_flow.models import TicketManager
from campus_flow.search_reports import TicketReports, TicketSearch


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
            "7": self._handle_search,
            "8": self._handle_work_queue,
            "9": self._handle_reports,
        }

        while True:
            print("\n--- MAIN MENU ---")
            print("1. Create Ticket")
            print("2. List All Tickets")
            print("3. View Ticket Details")
            print("4. Assign Ticket")
            print("5. Update Ticket Status (Workflow)")
            print("6. Add Note to Ticket")
            print("7. Search Tickets")
            print("8. View Work Queue")
            print("9. Generate Reports")
            print("10. Exit")

            choice = input("Select an option (1-10): ").strip()

            if choice == "10":
                print("Exiting CampusFlow. Goodbye!")
                return

            handler = actions.get(choice)
            if not handler:
                print("Error: Invalid choice. Please enter a number between 1 and 10.")
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

        print("Allowed target statuses: in_progress, resolved")
        self._report(self.manager.update_workflow(ticket_id, self._ask("Enter target status: ")))

    def _handle_add_note(self):
        ticket_id = self._ask("Enter Ticket ID: ")
        author = self._ask("Enter note author: ")
        message = self._ask("Enter note message: ")
        self._report(self.manager.add_note(ticket_id, author, message))

    def _handle_search(self):
        print("\n--- Search Tickets ---")
        print("Press Enter to skip any filter.")
        query = self._ask_optional("Title contains: ")
        category = self._ask_optional("Category: ")
        status = self._ask_optional("Status (open/in_progress/resolved): ")
        priority = self._ask_optional("Priority (critical/high/medium/low): ")

        try:
            results = TicketSearch.search(
                self.manager.list_all_tickets(),
                query=query,
                category=category,
                status=status,
                priority=priority,
            )
        except ValueError as error:
            print(f"Error: {error}")
            return

        if not results:
            print("\nNo tickets matched those filters.")
            return

        rows = [
            (t["id"], t["status"], t["priority"], t["category"], t["title"])
            for t in results
        ]
        print(f"\n--- {len(results)} Match(es) ---")
        self._print_table(rows, ("ID", "STATUS", "PRIORITY", "CATEGORY", "TITLE"))

    def _handle_work_queue(self):
        queue = self.manager.get_work_queue()
        if not queue:
            print("\nWork Queue is empty (no open or in-progress tickets).")
            return

        rows = [
            (t["id"], t["priority"], t["status"], t["assigned_to"] or "Unassigned", t["title"])
            for t in queue
        ]
        print(f"\n--- Active Work Queue ({len(queue)}) ---")
        self._print_table(rows, ("ID", "PRIORITY", "STATUS", "ASSIGNED", "TITLE"))

    def _handle_reports(self):
        report = TicketReports(self.manager.list_all_tickets()).generate()

        print("\n--- CampusFlow System Report ---")
        print(f"Total Tickets : {report['total']}")
        print(f"Unresolved    : {report['unresolved']}")
        print(f"Resolved      : {report['resolution_percentage']:.1f}%")

        print("\nStatus Breakdown:")
        for status, count in report["status_breakdown"].items():
            print(f"  - {status}: {count}")

        print("\nPriority Breakdown:")
        for priority, count in report["priority_breakdown"].items():
            print(f"  - {priority}: {count}")


def main():
    CLI().run()


if __name__ == "__main__":
    main()
