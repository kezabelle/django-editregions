# -*- coding: utf-8 -*-
from django.contrib import admin
from django.forms import Form
from django.template import Context
try:
    from unittest.case import TestCase
except ImportError:
    from django.utils.unittest.case import TestCase
from django.test import TestCase as DjangoTestCase, RequestFactory
from editregions.constants import REQUEST_VAR_CT, REQUEST_VAR_ID, REQUEST_VAR_REGION
from editregions.contrib.embeds.admin import IframeAdmin, JavascriptAssetAdmin, StylesheetAssetAdmin, JavaScriptAdmin, FeedAdmin
from editregions.contrib.embeds.models import Iframe, JavascriptAsset, StylesheetAsset, JavaScript, Feed


class IframeAdminTestCase(TestCase):
    def test_too_long_summary(self):
        theadmin = IframeAdmin(model=Iframe, admin_site=admin.site)
        obj = Iframe(url='http://reallylongurl.com/goes/here/and/will/be/cut/'
                         'to/keep/it/short')
        context = {}
        self.assertEqual(theadmin.render_into_summary(obj=obj, context=context),
                         'reallylongurl.com' )


class FeedAdminTestCase(DjangoTestCase):
    def setUp(self):
        self.admin = FeedAdmin
        self.model = Feed

    def test_render_into_summary(self):
        theadmin = self.admin(model=self.model, admin_site=admin.site)
        obj = self.model()
        obj.url = """<rss version="2.0">
        <channel>
        <title>Sample Feed</title>
        </channel>
        </rss>"""
        self.assertEqual(theadmin.render_into_summary(obj=obj, context={}),
                         'Sample Feed')

    def test_render_into_region(self):
        theadmin = self.admin(model=self.model, admin_site=admin.site)
        obj = self.model()
        # fake the url into a string parse.
        obj.url = """<rss version="2.0">
        <channel>
        <title>Sample Feed</title>
        </channel>
        </rss>"""
        # fake the iteration context
        context = Context({
            'chunkloop': {
                'object': obj,
            }
        })
        self.assertIn('<span>Sample Feed</span>',
                      theadmin.render_into_region(obj=obj, context=context))

    def test_save_model(self):
        theadmin = self.admin(model=self.model, admin_site=admin.site)
        obj = self.model(position=1)
        obj.url = """<rss version="2.0">
        <channel>
        <title>Sample Feed</title>
        </channel>
        </rss>"""
        request = RequestFactory().get('/', data={
            REQUEST_VAR_CT: 1,
            REQUEST_VAR_ID: 1,
            REQUEST_VAR_REGION: 'test'
        })
        theadmin.save_model(request=request, obj=obj, form=Form(),
                            change=False)


class JavascriptAdminTestCase(DjangoTestCase):
    def setUp(self):
        self.admin = JavaScriptAdmin
        self.model = JavaScript

    def test_render_into_summary(self):
        theadmin = self.admin(model=self.model, admin_site=admin.site)
        obj = self.model(content='var x;')
        self.assertEqual(theadmin.render_into_summary(obj=obj, context={}),
                         'var x;')

    def test_render_into_region(self):
        theadmin = self.admin(model=self.model, admin_site=admin.site)
        obj = self.model(content='var x;')
        # fake the iteration context
        context = Context({
            'chunkloop': {
                'object': obj,
            }
        })
        self.assertIn('var x;',
                      theadmin.render_into_region(obj=obj, context=context))

    def test_media(self):
        theadmin = self.admin(model=self.model, admin_site=admin.site)
        self.assertEqual(theadmin.media._css,
                         {'screen': ['editregions/css/embeds.css']})


class JavascriptAssetAdminTestCase(DjangoTestCase):
    def setUp(self):
        self.admin = JavascriptAssetAdmin
        self.model = JavascriptAsset

    def test_render_into_summary(self):
        theadmin = self.admin(model=self.model, admin_site=admin.site)
        obj = self.model(local='x/y')
        self.assertEqual(theadmin.render_into_summary(obj=obj, context={}),
                         'Local file: x/y')

    def test_render_into_region(self):
        theadmin = self.admin(model=self.model, admin_site=admin.site)
        obj = self.model(local='x/y')
        context = Context()
        self.assertEqual(theadmin.render_into_region(obj=obj, context=context),
                         None)

    def test_render_into_mediagroup(self):
        theadmin = self.admin(model=self.model, admin_site=admin.site)
        obj = self.model(local='x/y')
        context = Context()
        self.assertIsNotNone(
            theadmin.render_into_mediagroup(obj=obj, context=context))


class StylesheetAssetAdminTestCase(JavascriptAssetAdminTestCase):
    def setUp(self):
        self.admin = StylesheetAssetAdmin
        self.model = StylesheetAsset
