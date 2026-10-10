from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass
class Ticket:
    """Represent an IT support ticket."""

    id: str
    title: str
    category: str
    urgency: str
    affected_users: int
    priority: str
    status: str = "open"
    assigned_to: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert a ticket into a dictionary for JSON persistence."""
        return {
            "id": self.id,
            "title": self.title,
            "category": self.category,
            "urgency": self.urgency,
            "affected_users": self.affected_users,
            "priority": self.priority,
            "status": self.status,
            "assigned_to": self.assigned_to,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Ticket":
        """Create a validated ticket from stored dictionary data."""
        if not isinstance(data, dict):
            raise ValueError("Ticket data must be a dictionary.")

        required_fields = (
            "id",
            "title",
            "category",
            "urgency",
            "affected_users",
            "priority",
        )

        missing = [field for field in required_fields if field not in data]
        if missing:
            raise ValueError(
                f"Missing required ticket fields: {', '.join(missing)}"
            )

        ticket_id = data["id"]
        if not isinstance(ticket_id, str) or not ticket_id.strip():
            raise ValueError("Ticket ID must not be blank.")

        title = TicketValidator.validate_title(data["title"])
        category = TicketValidator.normalize_category(data["category"])
        urgency = TicketValidator.normalize_urgency(data["urgency"])
        affected_users = TicketValidator.validate_affected_users(
            data["affected_users"]
        )
        priority = data["priority"]

        expected_priority = TicketValidator.calculate_priority(
            urgency, affected_users
        )
        if priority != expected_priority:
            raise ValueError("Ticket priority does not match its urgency and affected users.")

        status = TicketValidator.validate_status(data.get("status", "open"))

        assigned_to = data.get("assigned_to")
        if assigned_to is not None:
            if not isinstance(assigned_to, str) or not assigned_to.strip():
                raise ValueError("Assigned staff name must be a non-empty string or None.")
            assigned_to = assigned_to.strip()

        return cls(
            id=ticket_id.strip(),
            title=title,
            category=category,
            urgency=urgency,
            affected_users=affected_users,
            priority=priority,
            status=status,
            assigned_to=assigned_to,
        )


class TicketValidator:
    """Validate and normalize ticket input."""

    VALID_CATEGORIES = {"Network", "Hardware", "Software", "Other"}
    VALID_URGENCIES = {"low", "medium", "high"}
    VALID_STATUSES = {"open", "in_progress", "resolved"}

    @staticmethod
    def validate_title(title: str) -> str:
        if not isinstance(title, str) or not title.strip():
            raise ValueError("Title must not be blank.")
        return title.strip()

    @staticmethod
    def normalize_category(category: str) -> str:
        if not isinstance(category, str) or not category.strip():
            raise ValueError("Category must not be blank.")

        normalized = category.strip().lower()
        for valid_category in TicketValidator.VALID_CATEGORIES:
            if normalized == valid_category.lower():
                return valid_category

        allowed = ", ".join(sorted(TicketValidator.VALID_CATEGORIES))
        raise ValueError(f"Invalid category. Choose from: {allowed}.")

    @staticmethod
    def normalize_urgency(urgency: str) -> str:
        if not isinstance(urgency, str) or not urgency.strip():
            raise ValueError("Urgency must not be blank.")

        normalized = urgency.strip().lower()
        if normalized not in TicketValidator.VALID_URGENCIES:
            allowed = ", ".join(sorted(TicketValidator.VALID_URGENCIES))
            raise ValueError(f"Invalid urgency. Choose from: {allowed}.")

        return normalized

    @staticmethod
    def validate_status(status: str) -> str:
        if not isinstance(status, str) or not status.strip():
            raise ValueError("Status must not be blank.")

        normalized = status.strip().lower()
        if normalized not in TicketValidator.VALID_STATUSES:
            allowed = ", ".join(sorted(TicketValidator.VALID_STATUSES))
            raise ValueError(f"Invalid status. Choose from: {allowed}.")

        return normalized

    @staticmethod
    def validate_affected_users(affected_users: Any) -> int:
        """Accept positive integers and digit-only strings, but reject decimals and booleans."""
        if isinstance(affected_users, bool):
            raise ValueError(
                "Affected users must be a positive integer, not a boolean."
            )

        if isinstance(affected_users, float):
            raise ValueError(
                "Affected users must be an integer, not a decimal."
            )

        if isinstance(affected_users, int):
            number = affected_users

        elif isinstance(affected_users, str):
            value = affected_users.strip()

            if not value:
                raise ValueError("Affected users must be a positive integer.")

            if "." in value:
                raise ValueError(
                    "Affected users must be an integer, not a decimal."
                )

            if not value.isdigit():
                raise ValueError("Affected users must be a positive integer.")

            number = int(value)

        else:
            raise ValueError("Affected users must be a positive integer.")

        if number <= 0:
            raise ValueError(
                "Affected users must be a positive integer greater than zero."
            )

        return number


    @staticmethod
    def calculate_priority(urgency: str, affected_users: int) -> str:
        normalized_urgency = TicketValidator.normalize_urgency(urgency)
        count = TicketValidator.validate_affected_users(affected_users)

        if normalized_urgency == "high":
            return "critical" if count >= 10 else "high"

        if normalized_urgency == "medium":
            return "high" if count >= 15 else "medium"

        return "medium" if count >= 10 else "low"


class IDGenerator:
    """Generate sequential ticket IDs."""

    @staticmethod
    def generate_next_id(existing_tickets: List[Ticket]) -> str:
        max_number = 0

        for ticket in existing_tickets:
            ticket_id = getattr(ticket, "id", None)

            if (
                isinstance(ticket_id, str)
                and ticket_id.startswith("T")
                and ticket_id[1:].isdigit()
            ):
                max_number = max(max_number, int(ticket_id[1:]))

        return f"T{max_number + 1:03d}"
