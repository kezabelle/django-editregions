# -*- coding: utf-8 -*-
from django.utils.unittest.case import TestCase
from editregions.utils.chunks import chunk_iteration_context

class ChunkContextTestCase(TestCase):
    def setUp(self):
        class FakeChunk(object):
            placeholder = u'faked'
            def __init__(self, num):
                self.num = num

            def __unicode__(self):
                return unicode(self.num)

        self.chunk_list = [FakeChunk(x) for x in range(10)]

    def test_one_item(self):
        """For an iterable of 1 item, make sure it does the right thing. """
        i = 0
        chunk = self.chunk_list[i]
        chunks = self.chunk_list[i:i+1]
        result = chunk_iteration_context(index=i, value=chunk, iterable=chunks)['plugin']

        # Should always return the length of the original iterable
        self.assertEqual(result['total'], len(chunks))

        # 1 based counter.
        self.assertEqual(result['counter'], i+1)
        # standard, 0 style counter
        self.assertEqual(result['counter0'], i)

        # returns None if we're at the end
        self.assertEqual(result['next'], None)
        self.assertEqual(result['next0'], None)

        self.assertEqual(result['previous'], None)
        self.assertEqual(result['previous0'], None)

        self.assertEqual(result['placeholder'], u'faked')

        self.assertEqual(result['first'], True)
        self.assertEqual(result['last'], True)

        self.assertEqual(result['used_plugins'], [])
        self.assertEqual(result['remaining_plugins'], [])

        self.assertEqual(result['previous_plugin'], None)
        self.assertEqual(result['next_plugin'], None)

    def test_fake_chunk_unicode(self):
        """This mostly exists to get coverage to 100% for touching FakeChunk.__unicode__ """
        input = [u'0', u'1', u'2', u'3', u'4', u'5', u'6', u'7', u'8', u'9']
        output = []
        for i, chunk in enumerate(self.chunk_list):
            output.append(unicode(chunk))
        self.assertEqual(input, output)

    def test_counter(self):
        """Make sure the `counter` variable behaves as we expect. """
        input = range(1, 11)
        output = []
        for i, chunk in enumerate(self.chunk_list):
            result = chunk_iteration_context(index=i, value=chunk,
                iterable=self.chunk_list)['plugin']
            output.append(result['counter'])
        self.assertEqual(input, output)

    def test_counter0(self):
        """Make sure that the 0 based index counter works too """
        input = range(0, 10)
        output = []
        for i, chunk in enumerate(self.chunk_list):
            result = chunk_iteration_context(index=i, value=chunk,
                iterable=self.chunk_list)['plugin']
            output.append(result['counter0'])
        self.assertEqual(input, output)

    def test_next(self):
        """Make sure that next counter increments and handles the last iteration """
        input = [1, 2, 3, 4, 5, 6, 7, 8, 9, None]
        output = []
        for i, chunk in enumerate(self.chunk_list):
            result = chunk_iteration_context(index=i, value=chunk,
                iterable=self.chunk_list)['plugin']
            output.append(result['next'])
        self.assertEqual(input, output)

    def test_next0(self):
        """Make sure that next0 counter increments and handles the last iteration """
        input = [0, 1, 2, 3, 4, 5, 6, 7, 8, None]
        output = []
        for i, chunk in enumerate(self.chunk_list):
            result = chunk_iteration_context(index=i, value=chunk,
                iterable=self.chunk_list)['plugin']
            output.append(result['next0'])
        self.assertEqual(input, output)

    def test_next_next0(self):
        """Ensure `next0` +1 is always `next` """
        for i, chunk in enumerate(self.chunk_list):
            result = chunk_iteration_context(index=i, value=chunk,
                iterable=self.chunk_list)['plugin']
            must_pass = [
                result['next0'] is not None,
                result['next'] is not None
            ]
            if all(must_pass):
                self.assertEqual(result['next0'] + 1, result['next'])

    def test_previous(self):
        """Make sure that previous counter increments and handles the first iteration """
        input = [None, 1, 2, 3, 4, 5, 6, 7, 8, 9]
        output = []
        for i, chunk in enumerate(self.chunk_list):
            result = chunk_iteration_context(index=i, value=chunk,
                iterable=self.chunk_list)['plugin']
            output.append(result['previous'])
        self.assertEqual(input, output)

    def test_previous0(self):
        """Make sure that previous0 counter increments and handles the first iteration """
        input = [None, 0, 1, 2, 3, 4, 5, 6, 7, 8]
        output = []
        for i, chunk in enumerate(self.chunk_list):
            result = chunk_iteration_context(index=i, value=chunk,
                iterable=self.chunk_list)['plugin']
            output.append(result['previous0'])
        self.assertEqual(input, output)

    def test_previous_previous0(self):
        """Ensure `previous0` +1 is always `previous` """
        for i, chunk in enumerate(self.chunk_list):
            result = chunk_iteration_context(index=i, value=chunk,
                iterable=self.chunk_list)['plugin']
            must_pass = [
                result['previous0'] is not None,
                result['previous'] is not None
            ]
            if all(must_pass):
                self.assertEqual(result['previous0'] + 1, result['previous'])

    def test_total_never_mutates(self):
        """The total should always be constant"""
        input = [10, 10, 10, 10, 10, 10, 10, 10, 10, 10]
        output = []
        for i, chunk in enumerate(self.chunk_list):
            result = chunk_iteration_context(index=i, value=chunk,
                iterable=self.chunk_list)['plugin']
            output.append(result['total'])
        self.assertEqual(input, output)

    def test_first(self):
        """Only one element can ever be `first`"""
        input = [True, False, False, False, False, False, False, False, False, False]
        output = []
        for i, chunk in enumerate(self.chunk_list):
            result = chunk_iteration_context(index=i, value=chunk,
                iterable=self.chunk_list)['plugin']
            output.append(result['first'])
        self.assertEqual(input, output)

    def test_last(self):
        """Only one element can ever be `last`"""
        input = [False, False, False, False, False, False, False, False, False, True]
        output = []
        for i, chunk in enumerate(self.chunk_list):
            result = chunk_iteration_context(index=i, value=chunk,
                iterable=self.chunk_list)['plugin']
            output.append(result['last'])
        self.assertEqual(input, output)

    def test_revcounter(self):
        """Reverse version of `counter` """
        input = [10, 9, 8, 7, 6, 5, 4, 3, 2, 1]
        output = []
        for i, chunk in enumerate(self.chunk_list):
            result = chunk_iteration_context(index=i, value=chunk,
                iterable=self.chunk_list)['plugin']
            output.append(result['revcounter'])
        self.assertEqual(input, output)

    def test_revcounter0(self):
        """Reverse `counter`, 0 indexed"""
        input = [9, 8, 7, 6, 5, 4, 3, 2, 1, 0]
        output = []
        for i, chunk in enumerate(self.chunk_list):
            result = chunk_iteration_context(index=i, value=chunk,
                iterable=self.chunk_list)['plugin']
            output.append(result['revcounter0'])
        self.assertEqual(input, output)

    def test_remaining_plugins_count(self):
        """The remaining plugins should always be decrementing. """
        input = [9, 8, 7, 6, 5, 4, 3, 2, 1, 0]
        output = []
        for i, chunk in enumerate(self.chunk_list):
            result = chunk_iteration_context(index=i, value=chunk,
                iterable=self.chunk_list)['plugin']
            output.append(len(result['remaining_plugins']))
        self.assertEqual(input, output)

    def test_used_plugins_count(self):
        """As we iterate, the used plugin list should always be growing"""
        input = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
        output = []
        for i, chunk in enumerate(self.chunk_list):
            result = chunk_iteration_context(index=i, value=chunk,
                iterable=self.chunk_list)['plugin']
            output.append(len(result['used_plugins']))
        self.assertEqual(input, output)

    def test_next_plugin(self):
        """Make sure the `next` plugin is always accurate in the original iterable """
        input = []
        output = []
        for i, chunk in enumerate(self.chunk_list):
            result = chunk_iteration_context(index=i, value=chunk,
                iterable=self.chunk_list)['plugin']
            try:
                input.append(self.chunk_list[i+1])
            except IndexError:
                input.append(None)
            output.append(result['next_plugin'])
        self.assertEqual(input, output)

    def test_previous_plugin(self):
        """Make sure the `previous` plugin is always accurate in the original iterable """
        input = []
        output = []
        for i, chunk in enumerate(self.chunk_list):
            result = chunk_iteration_context(index=i, value=chunk,
                iterable=self.chunk_list)['plugin']
            try:
                assert i-1 >= 0
                input.append(self.chunk_list[i-1])
            except AssertionError:
                input.append(None)
            output.append(result['previous_plugin'])
        self.assertEqual(input, output)

    def test_placeholder(self):
        """Make sure the `previous` plugin is always accurate in the original iterable """
        input = [u'faked'] * 10
        output = []
        for i, chunk in enumerate(self.chunk_list):
            result = chunk_iteration_context(index=i, value=chunk,
                iterable=self.chunk_list)['plugin']
            output.append(result['placeholder'])
        self.assertEqual(input, output)
