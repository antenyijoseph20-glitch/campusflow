import json
import os


class StorageManager:
    """Handles safe, atomic JSON file persistence and schema validation."""

    # Every stored record must carry these keys. The manager and the reporting
    # classes read them directly, so a record missing one would load cleanly and
    # then raise KeyError on first use.
    REQUIRED_FIELDS = (
        "id",
        "title",
        "category",
        "urgency",
        "affected_users",
        "priority",
        "status",
        "assigned_to",
        "notes",
    )

    # The canonical values the application writes. A record carrying anything
    # else is corrupt: the manager would accept it on load and then count it in
    # reports as a live ticket in a state the rest of the code cannot produce.
    VALID_CATEGORIES = ("Network", "Hardware", "Software", "Other")
    VALID_URGENCIES = ("low", "medium", "high")
    VALID_PRIORITIES = ("critical", "high", "medium", "low")
    VALID_STATUSES = ("open", "in_progress", "resolved")

    # A note is a three-field object. The message bounds match the ones
    # TicketManager.add_note enforces, so a file cannot smuggle in a note the
    # application itself would have refused.
    NOTE_FIELDS = ("note_id", "author", "message")
    NOTE_MIN_LENGTH = 5
    NOTE_MAX_LENGTH = 300

    def __init__(self, filepath="tickets.json", priority_rule=None):
        self.filepath = filepath
        # Injected rather than reimplemented. The derivation of ``priority``
        # belongs to TicketManager; passing it in lets the load check that what
        # was written down agrees with the rule without stating the rule twice.
        # Called directly with no rule, the check is skipped and only the
        # lexical values are validated.
        self.priority_rule = priority_rule

    def _reject(self, reason, silent):
        """Report a rejected load and return None, the caller's failure signal."""
        if not silent:
            print(f"Error: {reason} Load rejected.")
        return None

    def load_tickets(self, silent=False):
        """Loads and validates tickets from disk. Rejects corrupted data without crashing."""
        if not os.path.exists(self.filepath):
            return []

        try:
            with open(self.filepath, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if not content:
                    return []

                data = json.loads(content)
                # Edge case: JSON root must be a list
                if not isinstance(data, list):
                    return self._reject("JSON root is not a list.", silent)

                # Every record must be an object carrying all nine fields with
                # legal values, and IDs must be present and unique. The whole
                # file is rejected on the first problem: a partly loaded file is
                # harder to reason about than an explicit empty start.
                validated_tickets = []
                seen_ids = set()
                for t in data:
                    if not isinstance(t, dict):
                        return self._reject("Ticket record is not an object.", silent)

                    missing = [f for f in self.REQUIRED_FIELDS if f not in t]
                    if missing:
                        return self._reject(
                            f"Ticket record is missing {missing}.", silent
                        )

                    t_id = t.get("id")
                    if not isinstance(t_id, str) or not t_id.strip():
                        return self._reject("Ticket record has a blank ID.", silent)
                    if t_id in seen_ids:
                        return self._reject(f"Duplicate ID '{t_id}' detected.", silent)

                    problem = self._validate_values(t)
                    if problem:
                        return self._reject(f"Ticket {t_id}: {problem}", silent)

                    seen_ids.add(t_id)
                    validated_tickets.append(t)

                return validated_tickets
        except json.JSONDecodeError as e:
            if not silent:
                print(f"Error: Malformed JSON syntax ({e}). Memory preserved.")
            return None
        except Exception as e:
            if not silent:
                print(f"Unexpected storage error: {e}")
            return None

    def _validate_values(self, ticket):
        """Describe the first illegal value in a record, or return None if valid.

        Presence of the nine fields is checked by the caller; this checks that
        what they hold is something the application could have written.
        """
        if not isinstance(ticket["title"], str) or not ticket["title"].strip():
            return "title is blank or not a string."

        if ticket["category"] not in self.VALID_CATEGORIES:
            return (
                f"category {ticket['category']!r} is not one of "
                f"{list(self.VALID_CATEGORIES)}."
            )

        if ticket["urgency"] not in self.VALID_URGENCIES:
            return (
                f"urgency {ticket['urgency']!r} is not one of "
                f"{list(self.VALID_URGENCIES)}."
            )

        if ticket["priority"] not in self.VALID_PRIORITIES:
            return (
                f"priority {ticket['priority']!r} is not one of "
                f"{list(self.VALID_PRIORITIES)}."
            )

        if ticket["status"] not in self.VALID_STATUSES:
            return (
                f"status {ticket['status']!r} is not one of "
                f"{list(self.VALID_STATUSES)}."
            )

        users = ticket["affected_users"]
        # The bool test comes first on purpose: bool is a subclass of int, so
        # True would satisfy a plain integer check and load as one user.
        if isinstance(users, bool) or not isinstance(users, int) or users <= 0:
            return f"affected_users {users!r} is not a positive integer."

        assignee = ticket["assigned_to"]
        if assignee is not None and not (
            isinstance(assignee, str) and assignee.strip()
        ):
            return "assigned_to is neither null nor a non-blank name."

        # Priority is derived, not chosen, so a record where it disagrees with
        # urgency and affected_users describes a ticket the application could
        # not have created.
        if self.priority_rule is not None:
            expected = self.priority_rule(ticket["urgency"], users)
            if ticket["priority"] != expected:
                return (
                    f"priority {ticket['priority']!r} contradicts urgency "
                    f"{ticket['urgency']!r} with {users} affected users, which "
                    f"derives {expected!r}."
                )

        return self._validate_notes(ticket["notes"])

    def _validate_notes(self, notes):
        """Check note shapes and that note IDs are unique within the ticket."""
        if not isinstance(notes, list):
            return "notes is not a list."

        seen_note_ids = set()
        for note in notes:
            if not isinstance(note, dict):
                return "a note entry is not an object."

            missing = [f for f in self.NOTE_FIELDS if f not in note]
            if missing:
                return f"a note entry is missing {missing}."

            note_id = note["note_id"]
            if not isinstance(note_id, str) or not note_id.strip():
                return "a note entry has a blank note_id."
            if note_id in seen_note_ids:
                return f"note ID '{note_id}' is repeated within this ticket."
            seen_note_ids.add(note_id)

            if not isinstance(note["author"], str) or not note["author"].strip():
                return f"note {note_id} has a blank author."

            message = note["message"]
            if not isinstance(message, str) or not (
                self.NOTE_MIN_LENGTH <= len(message.strip()) <= self.NOTE_MAX_LENGTH
            ):
                return (
                    f"note {note_id} message is outside "
                    f"{self.NOTE_MIN_LENGTH}-{self.NOTE_MAX_LENGTH} characters."
                )

        return None

    def save_tickets(self, tickets):
        """Atomic write: writes to a temporary file first, then replaces target to prevent corruption."""
        temp_filepath = self.filepath + ".tmp"
        try:
            with open(temp_filepath, "w", encoding="utf-8") as f:
                json.dump(tickets, f, indent=4)
            os.replace(temp_filepath, self.filepath)
            return True
        except Exception as e:
            print(f"Error saving tickets atomically: {e}")
            if os.path.exists(temp_filepath):
                try:
                    os.remove(temp_filepath)
                except OSError:
                    pass
            return False
