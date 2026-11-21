import unittest
from other_event_pages import publish_other_event_pages

class SessionRecordTests(unittest.TestCase):
    def test_unprepared_session_does_not_claim_advance_research(self):
        row = ['27','Recorded','14/10/2026','','Year 13 Physics',
               'One-to-one past-paper exam preparation','Individual support / part-lesson','',
               'Support the student with exam questions','',
               'Physics past paper; no written session plan or advance review of questions',
               'I worked with one student during the Year 13 Physics lesson.',
               'I did not review the questions in advance.']
        output = {}
        def document(title, caption, body, back):
            return title + caption + body
        publish_other_event_pages([row], document, output.__setitem__)
        page = output['event-27-plan.html']
        self.assertIn('Session record', page)
        self.assertIn('no written session plan or advance review', page)
        self.assertNotIn('I reviewed the NZQA', page)
        self.assertNotIn('Checking understanding', page)

if __name__ == '__main__': unittest.main()
