import unittest

from site_finishing import observations_body


class StudentVoiceTests(unittest.TestCase):
    def test_feedback_sources_have_distinct_anchors_and_evidence(self):
        sources = {
            "mentor": "Week 1: Mentor teacher feedback",
            "1eBxsYyTaPqJJ4byG3CSqaxWeI3w4fMfM": "Student Voice - Exit Forms (Redacted).pdf",
            "visitor": "Evaluative Visit Report",
        }
        entries = [{"id": key, "name": title, "mimeType": "application/pdf"}
                   for key, title in sources.items()]
        linked = {key: {"page": f"file-{key}.html"} for key in sources}
        markup = observations_body(entries, linked)
        for anchor in ("mentor-teacher-voice", "student-voice", "evaluative-visitor-voice"):
            self.assertEqual(markup.count(f'id="{anchor}"'), 1)
        for anchor in ("feedback-on-my-teaching", "student-voice", "weekly-mentor-feedback"):
            self.assertIn(f'href="#{anchor}"', markup)
        for key in sources:
            self.assertEqual(markup.count(f'href="file-{key}.html"'), 1)
        self.assertEqual(markup.count('role="img"'), 5)
