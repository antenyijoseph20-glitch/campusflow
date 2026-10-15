"""The entry point in ``main.py``.

Thin by nature: this checks that ``main()`` wires the CLI up and runs it, and
that importing the module does not start the menu. The menu behaviour itself is
covered by tests/test_cli.py.
"""

try:  # discovery run from tests/ (the documented command)
    from base import CampusFlowTestCase
except ImportError:  # discovery run from the repository root
    from tests.base import CampusFlowTestCase

import inspect
from unittest import mock

import main as main_module


class TestMain(CampusFlowTestCase):
    def test_main_constructs_the_cli_and_runs_it(self):
        with mock.patch.object(main_module, "CLI") as fake_cli:
            main_module.main()

        fake_cli.assert_called_once_with()
        fake_cli.return_value.run.assert_called_once_with()

    def test_importing_main_does_not_start_the_menu(self):
        # main.py guards execution behind __name__ == "__main__". Without that
        # guard, importing this module during collection would start the menu
        # and block on input, so no test in the suite would ever run. Assert the
        # guard is present rather than relying on that never happening.
        source = inspect.getsource(main_module)
        self.assertIn('if __name__ == "__main__":', source)
