
from typing import List, Optional, Dict, Any

from campus_flow.models import Ticket, TicketValidator, IDGenerator
from campus_flow.storage import StorageHandler


class TicketManager:
    def __init__(self, filepath: str = "tickets.json"):
        self.filepath = filepath
        self.tickets: List[Ticket] = StorageHandler.load_tickets(self.filepath)

    def save(self) -> None:
        StorageHandler.save_tickets(self.tickets, self.filepath)

    def _set_status_and_save(self, ticket: Ticket, new_status: str) -> None:
        """Restore the previous status if persistence fails."""
        previous_status = ticket.status
        ticket.status = new_status

        try:
            self.save()
        except Exception:
            ticket.status = previous_status
            raise

    # F1 — CREATE
    def create_ticket(
        self,
        title: str,
        category: str,
        urgency: str,
        affected_users: int,
    ) -> Ticket:
        clean_title = TicketValidator.validate_title(title)
        clean_category = TicketValidator.normalize_category(category)
        clean_urgency = TicketValidator.normalize_urgency(urgency)
        clean_users = TicketValidator.validate_affected_users(affected_users)

        priority = TicketValidator.calculate_priority(clean_urgency, clean_users)
        ticket_id = IDGenerator.generate_next_id(self.tickets)

        new_ticket = Ticket(
            id=ticket_id,
            title=clean_title,
            category=clean_category,
            urgency=clean_urgency,
            affected_users=clean_users,
            priority=priority,
            status="open",
            assigned_to=None,
        )

        self.tickets.append(new_ticket)

        try:
            self.save()
        except Exception:
            self.tickets.pop()
            raise

        return new_ticket

    # F2 — LIST / VIEW
    def get_all_tickets(self) -> List[Ticket]:
        return self.tickets

    def get_ticket_by_id(self, ticket_id: str) -> Optional[Ticket]:
        if not isinstance(ticket_id, str):
            return None

        tid = ticket_id.strip().upper()

        for ticket in self.tickets:
            if ticket.id.upper() == tid:
                return ticket

        return None

    # F3 — ASSIGN
    def assign_ticket(self, ticket_id: str, staff_name: str) -> Ticket:
        if not isinstance(staff_name, str) or not staff_name.strip():
            raise ValueError("Staff member name must not be empty.")

        ticket = self.get_ticket_by_id(ticket_id)

        if not ticket:
            raise ValueError(f"Unknown ticket ID '{ticket_id}'.")

        previous_assignee = ticket.assigned_to
        ticket.assigned_to = staff_name.strip()

        try:
            self.save()
        except Exception:
            ticket.assigned_to = previous_assignee
            raise

        return ticket

    # F4 — WORKFLOW
    def update_status(
        self,
        ticket_id: str,
        new_status: str,
        reopen: bool = False,
    ) -> Ticket:
        ticket = self.get_ticket_by_id(ticket_id)

        if not ticket:
            raise ValueError(f"Unknown ticket ID '{ticket_id}'.")

        if not isinstance(new_status, str):
            raise ValueError("Status must be a string.")

        target_status = new_status.strip().lower()

        if target_status not in TicketValidator.VALID_STATUSES:
            raise ValueError(
                f"Invalid status '{new_status}'. "
                "Allowed: open, in_progress, resolved."
            )

        if target_status == ticket.status and not reopen:
            return ticket

        # Reopening is a special, explicit transition.
        if reopen:
            if ticket.status != "resolved":
                raise ValueError("Only resolved tickets can be reopened.")

            if target_status != "open":
                raise ValueError("Explicit reopen must set status to 'open'.")

            self._set_status_and_save(ticket, "open")
            return ticket

        # Resolved tickets must be explicitly reopened first.
        if ticket.status == "resolved":
            raise ValueError(
                "A resolved ticket may only be modified after an explicit reopen."
            )


        allowed_transitions = {
            "open": {"in_progress"},
            "in_progress": {"resolved"},
        }

        if target_status not in allowed_transitions.get(ticket.status, set()):
            raise ValueError(
                f"Invalid workflow transition: '{ticket.status}' to "
                f"'{target_status}'. Follow open -> in_progress -> resolved."
            )

        if ticket.status == "open" and target_status == "in_progress":
            if not ticket.assigned_to:
                raise ValueError(
                    "Do not move an unassigned ticket into in_progress. "
                    "Assign it first."
                )

        self._set_status_and_save(ticket, target_status)
        return ticket


    def get_work_queue(self) -> List[Ticket]:
        unresolved = [
            ticket
            for ticket in self.tickets
            if ticket.status in ("open", "in_progress")
        ]

        priority_weights = {
            "critical": 0,
            "high": 1,
            "medium": 2,
            "low": 3,
        }

        def sort_key(ticket: Ticket):
            priority_weight = priority_weights.get(ticket.priority, 4)

            try:
                numeric_id = int(ticket.id[1:])
            except (ValueError, IndexError):
                numeric_id = 0

            return priority_weight, numeric_id

        return sorted(unresolved, key=sort_key)

    # F6 — REPORTS
    def get_reports(self) -> Dict[str, Any]:
        total = len(self.tickets)
        status_counts = {
            "open": 0,
            "in_progress": 0,
            "resolved": 0,
        }
        priority_counts = {
            "critical": 0,
            "high": 0,
            "medium": 0,
            "low": 0,
        }

        for ticket in self.tickets:
            if ticket.status in status_counts:
                status_counts[ticket.status] += 1

            if ticket.priority in priority_counts:
                priority_counts[ticket.priority] += 1

        return {
            "total": total,
            "status_breakdown": status_counts,
            "priority_breakdown": priority_counts,
        }
