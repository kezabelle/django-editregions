# -*- coding: utf-8 -*-
from django.contrib import admin
from django.contrib.admin.sites import NotRegistered
from django.contrib.auth.models import User
from django.template import Context
from django.test import TestCase
from haystack.exceptions import SearchBackendError
from editregions.contrib.search.admin import MoreLikeThisAdmin, SearchResultsAdmin
from editregions.contrib.search.models import MoreLikeThis, SearchResults
from editregions.utils.data import get_content_type, get_modeladmin


class MoreLikeThisAdminTestCase(TestCase):
    def setUp(self):
        sample_user, created = User.objects.get_or_create()
        user_ct = get_content_type(sample_user)
        mlt = MoreLikeThis(position=1, content_type=user_ct,
                           content_id=sample_user.pk, region='test',
                           connection='default')
        mlt.full_clean()
        try:
            admin.site.unregister(MoreLikeThis)
        except NotRegistered:
            pass
        admin.site.register(MoreLikeThis, MoreLikeThisAdmin)
        self.modeladmin = get_modeladmin(MoreLikeThis)
        self.obj = mlt

    def test_render_into_region(self):
        data = self.modeladmin.render_into_region(obj=self.obj,
                                                  context=Context())
        self.assertIn('no more like this', data)

    def test_render_into_region_greedy_object_loading(self):
        self.obj.request_objects = True
        data = self.modeladmin.render_into_region(obj=self.obj,
                                                  context=Context())
        self.assertIn('no more like this', data)

    def test_render_into_summary(self):
        summary = self.modeladmin.render_into_summary(obj=self.obj, context={})
        self.assertEqual('Up to 3 similar items', summary)

    def test_render_into_summary_no_maxnum(self):
        self.obj.max_num = 0
        summary = self.modeladmin.render_into_summary(obj=self.obj, context={})
        self.assertEqual(None, summary)

    def test_render_into_summary_no_maxnum(self):
        self.obj.connection = 'testing'
        summary = self.modeladmin.render_into_summary(obj=self.obj, context={})
        self.assertEqual('Up to 3 similar items from "testing"', summary)


class SearchResultsAdminTestCase(TestCase):
    def setUp(self):
        sample_user, created = User.objects.get_or_create()
        user_ct = get_content_type(sample_user)
        sr = SearchResults(position=1, content_type=user_ct,
                           content_id=sample_user.pk, region='test',
                           connection='default', query="goose fat")
        sr.full_clean()
        try:
            admin.site.unregister(SearchResults)
        except NotRegistered:
            pass
        admin.site.register(SearchResults, SearchResultsAdmin)
        self.modeladmin = get_modeladmin(SearchResults)
        self.obj = sr

    def test_render_into_region(self):
        self.obj.boost = 'a,b'
        data = self.modeladmin.render_into_region(
            obj=self.obj, context=Context({
                'chunkloop': {
                    'object': self.obj,
                }
            }))
        self.assertIn('no search results for "goose fat" via default', data)

    def test_render_into_region_no_boosts(self):
        self.obj.boost = None
        data = self.modeladmin.render_into_region(
            obj=self.obj, context=Context({
                'chunkloop': {
                    'object': self.obj,
                }
            }))
        self.assertIn('no search results for "goose fat" via default', data)

    def test_render_into_region_greedy_object_loading(self):
        self.obj.request_objects = True
        data = self.modeladmin.render_into_region(
            obj=self.obj, context=Context({
                'chunkloop': {
                    'object': self.obj,
                }
            }))
        self.assertIn('no search results for "goose fat" via default', data)

    def test_render_into_summary(self):
        summary = self.modeladmin.render_into_summary(obj=self.obj, context={})
        self.assertEqual('Up to 3 best matches for "goose fat"', summary)
