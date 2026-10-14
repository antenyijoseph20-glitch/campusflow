from campus_flow.storage import StorageManager

class TicketManager:
    """Core business logic for ticket creation, validation, workflow, and notes."""

    VALID_CATEGORIES = {"Network", "Hardware", "Software", "Other"}
    VALID_URGENCIES = {"low", "medium", "high"}
    VALID_STATUSES = {"open", "in_progress", "resolved"}

    def __init__(self, filepath="tickets.json", silent_load=False):
        self.storage = StorageManager(filepath)
        loaded = self.storage.load_tickets(silent=silent_load)
        # If load failed due to corruption/duplicates, fallback to empty list to protect memory
        self.tickets = loaded if loaded is not None else []

    def _sync(self):
        """Persist current state to disk."""
        return self.storage.save_tickets(self.tickets)

    def list_all_tickets(self):
        """Return raw list of all tickets."""
        return self.tickets

    def get_ticket(self, ticket_id):
        """Retrieve a ticket by ID (case-insensitive lookup)."""
        if not ticket_id:
            return None
        clean_id = ticket_id.strip().upper()
        for t in self.tickets:
            if t["id"] == clean_id:
                return t
        return None

    def _generate_id(self):
        """Generate next sequential ID (T001, T002...)."""
        if not self.tickets:
            return "T001"
        max_num = 0
        for t in self.tickets:
            t_id = t.get("id", "")
            if t_id.startswith("T") and t_id[1:].isdigit():
                num = int(t_id[1:])
                if num > max_num:
                    max_num = num
        return f"T{max_num + 1:03d}"

    def calculate_priority(self, urgency, affected_users):
        """Rule precedence: critical when high & >=10 users; high when high or >=10; medium when medium or >=3; else low."""
        if urgency == "high" and affected_users >= 10:
            return "critical"
        elif urgency == "high" or affected_users >= 10:
            return "high"
        elif urgency == "medium" or affected_users >= 3:
            return "medium"
        else:
            return "low"

    def create_ticket(self, title, category, urgency, affected_users):
        """Strict validation before mutation."""
        if not title or not title.strip():
            return False, "Error: Title must not be blank."

        # Category validation (case-insensitive matching)
        normalized_cat = None
        for cat in self.VALID_CATEGORIES:
            if cat.lower() == category.strip().lower():
                normalized_cat = cat
                break
        if not normalized_cat:
            return False, f"Error: Invalid category. Choose from {list(self.VALID_CATEGORIES)}."

        norm_urgency = urgency.strip().lower()
        if norm_urgency not in self.VALID_URGENCIES:
            return False, f"Error: Invalid urgency. Choose from {list(self.VALID_URGENCIES)}."

        # CRITICAL BUG-HUNTER DEFENSE: Python bool is a subclass of int. Check bool explicitly first!
        if isinstance(affected_users, bool):
            return False, "Error: Affected users cannot be a boolean."

        raw_str = str(affected_users).strip()
        if "." in raw_str or "," in raw_str:
            return False, "Error: Affected users must be an integer, not a decimal."

        try:
            users_int = int(affected_users)
            if users_int <= 0:
                raise ValueError()
        except (ValueError, TypeError):
            return False, "Error: Affected users must be a positive integer greater than zero."

        ticket_id = self._generate_id()
        priority = self.calculate_priority(norm_urgency, users_int)

        new_ticket = {
            "id": ticket_id,
            "title": title.strip(),
            "category": normalized_cat,
            "urgency": norm_urgency,
            "affected_users": users_int,
            "priority": priority,
            "status": "open",
            "assigned_to": None,
            "notes": []
        }

        self.tickets.append(new_ticket)
        if not self._sync():
            self.tickets.pop()
            return False, "Error: Could not save ticket. Change rolled back."
        return True, f"Success! Created ticket {ticket_id} with priority '{priority}'."

    def assign_ticket(self, ticket_id, staff_name):
        """Assign ticket with resolved-lock guard."""
        if not staff_name or not staff_name.strip():
            return False, "Error: Staff name cannot be blank."
        
        ticket = self.get_ticket(ticket_id)
        if not ticket:
            return False, f"Error: Ticket ID '{ticket_id}' not found."

        if ticket["status"] == "resolved":
            return False, "Error: Cannot assign a resolved ticket."

        previous_assignee = ticket["assigned_to"]
        ticket["assigned_to"] = staff_name.strip()
        if not self._sync():
            ticket["assigned_to"] = previous_assignee
            return False, "Error: Could not save assignment. Change rolled back."
        return True, f"Success! Ticket {ticket['id']} assigned to {ticket['assigned_to']}."

    def update_workflow(self, ticket_id, new_status):
        """Workflow state machine: open -> in_progress -> resolved with strict guards."""
        norm_status = new_status.strip().lower()
        if norm_status not in self.VALID_STATUSES:
            return False, "Error: Invalid status."

        ticket = self.get_ticket(ticket_id)
        if not ticket:
            return False, f"Error: Ticket ID '{ticket_id}' not found."

        current_status = ticket["status"]

        # Resolved ticket lock guard
        if current_status == "resolved" and norm_status != "open":
            return False, "Error: Resolved tickets are locked and can only be modified by reopening."

        # Unassigned ticket guard
        if norm_status == "in_progress" and ticket["assigned_to"] is None:
            return False, "Error: Cannot move an unassigned ticket into 'in_progress'."

        previous_status = ticket["status"]
        ticket["status"] = norm_status
        if not self._sync():
            ticket["status"] = previous_status
            return False, "Error: Could not save status change. Change rolled back."
        return True, f"Success! Ticket status updated to '{norm_status}'."

    def add_note(self, ticket_id, author, message):
        """Append structured follow-up note with per-ticket ID (N001, N002...)."""
        ticket = self.get_ticket(ticket_id)
        if not ticket:
            return False, "Error: Ticket ID not found."

        if ticket["status"] not in ("open", "in_progress"):
            return False, "Error: Resolved tickets cannot accept new notes."

        if not author or not author.strip():
            return False, "Error: Note author cannot be blank."

        cleaned_msg = message.strip() if message else ""
        if not (5 <= len(cleaned_msg) <= 300):
            return False, "Error: Note message must be between 5 and 300 characters."

        notes_list = ticket.setdefault("notes", [])
        next_num = len(notes_list) + 1
        note_id = f"N{next_num:03d}"

        new_note = {
            "note_id": note_id,
            "author": author.strip(),
            "message": cleaned_msg
        }

        notes_list.append(new_note)
        if not self._sync():
            notes_list.pop()
            return False, "Error: Could not save note. Change rolled back."
        return True, f"Success! Added note {note_id}."

    def get_work_queue(self):
        """Unresolved tickets ordered by priority weight, then numeric ID."""
        priority_weights = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        unresolved = [t for t in self.tickets if t["status"] in ("open", "in_progress")]

        def sort_key(ticket):
            weight = priority_weights.get(ticket.get("priority"), 4)
            raw_id = ticket.get("id", "")
            numeric_id = int(raw_id[1:]) if raw_id[1:].isdigit() else 0
            return weight, numeric_id

        return sorted(unresolved, key=sort_key)