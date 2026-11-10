import html
import sys
import types
import unittest
from pathlib import Path

if 'sync_media' not in sys.modules:
    stub = types.ModuleType('sync_media')
    stub.api_json = lambda *a, **k: None
    stub.esc = html.escape
    sys.modules['sync_media'] = stub

import lesson_layout as layout


class PortfolioNumberingTests(unittest.TestCase):
    def setUp(self):
        self.events = {(g, n): {'status': 'Completed', 'date': '1 Nov 2026'}
                       for g in (1, 2) for n in range(1, 13)}
        self.events[1, 2]['status'] = 'Not delivered'

    def test_contiguous_without_changing_source_keys(self):
        self.assertEqual([layout.portfolio_number(1, n, self.events)
                          for n in range(1, 13) if n != 2], list(range(1, 12)))
        self.assertEqual([layout.portfolio_number(2, n, self.events)
                          for n in range(1, 13)], list(range(1, 13)))

    def test_table_keeps_anchors_and_hides_missed_session(self):
        table = layout.lesson_table(1, {}, self.events, {}, {}, {})
        self.assertNotIn('id="science-1-lesson-2"', table)
        self.assertIn('id="science-1-lesson-3"', table)
        self.assertIn('Lesson 02</span>', table)
        self.assertNotIn('was not delivered', table)

    def test_exact_shared_resources(self):
        self.assertEqual(layout.SLIDE_MAP[2, 8], layout.SLIDE_MAP[1, 9])
        self.assertEqual(layout.WORKSHEET_OVERRIDES[1, 9][0][0],
                         layout.WORKSHEET_OVERRIDES[2, 8][1][0])


if __name__ == '__main__':
    unittest.main()
