import pytest

from campus_flow.manager import TicketManager


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


def test_open_ticket_cannot_be_resolved_directly(tmp_path):
    db_file = tmp_path / "test_tickets.json"
    manager = TicketManager(filepath=str(db_file))

    ticket = manager.create_ticket("Printer issue", "Hardware", "medium", 3)
    manager.assign_ticket(ticket.id, "Alice")

    with pytest.raises(ValueError, match="Invalid workflow transition"):
        manager.update_status(ticket.id, "resolved")

    assert ticket.status == "open"


def test_in_progress_ticket_cannot_return_to_open_directly(tmp_path):
    db_file = tmp_path / "test_tickets.json"
    manager = TicketManager(filepath=str(db_file))

    ticket = manager.create_ticket("Network issue", "Network", "high", 5)
    manager.assign_ticket(ticket.id, "Bob")
    manager.update_status(ticket.id, "in_progress")

    with pytest.raises(ValueError, match="Invalid workflow transition"):
        manager.update_status(ticket.id, "open")

    assert ticket.status == "in_progress"


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


def test_reopen_requires_a_resolved_ticket(tmp_path):
    db_file = tmp_path / "test_tickets.json"
    manager = TicketManager(filepath=str(db_file))

    ticket = manager.create_ticket("Software issue", "Software", "low", 2)

    with pytest.raises(ValueError, match="Only resolved tickets can be reopened"):
        manager.update_status(ticket.id, "open", reopen=True)

    assert ticket.status == "open"




def test_create_ticket_rolls_back_when_save_fails(tmp_path, monkeypatch):
    manager = TicketManager(filepath=str(tmp_path / "tickets.json"))

    def fail_save():
        raise OSError("Simulated disk failure")

    monkeypatch.setattr(manager, "save", fail_save)

    with pytest.raises(OSError, match="Simulated disk failure"):
        manager.create_ticket("Printer issue", "Hardware", "low", 1)

    assert manager.get_all_tickets() == []


def test_assignment_rolls_back_when_save_fails(tmp_path, monkeypatch):
    manager = TicketManager(filepath=str(tmp_path / "tickets.json"))
    ticket = manager.create_ticket("Printer issue", "Hardware", "low", 1)

    def fail_save():
        raise OSError("Simulated disk failure")

    monkeypatch.setattr(manager, "save", fail_save)

    with pytest.raises(OSError, match="Simulated disk failure"):
        manager.assign_ticket(ticket.id, "Alice")

    assert ticket.assigned_to is None


def test_status_rolls_back_when_save_fails(tmp_path, monkeypatch):
    manager = TicketManager(filepath=str(tmp_path / "tickets.json"))
    ticket = manager.create_ticket("Network issue", "Network", "high", 5)
    manager.assign_ticket(ticket.id, "Bob")

    def fail_save():
        raise OSError("Simulated disk failure")

    monkeypatch.setattr(manager, "save", fail_save)

    with pytest.raises(OSError, match="Simulated disk failure"):
        manager.update_status(ticket.id, "in_progress")

    assert ticket.status == "open"
