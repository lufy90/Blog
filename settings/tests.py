from django.test import SimpleTestCase

from settings.comment_meaningless import is_meaningless_comment_text


class MeaninglessCommentTextTests(SimpleTestCase):
    def test_allows_normal_sentence(self):
        self.assertFalse(is_meaningless_comment_text('This is a helpful comment.'))

    def test_allows_short_unicode(self):
        self.assertFalse(is_meaningless_comment_text('谢谢'))

    def test_blocks_empty(self):
        self.assertTrue(is_meaningless_comment_text(''))
        self.assertTrue(is_meaningless_comment_text('   '))

    def test_blocks_single_punctuation(self):
        self.assertTrue(is_meaningless_comment_text('?'))

    def test_blocks_all_same_character(self):
        self.assertTrue(is_meaningless_comment_text('aaaaaaaa'))

    def test_blocks_no_letters_long_string(self):
        self.assertTrue(is_meaningless_comment_text('@@@@####$$$$'))

    def test_blocks_low_diversity_long_string(self):
        self.assertTrue(is_meaningless_comment_text('abababababababababab'))
