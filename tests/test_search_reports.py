"""Search and reporting behaviour from ``campus_flow.search_reports``.

Covers required verification cases 8-11 plus bug-hunter check B, which guards
the case normalisation that search depends on.
"""

try:  # discovery run from tests/ (the documented command)
    from base import CampusFlowTestCase
except ImportError:  # discovery run from the repository root
    from tests.base import CampusFlowTestCase

from campus_flow.search_reports import TicketReports, TicketSearch


class TestSearchReports(CampusFlowTestCase):
    # 8. Search title ignores case, matching substring
    def test_08_case_insensitive_substring_search(self):
        self.manager.create_ticket("Campus Wi-Fi Outage in Block A", "Network", "high", 20)
        self.manager.create_ticket("Printer jam in Library", "Hardware", "medium", 2)
        tickets = self.manager.list_all_tickets()

        # Lower-case query must match the mixed-case title.
        results = TicketSearch.search(tickets, query="wi-fi")
        self.assertEqual([t["id"] for t in results], ["T001"])

        # Upper-case query matches the same ticket.
        self.assertEqual(
            [t["id"] for t in TicketSearch.search(tickets, query="WI-FI")], ["T001"]
        )

        # A substring in the middle of the title also matches.
        self.assertEqual(
            [t["id"] for t in TicketSearch.search(tickets, query="outage")], ["T001"]
        )

        # A query matching nothing returns no results rather than raising.
        self.assertEqual(TicketSearch.search(tickets, query="nonexistent"), [])

    # 9. Combined search filters use AND
    def test_09_combined_search_filters_and(self):
        self.manager.create_ticket("Network switch error", "Network", "high", 15)
        self.manager.create_ticket("Network printer jam", "Hardware", "medium", 2)
        tickets = self.manager.list_all_tickets()

        # category=Network AND urgency=high -> only T001.
        results = TicketSearch.search(tickets, category="Network", urgency="high")
        self.assertEqual([t["id"] for t in results], ["T001"])

        # Adding a filter that T001 fails must empty the result set (strict AND).
        self.assertEqual(
            TicketSearch.search(tickets, category="Network", urgency="high", priority="low"),
            [],
        )

        # Category comparison is case-insensitive against the canonical value.
        # T002 is titled "Network printer jam" but its category is Hardware, so
        # only T001 matches the Network filter.
        self.assertEqual(
            [t["id"] for t in TicketSearch.search(tickets, category="network")],
            ["T001"],
        )

        # A title filter and a category filter combine with AND, not OR.
        self.assertEqual(
            TicketSearch.search(tickets, query="printer", category="Network"),
            [],
        )
        self.assertEqual(
            [t["id"] for t in TicketSearch.search(tickets, query="printer", category="Hardware")],
            ["T002"],
        )

        # An unknown filter name is reported, not silently ignored.
        with self.assertRaises(ValueError):
            TicketSearch.search(tickets, urgencyy="high")

    # 10. Empty report returns 0%, no crash
    def test_10_empty_report_safety(self):
        report = TicketReports(self.manager.list_all_tickets())

        self.assertEqual(report.total, 0)
        self.assertEqual(report.resolution_percentage(), 0.0)
        self.assertEqual(report.unresolved_count(), 0)

        # Every valid status is still reported, defaulting to zero.
        self.assertEqual(
            report.count_by_status(),
            {"open": 0, "in_progress": 0, "resolved": 0},
        )

        # generate() is safe on an empty fixture too.
        self.assertEqual(report.generate()["resolution_percentage"], 0.0)

    # 11. Report counts agree with known fixture after resolve/reopen
    def test_11_report_counts_fixture_sync(self):
        self.manager.create_ticket("T1", "Network", "high", 10)
        self.manager.create_ticket("T2", "Software", "low", 2)
        self.manager.assign_ticket("T001", "Alice")
        self.manager.update_workflow("T001", "in_progress")
        self.manager.update_workflow("T001", "resolved")

        report = TicketReports(self.manager.list_all_tickets())
        self.assertEqual(report.total, 2)
        self.assertEqual(report.count_by_status()["resolved"], 1)
        self.assertEqual(report.count_by_status()["open"], 1)
        self.assertEqual(report.resolution_percentage(), 50.0)

        # Reopening moves the ticket back and the report follows.
        self.manager.update_workflow("T001", "open")
        reopened = TicketReports(self.manager.list_all_tickets())
        self.assertEqual(reopened.count_by_status()["resolved"], 0)
        self.assertEqual(reopened.count_by_status()["open"], 2)
        self.assertEqual(reopened.resolution_percentage(), 0.0)

        # Report totals always agree with the live ticket list.
        self.assertEqual(reopened.total, len(self.manager.list_all_tickets()))

    # BUG-HUNTER B: Filter case-normalization check
    def test_bug_hunter_b_category_case_normalization(self):
        self.manager.create_ticket("Case Test", "network", "high", 10)
        ticket = self.manager.get_ticket("T001")
        # Canonical normalization stores "Network" regardless of lowercase input "network"
        self.assertEqual(ticket["category"], "Network")

        # The stored canonical value is what search must match against.
        results = TicketSearch.search(self.manager.list_all_tickets(), category="NETWORK")
        self.assertEqual([t["id"] for t in results], ["T001"])
