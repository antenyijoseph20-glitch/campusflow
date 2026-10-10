import json
import os
import tempfile
from typing import List

from campus_flow.models import Ticket


class StorageHandler:
    @staticmethod
    def load_tickets(filepath: str = "tickets.json") -> List[Ticket]:
        if not os.path.exists(filepath):
            return []

        try:
            with open(filepath, "r", encoding="utf-8") as file:
                content = file.read()
        except OSError as exc:
            raise RuntimeError(
                f"Failed to read tickets from '{filepath}': {exc}"
            ) from exc

        if not content.strip():
            return []

        try:
            data = json.loads(content)
        except json.JSONDecodeError as exc:
            raise ValueError(
                f"Malformed JSON detected in '{filepath}'. "
                "The file will not be overwritten automatically. "
                f"Error: {exc}"
            ) from exc

        if not isinstance(data, list):
            raise ValueError(
                f"Invalid storage format in '{filepath}': "
                "root must be a list of tickets."
            )

        tickets = []

        for index, item in enumerate(data):
            if not isinstance(item, dict):
                raise ValueError(
                    f"Invalid ticket entry at index {index} in "
                    f"'{filepath}': each entry must be a JSON object."
                )

            try:
                ticket = Ticket.from_dict(item)
            except (KeyError, TypeError, ValueError) as exc:
                raise ValueError(
                    f"Invalid ticket data at index {index} in "
                    f"'{filepath}': {exc}"
                ) from exc

            tickets.append(ticket)

        return tickets

    @staticmethod
    def save_tickets(
        tickets: List[Ticket],
        filepath: str = "tickets.json",
    ) -> None:
        temporary_path = None

        try:
            data = [ticket.to_dict() for ticket in tickets]

            # Use the same directory so replacement stays on the same filesystem.
            directory = os.path.dirname(os.path.abspath(filepath))
            filename = os.path.basename(filepath)

            with tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                dir=directory,
                prefix=f".{filename}.",
                suffix=".tmp",
                delete=False,
            ) as temporary_file:
                temporary_path = temporary_file.name

                json.dump(data, temporary_file, indent=4)
                temporary_file.write("\n")
                temporary_file.flush()
                os.fsync(temporary_file.fileno())

            # Replace the original only after the temporary file is complete.
            os.replace(temporary_path, filepath)
            temporary_path = None

        except Exception as exc:
            raise RuntimeError(
                f"Failed to save tickets to '{filepath}': {exc}"
            ) from exc

        finally:
            if temporary_path is not None:
                try:
                    os.remove(temporary_path)
                except FileNotFoundError:
                    pass
                except OSError:
                    pass
