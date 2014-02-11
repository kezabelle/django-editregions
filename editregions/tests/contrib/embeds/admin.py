# -*- coding: utf-8 -*-
from django.contrib import admin
from django.contrib.admin.sites import NotRegistered
from django.forms import Form
from django.template import Context
from editregions.utils.data import get_modeladmin

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
        self.model = Feed
        try:
            admin.site.unregister(self.model)
        except NotRegistered:
            pass
        admin.site.register(self.model, FeedAdmin)

    def test_render_into_summary(self):
        theadmin = get_modeladmin(self.model)
        obj = self.model()
        obj.url = """<rss version="2.0">
        <channel>
        <title>Sample Feed</title>
        </channel>
        </rss>"""
        self.assertEqual(theadmin.render_into_summary(obj=obj, context={}),
                         'Sample Feed')

    def test_render_into_region(self):
        theadmin = get_modeladmin(self.model)
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
        theadmin = get_modeladmin(self.model)
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
        self.model = JavaScript
        try:
            admin.site.unregister(self.model)
        except NotRegistered:
            pass
        admin.site.register(self.model, JavaScriptAdmin)

    def test_render_into_summary(self):
        theadmin = get_modeladmin(self.model)
        obj = self.model(content='var x;')
        self.assertEqual(theadmin.render_into_summary(obj=obj, context={}),
                         'var x;')

    def test_render_into_region(self):
        theadmin = get_modeladmin(self.model)
        obj = self.model(content='var x;')
        # fake the iteration context
        context = Context({
            'chunkloop': {
                'object': obj,
            }
        })
        # nothing is output now, because we want to
        # render_into_mediagroup instead
        result = theadmin.render_into_region(obj=obj, context=context)
        self.assertIsNone(result)

    def test_media(self):
        theadmin = get_modeladmin(self.model)
        self.assertEqual(theadmin.media._css,
                         {'screen': ['editregions/css/embeds.css']})


class JavascriptAssetAdminTestCase(DjangoTestCase):
    def setUp(self):
        self.model = JavascriptAsset
        try:
            admin.site.unregister(self.model)
        except NotRegistered:
            pass
        admin.site.register(self.model, JavascriptAssetAdmin)

    def test_render_into_summary(self):
        theadmin = get_modeladmin(self.model)
        obj = self.model(local='x/y')
        self.assertEqual(theadmin.render_into_summary(obj=obj, context={}),
                         'Local file: x/y')

    def test_render_into_region(self):
        theadmin = get_modeladmin(self.model)
        obj = self.model(local='x/y')
        context = Context()
        # nothing is output now, because we want to
        # render_into_mediagroup instead
        self.assertIsNone(theadmin.render_into_region(obj=obj, context=context))

    def test_render_into_mediagroup(self):
        theadmin = get_modeladmin(self.model)
        obj = self.model(local='x/y')
        context = Context()
        self.assertIsNotNone(
            theadmin.render_into_mediagroup(obj=obj, context=context))


class StylesheetAssetAdminTestCase(JavascriptAssetAdminTestCase):
    def setUp(self):
        self.model = StylesheetAsset
        try:
            admin.site.unregister(self.model)
        except NotRegistered:
            pass
        admin.site.register(self.model, StylesheetAssetAdmin)
