import unittest
from portfolio_sections import _goal_evidence_markup, _replace_goal_evidence, adapt_source

class EvidenceTests(unittest.TestCase):
    def test_goal_links_explain_relevance_outside_the_clickable_title(self):
        for i in (1,2,3):
            markup = _goal_evidence_markup(i)
            self.assertIn('</a>: ',markup)
            self.assertNotIn('<a href=""></a>',markup)
        self.assertIn('12 November',_goal_evidence_markup(2))
        self.assertIn('Week 8 mentor feedback',_goal_evidence_markup(3))

    def test_colleague_correspondence_anchor_preserves_the_collage(self):
        markup = '<h3>Evidence links</h3><p><a href="#colleague-correspondence">Colleague replies</a>: staff relationships.</p><h3>Colleague correspondence</h3><p><img src="collage.webp"></p>'
        result = adapt_source('1QWPX6RaidsiZVwXo9b8chnwWCXSk2V7QgOC9EhzAJt0',markup)
        self.assertIn('id="colleague-correspondence"',result)
        self.assertEqual(result.count('src="collage.webp"'),1)

    def test_future_drive_evidence_edits_are_preserved(self):
        source = '<h3>Evidence</h3><p><a href="new-evidence.html">My revised evidence</a>: Updated explanation.</p><h3>Photographic evidence</h3><p><img src="model.webp"></p>'
        result = _replace_goal_evidence(source,2)
        self.assertIn('<li><a href="new-evidence.html">My revised evidence</a>: Updated explanation.</li>',result)
        self.assertIn('src="model.webp"',result)
        self.assertNotIn('Year 13 standing-waves demonstration plan',result)

if __name__=='__main__':unittest.main()
