# -*- coding: utf-8 -*-
try:
    from unittest.case import TestCase
except ImportError:
    from django.utils.unittest.case import TestCase
from editregions.contrib.embeds.utils import static_asset_choices


class StaticAssetChoicesTestCase(TestCase):
    def test_yielding_css(self):
        data = static_asset_choices(only_patterns=('test-*.css',))
        self.assertEqual(list(data), [
            (u'test-1.css', u'test-1.css'),
            (u'test-2.css', u'test-2.css')
        ])

    def test_yielding_js(self):
        data = static_asset_choices(only_patterns=('test-*.js',))
        self.assertEqual(list(data), [
            (u'test-1.js', u'test-1.js'),
        ])

    def test_yielding_nothing(self):
        data = static_asset_choices(only_patterns=('test-*.xyz',))
        self.assertEqual(list(data), [])
