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

    updated = manager.assign_ticket(t.id, "Alice Smith")
    assert updated.assigned_to == "Alice Smith"


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