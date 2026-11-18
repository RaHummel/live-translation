import unittest

from translators.segmenter import TranscriptSegmenter


class TestTranscriptSegmenter(unittest.TestCase):
    def setUp(self):
        self.segmenter = TranscriptSegmenter(min_words=5, max_words=14)

    def test_sentence_end_with_min_words_is_emitted(self):
        segments = self.segmenter.update_interim('This is the first sentence. And then')
        self.assertEqual(segments, ['This is the first sentence.'])
        self.assertEqual(self.segmenter.committed_words, 5)

    def test_sentence_end_below_min_words_is_not_emitted(self):
        self.assertEqual(self.segmenter.update_interim('Yes exactly. And then'), [])

    def test_sentence_end_at_interim_boundary_emits_immediately(self):
        self.assertEqual(
            self.segmenter.update_interim('This is the first sentence.'),
            ['This is the first sentence.'],
        )

    def test_sentence_end_in_holdback_words_is_not_emitted(self):
        self.assertEqual(self.segmenter.update_interim('This is the first sentence. And'), [])
        self.assertEqual(
            self.segmenter.update_interim('This is the first sentence. And then'), ['This is the first sentence.']
        )

    def test_emits_up_to_last_sentence_end(self):
        segments = self.segmenter.update_interim('Yes exactly. That is so right! And then more')
        self.assertEqual(segments, ['Yes exactly. That is so right!'])

    def test_short_sentence_is_merged_with_following_one(self):
        self.assertEqual(self.segmenter.update_interim('Yes exactly. That is'), [])
        self.assertEqual(
            self.segmenter.update_interim('Yes exactly. That is so right. And then'),
            ['Yes exactly. That is so right.'],
        )

    def test_ordinal_numbers_are_not_sentence_ends(self):
        self.assertEqual(self.segmenter.update_interim('We will meet on 3. October in Berlin'), [])

    def test_sentence_end_with_closing_quote(self):
        segments = self.segmenter.update_interim('He said that is "good." And then')
        self.assertEqual(segments, ['He said that is "good."'])

    def test_max_words_cuts_at_last_clause_boundary(self):
        text = 'one two three four five six, seven eight nine ten eleven twelve thirteen fourteen'
        segments = self.segmenter.update_interim(text)
        self.assertEqual(segments, ['one two three four five six,'])
        self.assertEqual(self.segmenter.committed_words, 6)

    def test_max_words_without_clause_boundary_keeps_holdback(self):
        words = [f'w{i}' for i in range(14)]
        segments = self.segmenter.update_interim(' '.join(words))
        self.assertEqual(segments, [' '.join(words[:12])])

    def test_max_words_ignores_clause_boundary_below_min_words(self):
        words = ['one,'] + [f'w{i}' for i in range(13)]
        segments = self.segmenter.update_interim(' '.join(words))
        self.assertEqual(segments, [' '.join(words[:12])])

    def test_final_emits_remaining_suffix_and_resets(self):
        self.segmenter.update_interim('This is the first sentence. And then')
        self.assertEqual(
            self.segmenter.finalize('This is the first sentence. And then it ends.'), ['And then it ends.']
        )
        self.assertEqual(self.segmenter.committed_words, 0)

    def test_final_emits_short_suffix(self):
        self.assertEqual(self.segmenter.finalize('Yes.'), ['Yes.'])

    def test_final_without_new_words_emits_nothing(self):
        self.segmenter.update_interim('This is the first sentence. And then')
        self.assertEqual(self.segmenter.finalize('This is the first sentence.'), [])

    def test_revised_committed_words_are_not_respoken(self):
        self.segmenter.update_interim('This is the first sentence. And then')
        self.assertEqual(self.segmenter.update_interim('This is a first sentence. And then'), [])
        self.assertEqual(self.segmenter.finalize('Here is a first sentence. And then more.'), ['And then more.'])

    def test_shrunk_interim_does_not_emit(self):
        self.segmenter.update_interim('This is the first sentence. And then')
        self.assertEqual(self.segmenter.update_interim('This is'), [])
        self.assertEqual(self.segmenter.finalize('This is'), [])

    def test_invalid_configuration_raises(self):
        with self.assertRaises(ValueError):
            TranscriptSegmenter(min_words=0)
        with self.assertRaises(ValueError):
            TranscriptSegmenter(min_words=5, max_words=5)
