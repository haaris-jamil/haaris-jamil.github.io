"""Regression tests for automatic public Year 10 evidence linking."""
import unittest
from lesson_layout import class_evidence_from_files, STUDENT_EVIDENCE_RE

FOLDER = [
    "06 Teaching & Planning",
    "01 Year 10 Science - Electricity",
    "05 Student Evidence - Anonymised",
]

def pdf(fid, name, path=None, mime="application/pdf"):
    return {"id": fid, "name": name, "path": (path or FOLDER) + [name], "mimeType": mime}

class EvidenceLinkingTests(unittest.TestCase):
    def test_existing_three_automatically_match(self):
        records = [
            pdf("science1-7", "Lesson-07-Y10-Science-1-Student-Evidence-Anonymised.pdf"),
            pdf("science1-8", "Lesson-08-Y10-Science-1-Student-Evidence-2026-11-06-Anonymised.pdf"),
            pdf("science2-6", "Lesson-06-Y10-Science-2-Student-Evidence-2026-11-05-Anonymised.pdf"),
        ]
        linked = {entry["id"]: {"page": "file-" + entry["id"] + ".html"} for entry in records}
        found = class_evidence_from_files(records, linked)
        self.assertEqual({k: [f["id"] for f in v] for k, v in found.items()}, {
            (1, 7): ["science1-7"],
            (1, 8): ["science1-8"],
            (2, 6): ["science2-6"],
        })

    def test_new_lesson_needs_no_manual_mapping(self):
        e = pdf("future-upload", "Lesson-09-Y10-Science-2-Student-Evidence-2026-11-16-Anonymised.pdf")
        result = class_evidence_from_files([e], {e["id"]: {"page": "file-" + e["id"] + ".html"}})
        self.assertEqual([f["id"] for f in result[(2, 9)]], ["future-upload"])

    def test_ambiguous_and_wrong_folder_do_not_link(self):
        entries = [
            pdf("shared", "Lesson-05-Student-Evidence-Anonymised.pdf"),
            pdf("other", "Lesson-07-Y10-Science-2-Student-Evidence-Anonymised.pdf", ["Other"]),
            pdf("wrong", "Lesson-07-Y10-Science-2-Student-Evidence-Anonymised.pdf", mime="image/png"),
            pdf("unpublished", "Lesson-07-Y10-Science-2-Student-Evidence-Anonymised.pdf"),
            pdf("not-anon", "Lesson-07-Y10-Science-2-Student-Evidence.pdf"),
            pdf("invalid-lesson", "Lesson-15-Y10-Science-2-Student-Evidence-Anonymised.pdf"),
        ]
        links = {entry["id"]: {"page": f'file-{entry["id"]}.html'} for entry in entries}
        links["unpublished"] = {"page": None}
        self.assertEqual(class_evidence_from_files(entries, links), {})

    def test_multiple_distinct_samples_link_together(self):
        a = pdf("a", "Lesson-09-Y10-Science-2-Student-Evidence-Anonymised.pdf")
        b = pdf("b", "Lesson-09-Y10-Science-2-Student-Evidence-2026-11-16-Anonymised.pdf")
        found = class_evidence_from_files([a, b], {"a": {"page": "file-a.html"}, "b": {"page": "file-b.html"}})
        self.assertEqual({f["id"] for f in found[(2, 9)]}, {"a", "b"})

if __name__ == "__main__":
    unittest.main()
