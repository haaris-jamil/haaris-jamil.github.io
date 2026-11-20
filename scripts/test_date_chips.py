import unittest
from sync_reflections import inline_elements, render_blocks

class DateChipTests(unittest.TestCase):
    def test_date_chip_is_rendered_in_table(self):
        paragraph = {"elements": [{"dateElement": {"dateElementProperties": {"displayText": "Sep 17, 2026", "timestamp": "2026-09-17T00:00:00Z"}}}, {"textRun": {"content": "\n"}}]}
        blocks = [{"table": {"tableRows": [{"tableCells": [{"content": [{"paragraph": paragraph}]}]}]}}]
        self.assertIn("<td><p>Sep 17, 2026</p></td>", render_blocks(blocks))

    def test_preserves_surrounding_text_and_escapes_chip_label(self):
        paragraph = {"elements": [{"textRun": {"content": "Observed "}}, {"dateElement": {"dateElementProperties": {"displayText": "<17 September>"}}}, {"textRun": {"content": " in class.\n"}}]}
        self.assertEqual(inline_elements(paragraph), "Observed &lt;17 September&gt; in class.")

    def test_missing_display_label_uses_stored_date_without_timezone_shift(self):
        paragraph = {"elements": [{"dateElement": {"dateElementProperties": {"timestamp": "2026-09-21T12:00:00Z"}}}]}
        self.assertEqual(inline_elements(paragraph), "2026-09-21")

if __name__ == "__main__":
    unittest.main()
