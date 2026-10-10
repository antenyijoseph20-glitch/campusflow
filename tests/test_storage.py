import pytest

from campus_flow.models import Ticket
from campus_flow.storage import StorageHandler


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


def test_storage_rejects_ticket_with_missing_fields(tmp_path):
    bad_file = tmp_path / "missing_fields.json"
    bad_file.write_text('[{"id": "T001"}]', encoding="utf-8")

    with pytest.raises(ValueError, match="Invalid ticket data at index 0"):
        StorageHandler.load_tickets(str(bad_file))


def test_storage_rejects_non_object_ticket_entry(tmp_path):
    bad_file = tmp_path / "bad_entry.json"
    bad_file.write_text('[null]', encoding="utf-8")

    with pytest.raises(ValueError, match="each entry must be a JSON object"):
        StorageHandler.load_tickets(str(bad_file))


def test_storage_failed_replace_preserves_original_file(tmp_path, monkeypatch):
    test_file = tmp_path / "tickets.json"
    original_content = '[{"existing": "data"}]'
    test_file.write_text(original_content, encoding="utf-8")

    ticket = Ticket(
        id="T001",
        title="Printer issue",
        category="Hardware",
        urgency="low",
        affected_users=1,
        priority="low",
    )

    def fail_replace(source, destination):
        raise OSError("Simulated replacement failure")

    monkeypatch.setattr("campus_flow.storage.os.replace", fail_replace)

    with pytest.raises(RuntimeError, match="Failed to save tickets"):
        StorageHandler.save_tickets([ticket], str(test_file))

    assert test_file.read_text(encoding="utf-8") == original_content

    # Failed saves should not leave temporary files behind.
    assert list(tmp_path.glob(".tickets.json.*.tmp")) == []


def test_storage_rejects_non_list_json_root(tmp_path):
    bad_file = tmp_path / "bad_root.json"
    bad_file.write_text('{"ticket": "T001"}', encoding="utf-8")

    with pytest.raises(ValueError, match="root must be a list"):
        StorageHandler.load_tickets(str(bad_file))


def test_storage_malformed_json(tmp_path):
    bad_file = tmp_path / "bad_tickets.json"
    bad_file.write_text("{ this is invalid json }", encoding="utf-8")

    with pytest.raises(ValueError, match="Malformed JSON detected"):
        StorageHandler.load_tickets(str(bad_file))


def test_storage_missing_file():
    loaded = StorageHandler.load_tickets("nonexistent_tickets_file_12345.json")
    assert loaded == []

@pytest.mark.parametrize(
    "invalid_ticket",
    [
        {
            "id": "T001",
            "title": "Wi-Fi issue",
            "category": "Unknown",
            "urgency": "high",
            "affected_users": 5,
            "priority": "high",
            "status": "open",
        },
        {
            "id": "T001",
            "title": "Wi-Fi issue",
            "category": "Network",
            "urgency": "urgent",
            "affected_users": 5,
            "priority": "high",
            "status": "open",
        },
        {
            "id": "T001",
            "title": "Wi-Fi issue",
            "category": "Network",
            "urgency": "high",
            "affected_users": 5,
            "priority": "high",
            "status": "unknown",
        },
    ],
)
def test_storage_rejects_invalid_ticket_values(tmp_path, invalid_ticket):
    import json

    bad_file = tmp_path / "invalid_ticket_values.json"
    bad_file.write_text(json.dumps([invalid_ticket]), encoding="utf-8")

    with pytest.raises(ValueError, match="Invalid ticket data at index 0"):
        StorageHandler.load_tickets(str(bad_file))
