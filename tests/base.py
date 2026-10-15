"""Shared setup for the CampusFlow test modules.

The application package lives under ``src/``, and ``unittest`` does not read the
``pythonpath`` setting in ``pyproject.toml``. Discovery with ``-s tests`` and no
``-t`` sets its top-level directory to ``tests/`` itself, so it walks that folder
as a plain directory of modules: ``tests/__init__.py`` is never imported and
cannot put ``src/`` on the path for us. Doing it here means every test module
inherits a working import, and

    python3 -m unittest discover -s tests -v

runs from a fresh clone that has not run ``pip install -e .``.

Installing the package is still the recommended setup. The insert happens ahead
of anything installed, so the suite always exercises the working tree.
"""

import os
import shutil
import sys
import tempfile
import unittest

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_SRC = os.path.join(_ROOT, "src")

# src/ goes on first so the application package resolves; the repository root
# goes on too so that main.py can be imported the way `python3 main.py` reaches
# it, since discovery inserts tests/ but neither of these.
for _path in (_ROOT, _SRC):
    if _path not in sys.path:
        sys.path.insert(0, _path)

from campus_flow.models import TicketManager  # noqa: E402


class CampusFlowTestCase(unittest.TestCase):
    """Base case giving every test an isolated data file and a fresh manager."""

    def setUp(self):
        # Each test gets an isolated directory so nothing lands in the repo root.
        self.tmpdir = tempfile.mkdtemp()
        self.test_file = os.path.join(self.tmpdir, "test_tickets.json")
        self.manager = TicketManager(filepath=self.test_file, silent_load=True)

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def reload_manager(self):
        """A second manager over the same file, as a fresh process would build."""
        return TicketManager(filepath=self.test_file, silent_load=True)

    def fresh_manager(self, name="fresh.json"):
        """A manager over its own file, for checks that must not inherit state."""
        return TicketManager(
            filepath=os.path.join(self.tmpdir, name), silent_load=True
        )
