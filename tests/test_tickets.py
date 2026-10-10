import pytest

from campus_flow.manager import TicketManager
from campus_flow.models import Ticket, TicketValidator, IDGenerator


def test_reports_generation(tmp_path):
    db_file = tmp_path / "test_tickets.json"
    manager = TicketManager(filepath=str(db_file))

    # Zero tickets check
    rep_empty = manager.get_reports()
    assert rep_empty["total"] == 0

    manager.create_ticket("T1", "Network", "high", 15) # critical, open
    t2 = manager.create_ticket("T2", "Hardware", "low", 1)  # low, open

    manager.assign_ticket(t2.id, "Staff")
    manager.update_status(t2.id, "in_progress")
    manager.update_status(t2.id, "resolved")

    rep = manager.get_reports()
    assert rep["total"] == 2
    assert rep["status_breakdown"]["open"] == 1
    assert rep["status_breakdown"]["resolved"] == 1
    assert rep["priority_breakdown"]["critical"] == 1
    assert rep["priority_breakdown"]["low"] == 1


def test_manager_create_ticket(tmp_path):
    db_file = tmp_path / "test_tickets.json"
    manager = TicketManager(filepath=str(db_file))

    t = manager.create_ticket("Wi-Fi Down", "Network", "high", 15)
    assert t.id == "T001"
    assert t.priority == "critical"
    assert t.status == "open"
    assert t.assigned_to is None
    assert len(manager.get_all_tickets()) == 1


def test_priority_calculation():
    assert TicketValidator.calculate_priority("high", 12) == "critical"
    assert TicketValidator.calculate_priority("high", 5) == "high"
    assert TicketValidator.calculate_priority("medium", 20) == "high"
    assert TicketValidator.calculate_priority("medium", 5) == "medium"
    assert TicketValidator.calculate_priority("low", 15) == "medium"
    assert TicketValidator.calculate_priority("low", 3) == "low"


def test_ticket_validation_failures():
    with pytest.raises(ValueError, match="Title must not be blank"):
        TicketValidator.validate_title("   ")

    with pytest.raises(ValueError, match="Invalid category"):
        TicketValidator.normalize_category("Database")

    with pytest.raises(ValueError, match="Invalid urgency"):
        TicketValidator.normalize_urgency("urgent")

    with pytest.raises(ValueError, match="positive integer"):
        TicketValidator.validate_affected_users(0)

    with pytest.raises(ValueError, match="positive integer"):
        TicketValidator.validate_affected_users(-5)

    with pytest.raises(ValueError, match="not a boolean"):
        TicketValidator.validate_affected_users(True)

    with pytest.raises(ValueError, match="not a decimal"):
        TicketValidator.validate_affected_users(10.5)

    with pytest.raises(ValueError, match="not a decimal"):
        TicketValidator.validate_affected_users("12.34")


def test_ticket_validation_success():
    title = TicketValidator.validate_title("  Server downtime  ")
    assert title == "Server downtime"

    category = TicketValidator.normalize_category("network")
    assert category == "Network"

    urgency = TicketValidator.normalize_urgency("  HIGH ")
    assert urgency == "high"

    affected = TicketValidator.validate_affected_users("15")
    assert affected == 15


def test_id_generator():
    assert IDGenerator.generate_next_id([]) == "T001"

    t1 = Ticket(id="T001", title="Test", category="Hardware", urgency="low", affected_users=1, priority="low")
    t2 = Ticket(id="T005", title="Test 2", category="Software", urgency="low", affected_users=1, priority="low")

    assert IDGenerator.generate_next_id([t1, t2]) == "T006"
