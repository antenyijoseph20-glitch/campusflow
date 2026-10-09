from typing import List, Optional, Dict, Any
from campus_flow.models import Ticket, TicketValidator, IDGenerator
from campus_flow.storage import StorageHandler


class TicketManager:
    def __init__(self, filepath: str = "tickets.json"):
        self.filepath = filepath
        self.tickets: List[Ticket] = StorageHandler.load_tickets(self.filepath)

    def save(self) -> None:
        StorageHandler.save_tickets(self.tickets, self.filepath)

    # F1 — CREATE
    def create_ticket(self, title: str, category: str, urgency: str, affected_users: int) -> Ticket:
        clean_title = TicketValidator.validate_title(title)
        clean_cat = TicketValidator.normalize_category(category)
        clean_urg = TicketValidator.normalize_urgency(urgency)
        clean_users = TicketValidator.validate_affected_users(affected_users)

        priority = TicketValidator.calculate_priority(clean_urg, clean_users)
        ticket_id = IDGenerator.generate_next_id(self.tickets)

        new_ticket = Ticket(
            id=ticket_id,
            title=clean_title,
            category=clean_cat,
            urgency=clean_urg,
            affected_users=clean_users,
            priority=priority,
            status="open",
            assigned_to=None
        )

        self.tickets.append(new_ticket)
        self.save()
        return new_ticket

    # F2 — LIST / VIEW
    def get_all_tickets(self) -> List[Ticket]:
        return self.tickets

    def get_ticket_by_id(self, ticket_id: str) -> Optional[Ticket]:
        tid = ticket_id.strip().upper()
        for t in self.tickets:
            if t.id.upper() == tid:
                return t
        return None

    # F3 — ASSIGN
    def assign_ticket(self, ticket_id: str, staff_name: str) -> Ticket:
        if not staff_name or not staff_name.strip():
            raise ValueError("Staff member name must not be empty.")
       
        ticket = self.get_ticket_by_id(ticket_id)
        if not ticket:
            raise ValueError(f"Unknown ticket ID '{ticket_id}'.")

        ticket.assigned_to = staff_name.strip()
        self.save()
        return ticket

    # F4 — WORKFLOW
    def update_status(self, ticket_id: str, new_status: str, reopen: bool = False) -> Ticket:
        ticket = self.get_ticket_by_id(ticket_id)
        if not ticket:
            raise ValueError(f"Unknown ticket ID '{ticket_id}'.")

        target_status = new_status.strip().lower()
        if target_status not in TicketValidator.VALID_STATUSES:
            raise ValueError(f"Invalid status '{new_status}'. Allowed: open, in_progress, resolved.")

        # Reopen handling
        if reopen:
            if ticket.status != "resolved":
                raise ValueError("Only resolved tickets can be reopened.")
            if target_status != "open":
                raise ValueError("Explicit reopen must set status to 'open'.")
            ticket.status = "open"
            self.save()
            return ticket

        # Normal transition rules
        if ticket.status == "resolved" and target_status != "resolved":
            raise ValueError("A resolved ticket may only be modified after an explicit reopen.")

        if ticket.status == "open" and target_status == "in_progress":
            if ticket.assigned_to is None:
                raise ValueError("Do not move an unassigned ticket into in_progress. Assign it first.")

        ticket.status = target_status
        self.save()
        return ticket

    # F5 — WORK QUEUE
    def get_work_queue(self) -> List[Ticket]:
        unresolved = [t for t in self.tickets if t.status in ("open", "in_progress")]
        priority_weights = {"critical": 0, "high": 1, "medium": 2, "low": 3}

        def sort_key(t: Ticket):
            p_weight = priority_weights.get(t.priority, 4)
            try:
                num_id = int(t.id[1:])
            except (ValueError, IndexError):
                num_id = 0
            return (p_weight, num_id)

        return sorted(unresolved, key=sort_key)

    # F6 — REPORTS
    def get_reports(self) -> Dict[str, Any]:
        total = len(self.tickets)
        status_counts = {"open": 0, "in_progress": 0, "resolved": 0}
        priority_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}

        for t in self.tickets:
            if t.status in status_counts:
                status_counts[t.status] += 1
            if t.priority in priority_counts:
                priority_counts[t.priority] += 1

        return {
            "total": total,
            "status_breakdown": status_counts,
            "priority_breakdown": priority_counts
        }