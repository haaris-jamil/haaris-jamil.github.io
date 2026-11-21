import unittest
from other_events_table import render_other_events

class OtherEventsTests(unittest.TestCase):
    def test_separate_plans_resources_and_reflections(self):
        rows=[[rid,'Recorded','14/10/2026'] for rid in ('27','28','29')]
        markup=render_other_events(rows,{}, {})
        self.assertEqual(markup.count('scope="row"'),3)
        self.assertEqual(markup.count('scope="col"'),6)
        self.assertEqual(markup.count('>NZQA AS 91526</a>'),3)
        for rid in ('27','28','29'):
            self.assertIn(f'event-{rid}-plan.html',markup)
            self.assertIn(f'event-{rid}-reflection.html',markup)
        self.assertNotIn('learning-events.html',markup)

    def test_existing_plan_and_completed_status(self):
        markup=render_other_events([['34','Recorded','02/11/2026']],{}, {})
        self.assertIn('>Completed</span>',markup)
        self.assertIn('doc-1ofp5jgQ1npOkrbHJrQXB_HmaY6jh0zVUiR3_ksWdn-4.html',markup)

    def test_cover_and_assessment_sessions_are_visible_and_classified(self):
        rows = [[rid, 'Recorded', '23/10/2026', '', '', title, kind]
                for rid, title, kind in (
                    ('8', 'Assessment and estuary walk', 'Assessment and EOTC'),
                    ('30', 'Refraction', 'Exam preparation / cover lesson'),
                    ('31', 'Interference', 'Exam preparation / cover session'),
                    ('32', 'Astronomy', 'Exam preparation and investigation / cover lesson'))]
        markup = render_other_events(rows, {}, {})
        self.assertEqual(markup.count('scope="row"'), 4)
        self.assertEqual(markup.count('>Full lesson</span>'), 3)
        self.assertEqual(markup.count('>Other group activity</span>'), 1)
        for rid in ('8','30','31','32'):
            self.assertIn(f'learning-events.html#event-{rid}', markup)
            self.assertIn(f'event-{rid}-reflection.html', markup)
            self.assertNotIn(f'event-{rid}-plan.html', markup)

if __name__=='__main__': unittest.main()
