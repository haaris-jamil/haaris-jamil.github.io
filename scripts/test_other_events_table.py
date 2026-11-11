import unittest
from other_events_table import render_other_events

class OtherEventsTests(unittest.TestCase):
    def test_support_sessions_are_separate_completed_rows(self):
        rows = [[rid, 'Recorded', date] for rid,date in
                [('27','14/10/2026'),('28','15/10/2026'),('29','19/10/2026')]]
        markup = render_other_events(rows, {}, {})
        self.assertEqual(markup.count('scope="row"'), 3)
        self.assertEqual(markup.count('>Completed</span>'), 3)
        self.assertNotIn('<th scope="col">Evidence', markup)
        self.assertNotIn('>Plan</a>', markup)
        self.assertIn('learning-events.html#event-27', markup)
        self.assertEqual(markup.count('>NZQA AS 91526 resources</a>'), 2)

    def test_status_and_source_plan_are_preserved(self):
        markup = render_other_events([['34','Planned','02/11/2026']], {}, {})
        self.assertIn('>Planned</span>', markup)
        self.assertIn('>Planning record</a>', markup)
        self.assertIn('doc-1ofp5jgQ1npOkrbHJrQXB_HmaY6jh0zVUiR3_ksWdn-4.html', markup)

if __name__ == '__main__':
    unittest.main()
