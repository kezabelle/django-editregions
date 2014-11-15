# -*- coding: utf-8 -*-
import django
from django.contrib import admin
from django.contrib.admin.sites import NotRegistered
from django.contrib.auth.models import User
from django.core.urlresolvers import NoReverseMatch
try:
    from unittest.case import TestCase, skipUnless
except ImportError:
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
        self.assertEqual(force_text(wrapped), 'content block')
        self.assertEqual(repr(wrapped),
                         '<editregions.admin.utils.AdminChunkWrapper '
                         'admin=admin, label="content block", exists=True, '
                         'region=test, module=editregions, content_id=1>')

    def test_urls_for_raw_chunk(self):
        wrapped = AdminChunkWrapper(opts=self.base_obj._meta, obj=self.base_obj,
                                    namespace=admin.site.name,
                                    content_id=self.base_obj.content_id,
                                    content_type=self.base_obj.content_type,
                                    region=self.base_obj.region)

        self.assertIn('/admin_mountpoint/editregions/editregionchunk/1/?',
                      wrapped.get_absolute_url())
        self.assertIn('region=test', wrapped.get_absolute_url())
        self.assertIn('content_id={0}'.format(self.base_obj.content_id),
                      wrapped.get_absolute_url())
        self.assertIn('content_type={0}'.format(self.base_obj.content_type.pk),
                      wrapped.get_absolute_url())

        self.assertIn('/admin_mountpoint/editregions/editregionchunk/1/?',
                      wrapped.get_change_url())
        self.assertIn('region=test', wrapped.get_change_url())
        self.assertIn('content_id={0}'.format(self.base_obj.content_id),
                      wrapped.get_change_url())
        self.assertIn('content_type={0}'.format(self.base_obj.content_type.pk),
                      wrapped.get_change_url())

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

        self.assertIn('/admin_mountpoint/embeds/iframe/2/delete/?',
                      wrapped.get_delete_url())
        self.assertIn('region=test', wrapped.get_delete_url())
        self.assertIn('content_id=1', wrapped.get_delete_url())
        self.assertIn('content_type={0}'.format(self.obj.content_type.pk),
                      wrapped.get_delete_url())

        self.assertIn('/admin_mountpoint/embeds/iframe/2/history/?',
                      wrapped.get_history_url())
        self.assertIn('region=test', wrapped.get_history_url())
        self.assertIn('content_id=1', wrapped.get_history_url())
        self.assertIn('content_type={0}'.format(self.obj.content_type.pk),
                      wrapped.get_history_url())

    def test_getattr_badstartswith(self):
        wrapped = AdminChunkWrapper(opts=self.obj._meta, obj=self.obj,
                                    namespace=admin.site.name,
                                    content_id=self.obj.content_id,
                                    content_type=self.obj.content_type,
                                    region=self.obj.region)
        self.assertTrue(wrapped.exists)
        with self.assertRaises(AttributeError):
            wrapped._xyz

    def test_getattr(self):
        wrapped = AdminChunkWrapper(opts=self.obj._meta, obj=self.obj,
                                    namespace=admin.site.name,
                                    content_id=self.obj.content_id,
                                    content_type=self.obj.content_type,
                                    region=self.obj.region)
        self.assertTrue(wrapped.exists)
        self.assertEqual(wrapped.position, self.obj.position)

    def test_contains(self):
        wrapped = AdminChunkWrapper(opts=self.obj._meta, obj=self.obj,
                                    namespace=admin.site.name,
                                    content_id=self.obj.content_id,
                                    content_type=self.obj.content_type,
                                    region=self.obj.region)
        self.assertIn(self.obj, wrapped)
        self.assertNotIn(self.base_obj, wrapped)

    def test_bool(self):
        wrapped = AdminChunkWrapper(opts=self.obj._meta,
                                    namespace=admin.site.name,
                                    content_id=self.obj.content_id,
                                    content_type=self.obj.content_type)
        self.assertTrue(wrapped)
        wrapped = AdminChunkWrapper(opts=self.obj._meta,
                                    namespace=admin.site.name)
        self.assertFalse(wrapped)

    def test_contextmanager(self):
        wrapped = AdminChunkWrapper(opts=self.obj._meta, obj=self.obj,
                                    namespace=admin.site.name,
                                    content_id=self.obj.content_id,
                                    content_type=self.obj.content_type,
                                    region=self.obj.region)
        with wrapped as under_test:
            self.assertEqual(wrapped.content_type, under_test.content_type)
            self.assertEqual(wrapped.opts, under_test.opts)
            self.assertEqual(wrapped.content_id, under_test.content_id)
            self.assertIn(self.obj, under_test)
            self.assertIn(self.obj, wrapped)
            under_test.exists = False
            under_test.region = 'test2'
        self.assertNotEqual(wrapped.region, 'test2')
        self.assertTrue(wrapped.exists)
        self.assertFalse(under_test.exists)
        self.assertNotEqual(wrapped.region, under_test.region)
