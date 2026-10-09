import pytest
from campus_flow.manager import TicketManager


def test_manager_create_ticket(tmp_path):
    db_file = tmp_path / "test_tickets.json"
    manager = TicketManager(filepath=str(db_file))

    t = manager.create_ticket("Wi-Fi Down", "Network", "high", 15)
    assert t.id == "T001"
    assert t.priority == "critical"
    assert t.status == "open"
    assert t.assigned_to is None
    assert len(manager.get_all_tickets()) == 1


def test_manager_assign_ticket(tmp_path):
    db_file = tmp_path / "test_tickets.json"
    manager = TicketManager(filepath=str(db_file))
   
    t = manager.create_ticket("Broken Screen", "Hardware", "low", 1)
   
    # Unknown ID error
    with pytest.raises(ValueError, match="Unknown ticket ID"):
        manager.assign_ticket("T999", "Alice")

    # Empty staff name error
    with pytest.raises(ValueError, match="Staff member name must not be empty"):
        manager.assign_ticket(t.id, "   ")

    updated = manager.assign_ticket(t.id, "Alice Smiths")
    assert updated.assigned_to == "Alice Smiths"


def test_workflow_state_machine(tmp_path):
    db_file = tmp_path / "test_tickets.json"
    manager = TicketManager(filepath=str(db_file))
   
    t = manager.create_ticket("App Crash", "Software", "medium", 5)

    # Rule: Cannot move unassigned ticket into in_progress
    with pytest.raises(ValueError, match="Do not move an unassigned ticket into in_progress"):
        manager.update_status(t.id, "in_progress")

    # Assign ticket first, then move to in_progress
    manager.assign_ticket(t.id, "Bob")
    manager.update_status(t.id, "in_progress")
    assert manager.get_ticket_by_id(t.id).status == "in_progress"

    # Move to resolved
    manager.update_status(t.id, "resolved")
    assert manager.get_ticket_by_id(t.id).status == "resolved"

    # Rule: Resolved ticket cannot be modified without explicit reopen
    with pytest.raises(ValueError, match="explicit reopen"):
        manager.update_status(t.id, "in_progress")

    # Explicit reopen test
    manager.update_status(t.id, "open", reopen=True)
    assert manager.get_ticket_by_id(t.id).status == "open"


def test_work_queue_sorting(tmp_path):
    db_file = tmp_path / "test_tickets.json"
    manager = TicketManager(filepath=str(db_file))

    # Create tickets with various priorities
    t1 = manager.create_ticket("Low priority issue", "Other", "low", 2)       # low
    t2 = manager.create_ticket("Critical network issue", "Network", "high", 20) # critical
    t3 = manager.create_ticket("Medium issue", "Hardware", "medium", 5)       # medium

    queue = manager.get_work_queue()
    assert len(queue) == 3
    # Order should be critical -> medium -> low
    assert queue[0].id == t2.id
    assert queue[1].id == t3.id
    assert queue[2].id == t1.id


def test_reports_generation(tmp_path):
    db_file = tmp_path / "test_tickets.json"
    manager = TicketManager(filepath=str(db_file))

    # Zero tickets check
    rep_empty = manager.get_reports()
    assert rep_empty["total"] == 0

    manager.create_ticket("T1", "Network", "high", 15) # critical, open
    t2 = manager.create_ticket("T2", "Hardware", "low", 1)  # low, open
    manager.assign_ticket(t2.id, "Staff")
    manager.update_status(t2.id, "resolved")

    rep = manager.get_reports()
    assert rep["total"] == 2
    assert rep["status_breakdown"]["open"] == 1
    assert rep["status_breakdown"]["resolved"] == 1
    assert rep["priority_breakdown"]["critical"] == 1
    assert rep["priority_breakdown"]["low"] == 1
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
