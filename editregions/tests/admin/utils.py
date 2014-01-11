# -*- coding: utf-8 -*-
import django
from django.contrib import admin
from django.contrib.admin.sites import NotRegistered
from django.contrib.auth.models import User
from django.core.urlresolvers import NoReverseMatch
from django.utils.unittest.case import TestCase, skipUnless
from django.test import TestCase as DjangoTestCase
from editregions.admin.utils import django_jqueryui_version, AdminChunkWrapper
from editregions.contrib.embeds.admin import IframeAdmin
from editregions.contrib.embeds.models import Iframe
from editregions.models import EditRegionChunk
from editregions.utils.data import get_content_type
try:
    from django.utils.encoding import force_text
except ImportError:
    from django.utils.encoding import force_unicode as force_text


class JQueryUIVersion(TestCase):

    @skipUnless(django.VERSION >= (1, 6, 0), "test only applies to Django 1.6+")
    def test_ui_is_110_plus(self):
        self.assertEqual('editregions/js/jquery.ui.1-10-3.custom.js',
                         django_jqueryui_version())

    @skipUnless(django.VERSION < (1, 6, 0), "test only applies to Django < 1.6")
    def test_ui_is_110_plus(self):
        self.assertEqual('editregions/js/jquery.ui.1-8-24.custom.js',
                         django_jqueryui_version())


class AdminChunkWrapperTestCase(DjangoTestCase):
    def setUp(self):
        user = User(username='user')
        user.set_password('user')
        user.full_clean()
        user.save()
        ct = get_content_type(user)
        obj = EditRegionChunk(position=1, region='test', content_type=ct,
                              content_id=user.pk)
        obj.full_clean()
        obj.save()

        iframe = Iframe(position=2, region='test', content_type=ct,
                        content_id=user.pk, url='https://news.bbc.co.uk/')
        iframe.full_clean()
        iframe.save()

        try:
            admin.site.unregister(Iframe)
        except NotRegistered:
            pass
        admin.site.register(Iframe, IframeAdmin)

        self.base_obj = obj
        self.obj = iframe
        self.user = user
        self.user_content_type = user

    def test_example_usage(self):
        wrapped = AdminChunkWrapper(opts=self.base_obj._meta, obj=self.base_obj,
                                    namespace=admin.site.name,
                                    content_id=self.base_obj.content_id,
                                    content_type=self.base_obj.content_type,
                                    region=self.base_obj.region)
        self.assertEqual({'app': 'editregions', 'namespace': 'admin',
                          'module': 'editregionchunk',
                          'view': '__error__'}, wrapped.url_parts)

        self.assertEqual(force_text(wrapped), 'content block: pk=1, '
                                              'region=test, position=1')
        self.assertEqual(wrapped.summary(), 'pk=1, region=test, position=1')

    def test_urls_for_raw_chunk(self):
        wrapped = AdminChunkWrapper(opts=self.base_obj._meta, obj=self.base_obj,
                                    namespace=admin.site.name,
                                    content_id=self.base_obj.content_id,
                                    content_type=self.base_obj.content_type,
                                    region=self.base_obj.region)

        abs_url = ('/admin_mountpoint/editregions/editregionchunk/1/?'
                   'region=test&content_id=1&content_type=4')
        self.assertEqual(wrapped.get_absolute_url(), abs_url)

        change_url = ('/admin_mountpoint/editregions/editregionchunk/1/?'
                      'region=test&content_id=1&content_type=4')
        self.assertEqual(wrapped.get_change_url(), change_url)
        # these just remind me that the default doesn't expose these methods
        with self.assertRaises(NoReverseMatch):
            self.assertEqual(wrapped.get_add_url(), '')
        with self.assertRaises(NoReverseMatch):
            self.assertEqual(wrapped.get_delete_url(), '')
        with self.assertRaises(NoReverseMatch):
            self.assertEqual(wrapped.get_history_url(), '')
        with self.assertRaises(NoReverseMatch):
            self.assertEqual(wrapped.get_manage_url(), '')
        with self.assertRaises(NoReverseMatch):
            self.assertEqual(wrapped.get_move_url(), '')

    def test_urls_for_mounted_chunk(self):
        wrapped = AdminChunkWrapper(opts=self.obj._meta, obj=self.obj,
                                    namespace=admin.site.name,
                                    content_id=self.obj.content_id,
                                    content_type=self.obj.content_type,
                                    region=self.obj.region)
        del_url = ('/admin_mountpoint/embeds/iframe/2/delete/?'
                   'region=test&content_id=1&content_type=4')
        self.assertEqual(wrapped.get_delete_url(), del_url)
        hist_url = ('/admin_mountpoint/embeds/iframe/2/history/?'
                    'region=test&content_id=1&content_type=4')
        self.assertEqual(wrapped.get_history_url(), hist_url)
