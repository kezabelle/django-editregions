# -*- coding: utf-8 -*-
from django.core.exceptions import ValidationError
from django.db.models.loading import get_model
from django.template.loader import get_template_from_string
from django.utils.unittest.case import TestCase
from editregions.utils.regions import (region_comment, region_comment_re,
                                       validate_region_name, get_pretty_region_name,
                                       sorted_regions, FakedRequestContext, get_enabled_chunks_for_region)

class RegionScanningRegexTestCase(TestCase):

    def test_found_good(self):
        """Should always find these comments in HTML."""
        regions = [
            region_comment % 'test1',
            region_comment % 'test-2',
            region_comment % 'test_3',
            region_comment % '4test',
            region_comment % '5-test',
            region_comment % '6_test',
        ]
        expected = ['test1', 'test-2', 'test_3', '4test', '5-test', '6_test']
        self.assertEqual(region_comment_re.findall(''.join(regions)), expected)

    def test_ignored_bad(self):
        """Should not find these comments in HTML."""
        regions = [
            region_comment % 'test.1',
            region_comment % 'test 2',
            region_comment % 'test^3',
            region_comment % '4.test',
            region_comment % '5 test',
            region_comment % '6^test',
            ]
        expected = []
        self.assertEqual(region_comment_re.findall(''.join(regions)), expected)

    def test_flattening_repeats(self):
        """We want a unique result set"""
        regions = [
            region_comment % 'test1',
            region_comment % 'test-2',
            region_comment % 'test1',
            region_comment % 'test-2',
            region_comment % 'test1',
            region_comment % 'test-2!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!'
        ]
        expected = ['test1', 'test-2']
        output = ''.join(regions)
        output = region_comment_re.findall(output)
        output = sorted_regions(output)
        self.assertEqual(output, expected)

class RegionNameValidationTestCase(TestCase):

    def test_really_long_region_name(self):
        """Anything over a certain length (75 as I write this) should be banned"""
        with self.assertRaises(ValidationError):
            validate_region_name('aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa'
            'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa')

    def test_really_short_region_name(self):
        """Short region names are just fine"""
        self.assertTrue(validate_region_name('a'))

    def test_bad_characters_dont_validate(self):
        """Demonstrate that most uncommon characters wont be caught"""
        with self.assertRaises(ValidationError):
            validate_region_name('a*')
        with self.assertRaises(ValidationError):
            validate_region_name('a!')
        with self.assertRaises(ValidationError):
            validate_region_name('a@')
        with self.assertRaises(ValidationError):
            validate_region_name('a£')
        with self.assertRaises(ValidationError):
            validate_region_name('a()')
        with self.assertRaises(ValidationError):
            validate_region_name('a<>')
        with self.assertRaises(ValidationError):
            validate_region_name('a|')
        with self.assertRaises(ValidationError):
            validate_region_name('a+')

    def test_unicode_not_accepted(self):
        """For simplicity's sake, the regex only matches ascii-ish things."""
        # sample from http://www.columbia.edu/~fdc/utf8/
        sample = u'An preost wes on leoden, Laȝamon was ihoten'
        with self.assertRaises(ValidationError):
            validate_region_name(sample)
        sample = u'Sîne klâwen durh die wolken sint geslagen'
        with self.assertRaises(ValidationError):
            validate_region_name(sample)
        sample = u'Τη γλώσσα μου έδωσαν ελληνική'
        with self.assertRaises(ValidationError):
            validate_region_name(sample)
        sample = u'На берегу пустынных волн'
        with self.assertRaises(ValidationError):
            validate_region_name(sample)
        sample = u'ვეპხის ტყაოსანი შოთა რუსთაველი'
        with self.assertRaises(ValidationError):
            validate_region_name(sample)


class PrettyNameTestCase(TestCase):
    def test_no_settings_fallback(self):
        """Without any named settings, fall back to a regex prettifier"""
        self.assertEqual(get_pretty_region_name('I_AM_a_test'), 'I AM a test')
        self.assertEqual(get_pretty_region_name('i-am-another-test'), 'i am another test')
        self.assertEqual(get_pretty_region_name('what else is there'), 'what else is there')
        self.assertEqual(get_pretty_region_name('perhaps.I.am.done'), 'perhaps I am done')


class SortedRegionsTestCase(TestCase):
    def test_input_remains(self):
        """Output should be consistently ordered like the input."""
        in_and_out = ['z', 'c', 'a', 1]
        self.assertEqual(sorted_regions(in_and_out), in_and_out)

    def test_output_is_like_a_set(self):
        """Because sets are unordered, we can't use them. But we want uniques!"""
        input = ['z', 'z', 'z', 'b', 'a']
        output = sorted_regions(input)
        self.assertNotEqual(len(input), len(output))
        self.assertEqual(3, len(output))
        self.assertEqual(['z', 'b', 'a'], output)


class TemplateScanningTestCase(TestCase):
    def test_emulating_scanning_files(self):
        """TODO: this is crap. fix this."""
        regions = {
            'r1': region_comment % 'I_am_found',
            'r2': region_comment % 'I_am_found_too',
        }
        input = ('<html><head>%(r1)s</head><body><!-- a comment --><div>%(r2)s'
            '</div></body></html>') % regions
        template = get_template_from_string(input)
        context = FakedRequestContext(path='/')
        result = template.render(context)
        output = region_comment_re.findall(result)
        expected = [u'I_am_found', u'I_am_found_too']
        self.assertEqual(output, expected)


class EnabledChunksTestCase(TestCase):
    def test_dotted_path_resolution(self):
        """Make sure `app.Model` turns into the actual model class"""
        FAKE_SETTINGS = {
            'test': {
                'name': 'TESTING!',
                'chunks': {
                    'auth.User': 3,
                    'auth.Group': 1,
                }
            },
        }
        resolved = get_enabled_chunks_for_region('test', FAKE_SETTINGS)
        user = get_model('auth', 'User')
        group = get_model('auth', 'Group')
        self.assertIn(user, resolved)
        self.assertIn(group, resolved)
        self.assertEqual(resolved[user], 3)
        self.assertEqual(resolved[group], 1)

    def test_failing_dotted_path_resolution(self):
        """Bad items should not be added to the resulting datastructure"""
        FAKE_SETTINGS = {
            'test': {
                'name': 'TESTING!',
                'chunks': {
                    'auth.OhGod': 3,
                    'auth.WhereAmI': 1,
                    }
            },
        }
        resolved = get_enabled_chunks_for_region('test', FAKE_SETTINGS)
        self.assertEqual([], resolved.keys())
        self.assertEqual([], resolved.values())
        self.assertEqual(0, len(resolved))

    def test_combination_dotted_path_resolution(self):
        """Both good dotted paths and bad, combined, should resolve some things"""
        FAKE_SETTINGS = {
            'test': {
                'name': 'TESTING!',
                'chunks': {
                    'auth.OhGod': 3,
                    'auth.WhereAmI': 1,
                    'auth.User': 4,
                    }
            },
        }
        resolved = get_enabled_chunks_for_region('test', FAKE_SETTINGS)
        user = get_model('auth', 'User')
        self.assertEqual([user], resolved.keys())
        self.assertEqual([4], resolved.values())
        self.assertEqual(1, len(resolved))
