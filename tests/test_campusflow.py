import os
import pytest
from campus_flow.models import Ticket, TicketValidator, IDGenerator
from campus_flow.storage import StorageHandler


def test_ticket_validation_success():
    title = TicketValidator.validate_title("  Server downtime  ")
    assert title == "Server downtime"

    category = TicketValidator.normalize_category("network")
    assert category == "Network"

    urgency = TicketValidator.normalize_urgency("  HIGH ")
    assert urgency == "high"

    affected = TicketValidator.validate_affected_users("15")
    assert affected == 15


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


def test_priority_calculation():
    assert TicketValidator.calculate_priority("high", 12) == "critical"
    assert TicketValidator.calculate_priority("high", 5) == "high"
    assert TicketValidator.calculate_priority("medium", 20) == "high"
    assert TicketValidator.calculate_priority("medium", 5) == "medium"
    assert TicketValidator.calculate_priority("low", 15) == "medium"
    assert TicketValidator.calculate_priority("low", 3) == "low"


def test_id_generator():
    assert IDGenerator.generate_next_id([]) == "T001"
    
    t1 = Ticket(id="T001", title="Test", category="Hardware", urgency="low", affected_users=1, priority="low")
    t2 = Ticket(id="T005", title="Test 2", category="Software", urgency="low", affected_users=1, priority="low")
    
    assert IDGenerator.generate_next_id([t1, t2]) == "T006"


def test_storage_save_and_load(tmp_path):
    test_file = tmp_path / "test_tickets.json"
    
    tickets = [
        Ticket(id="T001", title="Wi-Fi Outage", category="Network", urgency="high", affected_users=20, priority="critical", status="open", assigned_to=None),
        Ticket(id="T002", title="Broken Screen", category="Hardware", urgency="low", affected_users=1, priority="low", status="in_progress", assigned_to="Alice")
    ]
    
    StorageHandler.save_tickets(tickets, str(test_file))
    assert test_file.exists()
    
    loaded = StorageHandler.load_tickets(str(test_file))
    assert len(loaded) == 2
    assert loaded[0].id == "T001"
    assert loaded[0].priority == "critical"
    assert loaded[1].assigned_to == "Alice"


def test_storage_missing_file():
    loaded = StorageHandler.load_tickets("nonexistent_tickets_file_12345.json")
    assert loaded == []


def test_storage_malformed_json(tmp_path):
    bad_file = tmp_path / "bad_tickets.json"
    bad_file.write_text("{ this is invalid json }", encoding="utf-8")
    
    with pytest.raises(ValueError, match="Malformed JSON detected"):
        StorageHandler.load_tickets(str(bad_file))