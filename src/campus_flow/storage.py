import json
import os
from typing import List
from campus_flow.models import Ticket


class StorageHandler:
    @staticmethod
    def load_tickets(filepath: str = "tickets.json") -> List[Ticket]:
        if not os.path.exists(filepath):
            return []
        
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if not content:
                    return []
                data = json.loads(content)
                if not isinstance(data, list):
                    raise ValueError("Storage file format invalid: root must be a list of tickets.")
                
                tickets = []
                for item in data:
                    if isinstance(item, dict):
                        tickets.append(Ticket.from_dict(item))
                return tickets
        except json.JSONDecodeError as e:
            raise ValueError(f"Malformed JSON detected in '{filepath}'. Data protection engaged: file will not be overwritten automatically. Error: {e}")
        except Exception as e:
            raise RuntimeError(f"Failed to load tickets from '{filepath}': {e}")

    @staticmethod
    def save_tickets(tickets: List[Ticket], filepath: str = "tickets.json") -> None:
        try:
            data = [t.to_dict() for t in tickets]
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4)
        except Exception as e:
            raise RuntimeError(f"Failed to save tickets to '{filepath}': {e}")