from dataclasses import dataclass
from typing import Optional, List, Dict, Any


@dataclass
class Ticket:
    id: str
    title: str
    category: str
    urgency: str
    affected_users: int
    priority: str
    status: str = "open"
    assigned_to: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "category": self.category,
            "urgency": self.urgency,
            "affected_users": self.affected_users,
            "priority": self.priority,
            "status": self.status,
            "assigned_to": self.assigned_to
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Ticket":
        return cls(
            id=data["id"],
            title=data["title"],
            category=data["category"],
            urgency=data["urgency"],
            affected_users=int(data["affected_users"]),
            priority=data["priority"],
            status=data.get("status", "open"),
            assigned_to=data.get("assigned_to", None)
        )


class TicketValidator:
    VALID_CATEGORIES = {"Network", "Hardware", "Software", "Other"}
    VALID_URGENCIES = {"low", "medium", "high"}
    VALID_STATUSES = {"open", "in_progress", "resolved"}

    @staticmethod
    def normalize_category(category: str) -> str:
        if not isinstance(category, str):
            raise ValueError("Category must be a string.")
        cleaned = category.strip().capitalize()
        if cleaned not in TicketValidator.VALID_CATEGORIES:
            raise ValueError(f"Invalid category '{category}'. Must be one of: {sorted(list(TicketValidator.VALID_CATEGORIES))}")
        return cleaned

    @staticmethod
    def normalize_urgency(urgency: str) -> str:
        if not isinstance(urgency, str):
            raise ValueError("Urgency must be a string.")
        cleaned = urgency.strip().lower()
        if cleaned not in TicketValidator.VALID_URGENCIES:
            raise ValueError(f"Invalid urgency '{urgency}'. Must be one of: {sorted(list(TicketValidator.VALID_URGENCIES))}")
        return cleaned

    @staticmethod
    def validate_title(title: str) -> str:
        if not isinstance(title, str) or not title.strip():
            raise ValueError("Title must not be blank.")
        return title.strip()

    @staticmethod
    def validate_affected_users(affected_users) -> int:
        # Guard against booleans (since isinstance(True, int) is True in Python)
        if isinstance(affected_users, bool):
            raise ValueError("Affected users must be a positive integer, not a boolean.")
        
        # Guard against floats / decimals passed directly or as strings containing '.'
        if isinstance(affected_users, float):
            raise ValueError("Affected users must be an integer, not a decimal.")
        
        if isinstance(affected_users, str):
            s = affected_users.strip()
            if "." in s or "e" in s.lower():
                raise ValueError("Affected users must be an integer, not a decimal.")
            try:
                val = int(s)
            except (ValueError, TypeError):
                raise ValueError("Affected users must be a positive numbers.")
        else:
            try:
                val = int(affected_users)
            except (ValueError, TypeError):
                raise ValueError("Affected users must be a positive integer.")

        if val <= 0:
            raise ValueError("Affected users must be a positive integer greater than zero.")
        return val

    @staticmethod
    def calculate_priority(urgency: str, affected_users: int) -> str:
        u = urgency.lower()
        if u == "high":
            return "critical" if affected_users >= 10 else "high"
        elif u == "medium":
            return "high" if affected_users >= 15 else "medium"
        elif u == "low":
            return "medium" if affected_users >= 10 else "low"
        return "low"


class IDGenerator:
    @staticmethod
    def generate_next_id(existing_tickets: List[Ticket]) -> str:
        if not existing_tickets:
            return "T001"
        max_num = 0
        for t in existing_tickets:
            try:
                # Expects format like 'T001', 'T012', etc.
                if t.id.startswith("T") and t.id[1:].isdigit():
                    num = int(t.id[1:])
                    if num > max_num:
                        max_num = num
            except (ValueError, IndexError):
                continue
        return f"T{max_num + 1:03d}"