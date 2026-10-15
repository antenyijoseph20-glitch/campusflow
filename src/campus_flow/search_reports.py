"""Search and reporting for CampusFlow tickets (Engineer B: feat/22-search-and-insights).

Two cooperating helpers, both operating on the plain dict records produced by
``campus_flow.models.TicketManager``:

- ``TicketSearch``  -- case-insensitive substring title matching plus category,
  status, urgency and priority filters combined with strict logical AND.
- ``TicketReports`` -- aggregate counts and resolution percentage, safe on an
  empty dataset (no division by zero).

Also exports ``sort_by_priority``, the ordering the work queue uses, so search
results can be presented in the same order.

Neither class mutates ticket data.
"""

VALID_CATEGORIES = ("Network", "Hardware", "Software", "Other")
VALID_STATUSES = ("open", "in_progress", "resolved")
VALID_PRIORITIES = ("critical", "high", "medium", "low")

# Lower weight sorts first. Unknown priorities fall to the end rather than
# raising, so one odd record cannot take down a whole view; the loader rejects
# such records, which makes this a fallback rather than an expected path.
PRIORITY_WEIGHTS = {"critical": 0, "high": 1, "medium": 2, "low": 3}


def sort_by_priority(tickets):
    """Return the tickets ordered by priority weight, then numeric ticket ID."""
    def sort_key(ticket):
        raw_id = str(ticket.get("id", ""))
        numeric_id = int(raw_id[1:]) if raw_id[1:].isdigit() else 0
        return PRIORITY_WEIGHTS.get(ticket.get("priority"), len(PRIORITY_WEIGHTS)), numeric_id

    return sorted(tickets, key=sort_key)


def _fold(value):
    """Normalize a filter value for case-insensitive comparison."""
    return value.strip().casefold() if isinstance(value, str) else value


class TicketSearch:
    """Filter a list of ticket dicts. Every supplied filter must match (AND)."""

    FILTER_KEYS = ("query", "category", "status", "priority", "urgency")

    @classmethod
    def matches(
        cls,
        ticket,
        query=None,
        category=None,
        status=None,
        priority=None,
        urgency=None,
    ):
        """Return True when the ticket satisfies every supplied filter."""
        if query:
            needle = _fold(query)
            haystack = ticket.get("title", "")
            if needle not in haystack.casefold():
                return False

        # Category is stored canonically ("Network"); compare case-insensitively
        # so that "network" finds the same tickets.
        if category and _fold(category) != _fold(ticket.get("category", "")):
            return False

        if status and _fold(status) != _fold(ticket.get("status", "")):
            return False

        if priority and _fold(priority) != _fold(ticket.get("priority", "")):
            return False

        if urgency and _fold(urgency) != _fold(ticket.get("urgency", "")):
            return False

        return True

    @classmethod
    def search(cls, tickets, **filters):
        """Return the tickets matching all supplied filters.

        Raises ValueError for a filter name that is not recognised, so a typo
        is reported rather than silently ignored.
        """
        unknown = set(filters) - set(cls.FILTER_KEYS)
        if unknown:
            raise ValueError(
                f"Unknown filter(s): {sorted(unknown)}. "
                f"Allowed: {list(cls.FILTER_KEYS)}."
            )
        return [t for t in tickets if cls.matches(t, **filters)]


class TicketReports:
    """Aggregate reporting over a snapshot of tickets."""

    def __init__(self, tickets=()):
        self.tickets = list(tickets)

    @property
    def total(self):
        return len(self.tickets)

    def count_by_status(self):
        """Status breakdown; every valid status is present, defaulting to 0."""
        return {
            status: sum(1 for t in self.tickets if t.get("status") == status)
            for status in VALID_STATUSES
        }

    def count_by_priority(self):
        """Priority breakdown; every valid priority is present, defaulting to 0."""
        return {
            priority: sum(1 for t in self.tickets if t.get("priority") == priority)
            for priority in VALID_PRIORITIES
        }

    def count_by_category(self):
        """Category breakdown; every valid category is present, defaulting to 0."""
        return {
            category: sum(1 for t in self.tickets if t.get("category") == category)
            for category in VALID_CATEGORIES
        }

    def resolved_count(self):
        return sum(1 for t in self.tickets if t.get("status") == "resolved")

    def resolution_percentage(self):
        """Percentage of tickets resolved. Returns 0.0 for an empty dataset."""
        if self.total == 0:
            return 0.0
        return self.resolved_count() / self.total * 100.0

    def unresolved_count(self):
        return sum(
            1 for t in self.tickets if t.get("status") in ("open", "in_progress")
        )

    def generate(self):
        """Return the full report as a plain dict."""
        return {
            "total": self.total,
            "status_breakdown": self.count_by_status(),
            "category_breakdown": self.count_by_category(),
            "priority_breakdown": self.count_by_priority(),
            "resolution_percentage": self.resolution_percentage(),
            "resolved": self.resolved_count(),
            "unresolved": self.unresolved_count(),
        }
