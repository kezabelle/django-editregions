# -*- coding: utf-8 -*-
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.test import TestCase as DjangoTestCase
from editregions.contrib.embeds.models import (Iframe, JavascriptAsset,
                                               StylesheetAsset, Feed)
from editregions.utils.data import get_content_type

try:
    from django.utils.encoding import force_text
except ImportError:
    from django.utils.encoding import force_unicode as force_text


class IframeTestCase(DjangoTestCase):
    def setUp(self):
        self.content_type = get_content_type(User)

    def test_get_name(self):
        iframe = Iframe(position=2, region='test',
                        content_type=self.content_type, content_id=1,
                        url='https://news.bbc.co.uk/',
                        name='BBC News')
        iframe.full_clean()
        iframe.save()
        self.assertEqual(iframe.get_name(), 'BBC News')

    def test_get_name_fallback(self):
        iframe = Iframe(position=2, region='test',
                        content_type=self.content_type, content_id=1,
                        url='https://news.bbc.co.uk/')
        iframe.full_clean()
        iframe.save()
        self.assertEqual(iframe.get_name(), 'chunk-iframe-1')

    def test_get_safe_name(self):
        iframe = Iframe(position=2, region='test',
                        content_type=self.content_type, content_id=1,
                        url='https://news.bbc.co.uk/',
                        name='BBC News')
        iframe.full_clean()
        iframe.save()
        self.assertEqual(iframe.get_safe_name(), 'bbc-news')

    def test_get_safe_name_fallback(self):
        iframe = Iframe(position=2, region='test',
                        content_type=self.content_type, content_id=1,
                        url='https://news.bbc.co.uk/')
        iframe.full_clean()
        iframe.save()
        self.assertEqual(iframe.get_safe_name(), 'chunk-iframe-1')

    def test_str(self):
        iframe = Iframe(position=2, region='test',
                        content_type=self.content_type, content_id=1,
                        url='https://news.bbc.co.uk/')
        iframe.full_clean()
        iframe.save()
        self.assertEqual(force_text(iframe), 'https://news.bbc.co.uk/')


class FeedTestCase(DjangoTestCase):
    def setUp(self):
        self.content_type = get_content_type(User)

    def test_str(self):
        feed = Feed(position=2, region='test',
                    content_type=self.content_type, content_id=1,
                    url='http://example.com/')
        self.assertEqual(force_text(feed), 'http://example.com/')

    def test_get_from_cache(self):
        feed = Feed(position=2, region='test',
                    content_type=self.content_type, content_id=1,
                    url='http://example.com/')
        feed.url = """<rss version="2.0">
        <channel>
        <title>Sample Feed</title>
        </channel>
        </rss>"""
        result = feed.get_from_cache()
        self.assertEqual(result, {
            'feed': {
            'title_detail': {
                'base': u'',
                'type': u'text/plain',
                'value': u'Sample Feed',
                'language': None},
            'title': u'Sample Feed'},
            'encoding': u'utf-8',
            'bozo': 0,
            'version': u'rss20',
            'namespaces': {},
            'entries': []
        })


class JavascriptAssetTestCase(DjangoTestCase):
    def setUp(self):
        self.model = JavascriptAsset
        self.content_type = get_content_type(User)

    def test_cleaning_no_data(self):
        asset = self.model(position=2, region='test',
                           content_type=self.content_type, content_id=1)
        try:
            asset.full_clean()
        except ValidationError as e:
            self.assertEqual(len(e.message_dict), 1)
            self.assertIn('__all__', e.message_dict)
            self.assertEqual(
                e.message_dict.get('__all__'),
                [u'Please provide a local file or an external URL'])

    def test_cleaning_ok_data(self):
        asset = self.model(position=2, region='test',
                           content_type=self.content_type, content_id=1,
                           local='x/y')
        asset.full_clean()

    def test_cleaning_both_data(self):
        asset = self.model(position=2, region='test',
                           content_type=self.content_type, content_id=1,
                           local='x/y', external='a/z')
        try:
            asset.full_clean()
        except ValidationError as e:
            self.assertEqual(len(e.message_dict), 1)
            self.assertIn('__all__', e.message_dict)
            self.assertEqual(
                e.message_dict.get('__all__'),
                [u'Please choose either a local file or an external URL'])

    def test_external_scheme_relative_if_possible(self):
        asset = self.model(position=2, region='test',
                           content_type=self.content_type,
                           content_id=1, external='http://a/b/c')
        scheme_relative = asset.external_scheme_relative()
        self.assertEqual(scheme_relative, '//a/b/c')

        asset2 = self.model(position=2, region='test',
                            content_type=self.content_type,
                            content_id=1, external='https://d/e/f')
        scheme_relative = asset2.external_scheme_relative()
        self.assertEqual(scheme_relative, '//d/e/f')

    def test_external_scheme_relative_not_possible(self):
        asset = self.model(position=2, region='test',
                           content_type=self.content_type,
                           content_id=1, external='ftp://a/b/c')
        scheme_relative = asset.external_scheme_relative()
        self.assertEqual(scheme_relative, 'ftp://a/b/c')

    def test_str_external(self):
        asset = self.model(position=2, region='test',
                           content_type=self.content_type,
                           content_id=1, external='ftp://a/b/c')
        asset.full_clean()
        self.assertEqual(force_text(asset), 'External URL: ftp://a/b/c')

    def test_str_local(self):
        asset = self.model(position=2, region='test',
                           content_type=self.content_type,
                           content_id=1, local='a/b/c')
        asset.full_clean()
        self.assertEqual(force_text(asset), 'Local file: a/b/c')

    def test_str_neither(self):
        asset = self.model(position=2, region='test',
                           content_type=self.content_type,
                           content_id=1)
        self.assertEqual(force_text(asset), 'None')


class StylesheetAssetTestCase(JavascriptAssetTestCase):
    def setUp(self):
        self.model = StylesheetAsset
        self.content_type = get_content_type(User)
