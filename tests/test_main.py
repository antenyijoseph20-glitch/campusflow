"""The entry point in ``main.py``.

Thin by nature: this checks that ``main()`` wires the CLI up and runs it. The
menu behaviour itself is covered by tests/test_cli.py.

The ``__main__`` guard in ``main.py`` is deliberately not asserted here. Reading
the source and looking for the string would check text rather than behaviour,
and the guard is already proved by this module importing during collection
without the menu starting: if it were missing, no test in the suite would run
at all. A test that cannot fail independently is not worth the line.
"""

try:  # discovery run from tests/ (the documented command)
    from base import CampusFlowTestCase
except ImportError:  # discovery run from the repository root
    from tests.base import CampusFlowTestCase

from unittest import mock

import main as main_module


class TestMain(CampusFlowTestCase):
    def test_main_constructs_the_cli_and_runs_it(self):
        with mock.patch.object(main_module, "CLI") as fake_cli:
            main_module.main()

        fake_cli.assert_called_once_with()
        fake_cli.return_value.run.assert_called_once_with()
