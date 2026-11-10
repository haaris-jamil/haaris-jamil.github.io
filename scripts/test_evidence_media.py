import unittest
from evidence_media import inline_evidence, video_card


class InlineEvidenceTests(unittest.TestCase):
    def test_photo_visible_and_caption_preserved(self):
        source = '<p><a href="file-photo.html"><u>My model</u></a></p>'
        output = inline_evidence(source, {'file-photo.html': ('image', 'assets/photo.png', '')})
        self.assertIn('<img ', output)
        self.assertIn('My model</span>', output)
        self.assertNotIn('<a ', output)

    def test_video_playable_with_poster(self):
        source = '<li><a href="file-clip.html">Model in action</a></li>'
        output = inline_evidence(source, {'file-clip.html': ('video', 'assets/clip.mp4', 'assets/poster.jpg')})
        self.assertIn('poster="assets/poster.jpg"', output)
        self.assertIn('Play video', output)
        self.assertIn('playsinline', output)
        self.assertEqual(inline_evidence(output, {'file-clip.html': ('video', 'assets/clip.mp4', 'assets/poster.jpg')}), output)

    def test_documents_and_existing_images_unchanged(self):
        source = '<a href="doc-abc.html">Plan</a><a href="file-photo.html"><img src="x"></a>'
        self.assertEqual(inline_evidence(source, {'file-photo.html': ('image','photo.png','')}), source)


if __name__ == '__main__':
    unittest.main()
