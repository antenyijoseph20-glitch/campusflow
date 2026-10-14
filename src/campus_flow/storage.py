import json
import os

class StorageManager:
    """Handles safe, atomic JSON file persistence and schema validation."""

    def __init__(self, filepath="tickets.json"):
        self.filepath = filepath

    def load_tickets(self, silent=False):
        """Loads and validates tickets from disk. Rejects corrupted data without crashing."""
        if not os.path.exists(self.filepath):
            return []
        
        try:
            with open(self.filepath, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if not content:
                    return []
                
                data = json.loads(content)
                # Edge case: JSON root must be a list
                if not isinstance(data, list):
                    if not silent:
                        print("Error: JSON root is not a list. Load rejected.")
                    return None
                
                # Edge case: Check for duplicate IDs during load
                validated_tickets = []
                seen_ids = set()
                for t in data:
                    if not isinstance(t, dict):
                        return None
                    t_id = t.get("id")
                    if not t_id or t_id in seen_ids:
                        if not silent:
                            print(f"Error: Duplicate or missing ID '{t_id}' detected. Load rejected.")
                        return None
                    seen_ids.add(t_id)
                    validated_tickets.append(t)

                return validated_tickets
        except json.JSONDecodeError as e:
            if not silent:
                print(f"Error: Malformed JSON syntax ({e}). Memory preserved.")
            return None
        except Exception as e:
            if not silent:
                print(f"Unexpected storage error: {e}")
            return None

    def save_tickets(self, tickets):
        """Atomic write: writes to a temporary file first, then replaces target to prevent corruption."""
        temp_filepath = self.filepath + ".tmp"
        try:
            with open(temp_filepath, "w", encoding="utf-8") as f:
                json.dump(tickets, f, indent=4)
            os.replace(temp_filepath, self.filepath)
            return True
        except Exception as e:
            print(f"Error saving tickets atomically: {e}")
            if os.path.exists(temp_filepath):
                try:
                    os.remove(temp_filepath)
                except:
                    pass
            return False