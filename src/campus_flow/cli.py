import sys
from campus_flow.manager import TicketManager


class CLI:
    def __init__(self):
        self.manager = TicketManager()

    def _get_required_input(self, prompt):
        """Keep asking until the user provides a non-empty value."""
        while True:
            value = input(prompt).strip()

            if value:
                return value

            print("Error: Invalid input. This field cannot be empty.")

    def run(self):
        print("========================================")
        print("     Welcome to CampusFlow CLI          ")
        print(" IT Support Ticket & Workflow Manager   ")
        print("========================================")

        while True:
            print("\n--- MAIN MENU ---")
            print("1. Create Ticket")
            print("2. List All Tickets")
            print("3. View Ticket Details")
            print("4. Assign Ticket")
            print("5. Update Ticket Status (Workflow)")
            print("6. View Work Queue")
            print("7. Generate Reports")
            print("8. Exit")

            choice = input("Select an option (1-8): ").strip()

            try:
                if choice == "1":
                    self._handle_create()
                elif choice == "2":
                    self._handle_list()
                elif choice == "3":
                    self._handle_view()
                elif choice == "4":
                    self._handle_assign()
                elif choice == "5":
                    self._handle_workflow()
                elif choice == "6":
                    self._handle_work_queue()
                elif choice == "7":
                    self._handle_reports()
                elif choice == "8":
                    print("Exiting CampusFlow. Goodbye!")
                    sys.exit(0)
                else:
                    print("Error: Invalid choice. Please enter a number between 1 and 8.")
            except Exception as e:
                print(f"\n[Error]: {e}")

    def _handle_create(self):
        print("\n--- Create New Ticket ---")
        title = input("Enter ticket title: ")
        print("Categories: Network, Hardware, Software, Other")
        category = input("Enter category: ")
        print("Urgency levels: low, medium, high")
        urgency = input("Enter urgency: ")
        affected_users = input("Enter affected users (positive integer): ")

        ticket = self.manager.create_ticket(title, category, urgency, affected_users)
        print(f"\nSuccess! Ticket {ticket.id} created with priority '{ticket.priority}'.")

    def _handle_list(self):
        tickets = self.manager.get_all_tickets()
        if not tickets:
            print("\nNo tickets found in the system.")
            return

        print(f"\n--- All Tickets ({len(tickets)}) ---")
        print(f"{'ID':<6} | {'Status':<12} | {'Priority':<10} | {'Category':<10} | {'Title'}")
        print("-" * 65)
        for t in tickets:
            print(f"{t.id:<6} | {t.status:<12} | {t.priority:<10} | {t.category:<10} | {t.title}")

    def _handle_view(self):
        tid = input("Enter Ticket ID to view (e.g., T001): ")
        t = self.manager.get_ticket_by_id(tid)
        if not t:
            print(f"Error: Ticket '{tid}' not found.")
            return

        print(f"\n--- Ticket Details [{t.id}] ---")
        print(f"Title          : {t.title}")
        print(f"Category       : {t.category}")
        print(f"Urgency        : {t.urgency}")
        print(f"Affected Users : {t.affected_users}")
        print(f"Priority       : {t.priority}")
        print(f"Status         : {t.status}")
        print(f"Assigned To    : {t.assigned_to or 'Unassigned'}")

    def _handle_assign(self):
        tid = input("Enter Ticket ID to assign: ")
        staff = input("Enter staff member name: ")
        t = self.manager.assign_ticket(tid, staff)
        print(f"Success! Ticket {t.id} assigned to {t.assigned_to}.")

    def _handle_workflow(self):
        tid = input("Enter Ticket ID: ")
        t = self.manager.get_ticket_by_id(tid)
        if not t:
            print(f"Error: Ticket '{tid}' not found.")
            return

        print(f"Current Status: {t.status}")
        if t.status == "resolved":
            reopen_choice = input("Ticket is resolved. Do you want to reopen it? (y/n): ").strip().lower()
            if reopen_choice == "y":
                self.manager.update_status(tid, "open", reopen=True)
                print(f"Success! Ticket {tid} has been reopened to status 'open'.")
                return
            else:
                print("Operation cancelled.")
                return

        print("Allowed target statuses: in_progress, resolved")
        new_status = input("Enter target status: ")
        self.manager.update_status(tid, new_status)
        print(f"Success! Ticket {tid} status updated to {new_status}.")

    def _handle_work_queue(self):
        queue = self.manager.get_work_queue()
        if not queue:
            print("\nWork Queue is empty (no open or unresolved tickets).")
            return

        print(f"\n--- Active Work Queue ({len(queue)} tickets) ---")
        print(f"{'ID':<6} | {'Priority':<10} | {'Status':<12} | {'Assigned':<12} | {'Title'}")
        print("-" * 70)
        for t in queue:
            assigned = t.assigned_to or "Unassigned"
            print(f"{t.id:<6} | {t.priority:<10} | {t.status:<12} | {assigned:<12} | {t.title}")

    def _handle_reports(self):
        rep = self.manager.get_reports()
        print("\n--- CampusFlow System Report ---")
        print(f"Total Tickets : {rep['total']}")
        print("\nStatus Breakdown:")
        for status, count in rep["status_breakdown"].items():
            print(f"  - {status}: {count}")
        print("\nPriority Breakdown:")
        for priority, count in rep["priority_breakdown"].items():
            print(f"  - {priority}: {count}")