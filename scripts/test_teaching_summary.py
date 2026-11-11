import unittest
from teaching_summary import event_counts,render_teaching_summary

def row(i,status,kind):
    return [i,status,'','','','Teaching event',kind,'']

class TeachingSummaryTests(unittest.TestCase):
    def test_exclusive_categories_and_planned_exclusion(self):
        rows=[row('1','Recorded','Full lesson'),row('2','Recorded','Individual support / part-lesson'),
              row('3','Recorded','Teacher demonstration / part-lesson'),row('4','Recorded','Assessment and EOTC'),
              row('5','Planned','Full lesson'),row('6','Not delivered – absence','Full lesson')]
        c=event_counts(rows)
        self.assertEqual(c['completed'],4)
        self.assertEqual([c[k] for k in ('full','individual','part','other','planned')],[1,1,1,1,1])
        self.assertEqual(event_counts(rows+[rows[0]]),c)

    def test_cover_periods_are_full_lessons(self):
        c=event_counts([row('30','Recorded','Exam preparation / cover lesson'),row('31','Recorded','Exam preparation / cover session')])
        self.assertEqual(c['full'],2)
        self.assertIn('excluded from the completed total',render_teaching_summary([]))

if __name__=='__main__':
    unittest.main()
