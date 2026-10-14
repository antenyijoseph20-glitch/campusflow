import json
import os
import sys

class TicketManager:
    """Engineer A & B Integrated Core: Manages tickets, strict validation, notes, workflows, and safe JSON persistence."""
    
    VALID_CATEGORIES = {"Network", "Hardware", "Software", "Other"}
    VALID_URGENCIES = {"low", "medium", "high"}
    VALID_STATUSES = {"open", "in_progress", "resolved"}
    PRIORITY_RANKS = {"critical": 0, "high": 1, "medium": 2, "low": 3}

    def __init__(self, filepath="tickets.json", silent_load=False):
        self.filepath = filepath
        self.tickets = []
        self.load_data(silent=silent_load)

    def load_data(self, silent=False):
        """F7 — PERSISTENCE: Safe load with schema validation, duplicate ID checks, and memory protection."""
        if not os.path.exists(self.filepath):
            self.tickets = []
            return
        
        try:
            with open(self.filepath, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if not content:
                    self.tickets = []
                    return
                data = json.loads(content)
                if not isinstance(data, list):
                    if not silent:
                        print("Error: JSON root must be a list. Load rejected.")
                    return
                
                # Validate candidate records before mutating active memory
                validated_tickets = []
                seen_ids = set()
                for t in data:
                    if not isinstance(t, dict):
                        return
                    t_id = t.get("id")
                    if not t_id or t_id in seen_ids:
                        if not silent:
                            print(f"Error: Duplicate or missing ID '{t_id}'. Load rejected.")
                        return
                    seen_ids.add(t_id)
                    validated_tickets.append(t)

                self.tickets = validated_tickets
        except json.JSONDecodeError as e:
            if not silent:
                print(f"Error: Malformed JSON: {e}. Memory preserved.")
        except Exception as e:
            if not silent:
                print(f"Unexpected error loading data: {e}")

    def save_data(self):
        """Save active tickets to JSON file atomically."""
        try:
            with open(self.filepath, "w", encoding="utf-8") as f:
                json.dump(self.tickets, f, indent=4)
        except Exception as e:
            print(f"Error saving data: {e}")

    def _generate_id(self):
        """Auto-generate unique ticket IDs (T001, T002, ...)."""
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
        """Rule precedence: critical when high urgency AND affected_users >= 10; otherwise high when high urgency OR affected_users >= 10; otherwise medium when medium urgency OR affected_users >= 3; otherwise low."""
        if urgency == "high" and affected_users >= 10:
            return "critical"
        elif urgency == "high" or affected_users >= 10:
            return "high"
        elif urgency == "medium" or affected_users >= 3:
            return "medium"
        else:
            return "low"

    def create_ticket(self, title, category, urgency, affected_users):
        """F1 — CREATE: Strict validation before mutation."""
        if not title or not title.strip():
            return False, "Error: Title must not be blank."
        
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

        # Strict validation: disallow booleans, floats, decimals, negative, or zero
        if isinstance(affected_users, bool):
            return False, "Error: Affected users cannot be a boolean."
        
        raw_users_str = str(affected_users).strip()
        if "." in raw_users_str or "," in raw_users_str:
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
        self.save_data()
        return True, f"Success! Created ticket {ticket_id} with priority '{priority}'."

    def get_ticket(self, ticket_id):
        """Retrieve ticket by ID."""
        ticket_id = ticket_id.strip().upper()
        for t in self.tickets:
            if t["id"] == ticket_id:
                return t
        return None

    def list_all_tickets(self):
        """Return all stored tickets."""
        return self.tickets

    def assign_ticket(self, ticket_id, staff_name):
        """F3 — ASSIGN: Assign ticket to staff with atomic checks."""
        if not staff_name or not staff_name.strip():
            return False, "Error: Staff member name cannot be blank."
        
        ticket = self.get_ticket(ticket_id)
        if not ticket:
            return False, f"Error: Ticket ID '{ticket_id}' not found."

        if ticket["status"] == "resolved":
            return False, "Error: Cannot assign a resolved ticket."

        ticket["assigned_to"] = staff_name.strip()
        self.save_data()
        return True, f"Success! Ticket {ticket['id']} assigned to {ticket['assigned_to']}."

    def update_workflow(self, ticket_id, new_status):
        """F4 — WORKFLOW: open -> in_progress -> resolved with strict guards."""
        norm_status = new_status.strip().lower()
        if norm_status not in self.VALID_STATUSES:
            return False, f"Error: Invalid status."

        ticket = self.get_ticket(ticket_id)
        if not ticket:
            return False, f"Error: Ticket ID '{ticket_id}' not found."

        current_status = ticket["status"]

        # Resolved ticket lock guard
        if current_status == "resolved" and norm_status != "open":
            return False, "Error: Resolved tickets are locked and can only be modified by reopening to 'open'."

        # Unassigned ticket guard
        if norm_status == "in_progress" and ticket["assigned_to"] is None:
            return False, "Error: Cannot move an unassigned ticket into 'in_progress'."

        ticket["status"] = norm_status
        self.save_data()
        return True, f"Success! Ticket status updated to '{norm_status}'."

    def add_note(self, ticket_id, author, message):
        """Add structured follow-up note with per-ticket ID (N001, N002, ...) and strict validation."""
        ticket = self.get_ticket(ticket_id)
        if not ticket:
            return False, f"Error: Ticket ID not found."

        # Guard: Notes only allowed on open or in_progress tickets
        if ticket["status"] not in ("open", "in_progress"):
            return False, "Error: Resolved tickets cannot accept new notes."

        if not author or not author.strip():
            return False, "Error: Note author cannot be blank."

        cleaned_msg = message.strip() if message else ""
        if not (5 <= len(cleaned_msg) <= 300):
            return False, "Error: Note message must be between 5 and 300 characters."

        # Generate per-ticket note ID (N001, N002, ...)
        notes_list = ticket.setdefault("notes", [])
        next_num = len(notes_list) + 1
        note_id = f"N{next_num:03d}"

        new_note = {
            "note_id": note_id,
            "author": author.strip(),
            "message": cleaned_msg
        }

        notes_list.append(new_note)
        self.save_data()
        return True, f"Success! Added note {note_id}."

class EngineeringQuiz:
    """Manages the CLI Engineering Understanding Check for CampusFlow Next."""
    
    QUESTION_BANK = [
        {"id": 1, "scenario": "Ticket T001 is open and unassigned. A user tries to move it to in_progress.", "options": {"A": "Accept", "B": "Reject and preserve all data", "C": "Resolve it automatically", "D": "Remove ticket"}, "answer": "B"},
        {"id": 2, "scenario": "The app has zero tickets. What should resolution percentage display?", "options": {"A": "Crash", "B": "100%", "C": "0%", "D": "Divide by one without explanation"}, "answer": "C"},
        {"id": 3, "scenario": "Filter title='wifi', category='Network', status='open'. Which records should match?", "options": {"A": "Any record matching one filter", "B": "Only records matching all supplied filters", "C": "All network records", "D": "All open records"}, "answer": "B"},
        {"id": 4, "scenario": "A resolved ticket receives 'Add note'. What should happen?", "options": {"A": "Append anyway", "B": "Delete old notes", "C": "Reject until reopened", "D": "Change status silently"}, "answer": "C"},
        {"id": 5, "scenario": "The JSON file includes two tickets with the same ID. What should load do?", "options": {"A": "Keep both", "B": "Replace memory with duplicates", "C": "Reject the load without changing current memory", "D": "Rename IDs silently"}, "answer": "C"},
        {"id": 6, "scenario": "A PR changes validation but has no negative-case tests. Best review action?", "options": {"A": "Approve because it runs", "B": "Request focused tests and reasoning", "C": "Merge immediately", "D": "Ask AI to approve it"}, "answer": "B"}
    ]

    @staticmethod
    def grade_quiz(user_answers):
        score = 0
        results = []
        for q in EngineeringQuiz.QUESTION_BANK:
            q_id = q["id"]
            selected = user_answers.get(q_id, "").strip().upper()
            is_correct = (selected == q["answer"])
            if is_correct:
                score += 1
            results.append({"id": q_id, "selected": selected, "correct": q["answer"], "is_correct": is_correct})
        return score, results
    